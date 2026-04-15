from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_csv_path() -> Path:
    return FIXTURES / "cfd_sample.csv"


@pytest.fixture
def fresh_duckdb(tmp_path: Path) -> Path:
    return tmp_path / "test.duckdb"


@pytest.fixture
def mock_lccc_response(sample_csv_path: Path) -> bytes:
    return sample_csv_path.read_bytes()
