import sys
from pathlib import Path
import pytest

Root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Root))

@pytest.fixture(scope="session", autouse=True)
def add_web_app_to_path():
    web_app_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(web_app_dir))
    yield
    if str(web_app_dir) in sys.path:
        sys.path.remove(str(web_app_dir))