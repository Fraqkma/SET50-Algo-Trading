from pathlib import Path


def test_phase_documents_are_conservative():
    root = Path(__file__).resolve().parents[1]
    text = (root / "docs/NEXT_DESIGN_PROPOSALS.md").read_text(encoding="utf-8")
    assert "approval" in text.lower()
    assert "not been implemented" in text
