from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_market_research_pages_render_and_controls_switch() -> None:
    app = Path(__file__).parents[1] / "ui" / "app.py"
    tested = AppTest.from_file(str(app), default_timeout=30).run()
    assert not tested.exception
    workspace = next(widget for widget in tested.selectbox if widget.label == "Workspace")
    assert workspace.value == "Overview"
    workspace.select("Market Overview").run()
    assert not tested.exception
    assert any("Current SET50 display universe only" in item.value for item in tested.warning)
    assert any("source rows violate OHLC range checks" in item.value for item in tested.warning)
    tested.segmented_control(key="overview_group").set_value("Stocks 26–50").run()
    assert not tested.exception
    assert any("Stocks 26–50" in item.value for item in tested.subheader)
    tested.segmented_control(key="overview_mode").set_value("Cumulative return").run()
    assert not tested.exception
    tested.segmented_control(key="overview_mode").set_value("Relative performance").run()
    assert not tested.exception
    tested.segmented_control(key="overview_mode").set_value("Raw close").run()
    assert not tested.exception

    workspace = next(widget for widget in tested.selectbox if widget.label == "Workspace")
    workspace.select("Multi-Stock Trends").run()
    assert not tested.exception
    tested.selectbox(key="trends_range").select("Max available").run()
    assert not tested.exception

    workspace = next(widget for widget in tested.selectbox if widget.label == "Workspace")
    workspace.select("Correlation Lab").run()
    assert not tested.exception
    tested.selectbox(key="corr_window").select(20).run()
    assert not tested.exception
    tested.segmented_control(key="corr_order").set_value("Correlation clustered").run()
    assert not tested.exception

    for page in ("Market Breadth", "Stock Detail", "Historical Data Explorer"):
        workspace = next(widget for widget in tested.selectbox if widget.label == "Workspace")
        workspace.select(page).run()
        assert not tested.exception, page

    workspace = next(widget for widget in tested.selectbox if widget.label == "Workspace")
    workspace.select("Market Overview").run()
    tested.selectbox(key="overview_detail_symbol").select("AOT").run()
    tested.button(key="open_stock_detail").click().run()
    assert not tested.exception
    assert tested.selectbox(key="detail_symbol").value == "AOT"
