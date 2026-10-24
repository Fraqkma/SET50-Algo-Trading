from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_settrade_destinations_are_direct_navigation_pages() -> None:
    app = Path(__file__).parents[1] / "ui" / "app.py"
    tested = AppTest.from_file(str(app), default_timeout=30).run()
    assert not tested.exception
    workspaces = [widget for widget in tested.selectbox if widget.label == "Workspace"]
    assert workspaces
    assert "Candle Explorer" in workspaces[0].options
    assert "Order Book Explorer" in workspaces[0].options
    workspaces[0].select("Candle Explorer").run()
    assert not tested.exception
    workspaces = [widget for widget in tested.selectbox if widget.label == "Workspace"]
    workspaces[0].select("Order Book Explorer").run()
    assert not tested.exception
    for destination in ("Gap Inspector", "Production API Status", "TradeSim Results"):
        current = [widget for widget in tested.selectbox if widget.label == "Workspace"][0]
        assert destination in current.options
        current.select(destination).run()
        assert not tested.exception
