import pytest
from pydantic import ValidationError
from project5.api_db import PredictionInput

def test_valid_input():
    data = PredictionInput(feature1=0, feature2=1)
    assert data.feature1 == 0

def test_invalid_input_type():
    with pytest.raises(ValidationError):
        PredictionInput(feature1="abc", feature2=1)
