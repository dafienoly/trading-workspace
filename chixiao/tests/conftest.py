import pytest
from pathlib import Path


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def sample_csv_path(project_root) -> Path:
    return project_root / "data" / "positions_sample.csv"
