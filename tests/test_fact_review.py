import pytest

from app.validation import OutputValidationError, validate_fact_review


def test_valid_fact_review():
    review = validate_fact_review({
        "is_grounded": False,
        "unsupported_claims": [
            {
                "claim": "для промышленных систем",
                "reason": "этого нет во входных данных",
            }
        ],
    })
    assert review["is_grounded"] is False


def test_invalid_fact_review_rejected():
    with pytest.raises(OutputValidationError):
        validate_fact_review({"is_grounded": "yes", "unsupported_claims": []})
