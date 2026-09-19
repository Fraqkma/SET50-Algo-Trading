from scripts.run_observability_diagnostic_replay import load_frames


def test_observability_loader_uses_approved_path():
    frames, _ = load_frames()
    assert frames
