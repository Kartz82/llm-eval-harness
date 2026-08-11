// k6 performance smoke test + SLO gate for a live agent API.
//   k6 run -e BASE_URL=http://localhost:8000 perf/k6_smoke.js
//
// Fails (non-zero exit) if the p95 latency or error-rate SLOs are breached — a
// perf release gate to sit alongside the correctness eval.
import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const options = {
  vus: 5,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<3000"], // 95% of requests under 3s
    http_req_failed: ["rate<0.02"],    // <2% errors
  },
};

export default function () {
  const res = http.post(
    `${BASE_URL}/chat`,
    JSON.stringify({ message: "How long do refunds take?" }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(res, { "status is 2xx/4xx (not 5xx)": (r) => r.status < 500 });
  sleep(1);
}
