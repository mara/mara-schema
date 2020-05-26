import pytest


@pytest.fixture
def mock_data_sets():
    """Set up the mara_schema.config.data_sets."""
    from mara_schema.config import data_sets

    return data_sets()
