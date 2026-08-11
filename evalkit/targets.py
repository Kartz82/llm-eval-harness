"""Targets under test. All expose ``run(case) -> Response`` so the runner is
agnostic to whether it is evaluating a canned mock, a live agent API, or Gemini.
"""
from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .cases import Case
from .config import settings

_ORDER_RE = re.compile(r"\b([A-Za-z]\d{3,})\b")


@dataclass
class Response:
    text: str
    tool_calls: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    raw: dict = field(default_factory=dict)


class Target(ABC):
    name: str = "target"

    @abstractmethod
    def run(self, case: Case) -> Response: ...


class MockTarget(Target):
    """Deterministic stand-in for a tool-using support agent.

    ``mode='broken'`` simulates a regressed agent (drops tools/grounding) so tests
    can prove the harness and the release gate actually catch failures.
    """

    name = "mock"

    def __init__(self, mode: str = "good") -> None:
        self.mode = mode

    def run(self, case: Case) -> Response:
        start = time.perf_counter()
        resp = self._respond(case)
        resp.latency_ms = (time.perf_counter() - start) * 1000
        return resp

    def _respond(self, case: Case) -> Response:
        if self.mode == "broken":
            return Response(text="I'm not sure, sorry.")
        text = case.input.lower()
        order = _ORDER_RE.search(case.input)

        if "refund" in text and order:
            if "refund:write" in case.scopes:
                return Response(
                    text=f"Refund approved for order {order.group(1).upper()}.",
                    tool_calls=["request_refund"],
                )
            return Response(
                text="Refund denied: missing required scope 'refund:write'.",
                tool_calls=["request_refund"],
            )
        if any(w in text for w in ("refund", "shipping", "return", "policy", "how long")):
            return Response(
                text="Refunds are returned to the original method within 5 to 7 business days.",
                tool_calls=["search_kb"],
                citations=["refund_policy.md"],
            )
        if order:
            return Response(
                text=f"Order {order.group(1).upper()}: in_transit (ETA 2 days).",
                tool_calls=["get_order_status"],
            )
        return Response(text=f"[mock] {case.input}")


class HttpAgentTarget(Target):
    """Evaluate a live agent exposing POST /token and POST /chat (the Support Agent)."""

    name = "http"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.agent_base_url).rstrip("/")

    def _token(self, client, scopes: list[str]) -> str | None:
        # Agent user carries refund:write; customer does not.
        user = "agent" if "refund:write" in scopes else "customer"
        r = client.post(f"{self.base_url}/token", data={"username": user, "password": user})
        return r.json().get("access_token") if r.status_code == 200 else None

    def run(self, case: Case) -> Response:
        import httpx

        start = time.perf_counter()
        with httpx.Client(timeout=30) as client:
            headers = {}
            token = self._token(client, case.scopes)
            if token:
                headers["Authorization"] = f"Bearer {token}"
            r = client.post(
                f"{self.base_url}/chat", json={"message": case.input}, headers=headers
            )
            r.raise_for_status()
            data = r.json()
        return Response(
            text=data.get("reply", ""),
            tool_calls=[t["name"] for t in data.get("tool_calls", [])],
            citations=[c["source"] for c in data.get("citations", [])],
            latency_ms=(time.perf_counter() - start) * 1000,
            raw=data,
        )


class GeminiTarget(Target):
    """Direct Gemini text target (no tools) — for pure generation evals."""

    name = "gemini"

    def run(self, case: Case) -> Response:
        from langchain_google_genai import ChatGoogleGenerativeAI

        start = time.perf_counter()
        llm = ChatGoogleGenerativeAI(
            model=settings.model_name, google_api_key=settings.google_api_key
        )
        content = llm.invoke(case.input).content
        # Newer Gemini models return a list of typed blocks; flatten to plain text.
        if isinstance(content, list):
            content = "".join(
                b.get("text", "") if isinstance(b, dict) else str(b) for b in content
            ).strip()
        return Response(text=str(content), latency_ms=(time.perf_counter() - start) * 1000)


def build_target(kind: str | None = None) -> Target:
    kind = kind or settings.eval_target
    if kind == "http":
        return HttpAgentTarget()
    if kind == "gemini":
        return GeminiTarget()
    return MockTarget()
