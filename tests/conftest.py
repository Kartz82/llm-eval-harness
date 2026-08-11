import os
from pathlib import Path

import pytest

os.environ.setdefault("EVAL_TARGET", "mock")
os.environ.setdefault("PASS_THRESHOLD", "1.0")

_DATASET = str(Path(__file__).resolve().parent.parent / "datasets" / "support_agent.yaml")


@pytest.fixture
def dataset() -> str:
    return _DATASET
