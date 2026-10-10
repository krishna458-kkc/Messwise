"""AppTest automated verification across all 9 MessWise Streamlit pages."""

from pathlib import Path
from streamlit.testing.v1 import AppTest

BASE_DIR = Path(__file__).resolve().parent.parent


def test_page_home_runs_cleanly():
    at = AppTest.from_file(BASE_DIR / "app" / "Home.py")
    at.run(timeout=15)
    assert not at.exception, f"Home page crashed: {at.exception}"


def test_page_kitchen_runs_cleanly():
    at = AppTest.from_file(BASE_DIR / "app" / "pages" / "Kitchen.py")
    at.run(timeout=15)
    assert not at.exception, f"Kitchen page crashed: {at.exception}"


def test_page_planner_runs_cleanly():
    at = AppTest.from_file(BASE_DIR / "app" / "pages" / "Planner.py")
    at.run(timeout=15)
    assert not at.exception, f"Planner page crashed: {at.exception}"


def test_page_forecast_lab_runs_cleanly():
    at = AppTest.from_file(BASE_DIR / "app" / "pages" / "Forecast_Lab.py")
    at.run(timeout=15)
    assert not at.exception, f"Forecast Lab page crashed: {at.exception}"


def test_page_waste_intelligence_runs_cleanly():
    at = AppTest.from_file(BASE_DIR / "app" / "pages" / "Waste_Intelligence.py")
    at.run(timeout=15)
    assert not at.exception, f"Waste Intelligence page crashed: {at.exception}"


def test_page_reports_runs_cleanly():
    at = AppTest.from_file(BASE_DIR / "app" / "pages" / "Reports.py")
    at.run(timeout=15)
    assert not at.exception, f"Reports page crashed: {at.exception}"


def test_page_simulator_runs_cleanly():
    at = AppTest.from_file(BASE_DIR / "app" / "pages" / "Simulator.py")
    at.run(timeout=15)
    assert not at.exception, f"Simulator page crashed: {at.exception}"


def test_page_surplus_routing_runs_cleanly():
    at = AppTest.from_file(BASE_DIR / "app" / "pages" / "Surplus_Routing.py")
    at.run(timeout=15)
    assert not at.exception, f"Surplus Routing page crashed: {at.exception}"


def test_page_impact_runs_cleanly():
    at = AppTest.from_file(BASE_DIR / "app" / "pages" / "Impact.py")
    at.run(timeout=15)
    assert not at.exception, f"Impact page crashed: {at.exception}"
