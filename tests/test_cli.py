"""CLI gate tests."""
from evalkit.run import main


def test_cli_gate_passes_on_mock(dataset, tmp_path):
    report = tmp_path / "report.md"
    rc = main(["--dataset", dataset, "--target", "mock", "--report", str(report)])
    assert rc == 0
    assert report.exists()


def test_cli_gate_fails_on_impossible_threshold(dataset):
    # threshold above 1.0 can never be met → non-zero exit (gate blocks release).
    rc = main(["--dataset", dataset, "--target", "mock", "--threshold", "1.01"])
    assert rc == 1
