from streamlit.testing.v1 import AppTest


def test_app_loads_without_exceptions():
    at = AppTest.from_file("../app.py")
    at.run()
    assert not at.exception
