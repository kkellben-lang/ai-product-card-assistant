import pytest
from app.validation import InputValidationError, build_characteristics, collect_missing_fields, validate_product_input

def test_non_object_input_is_rejected():
    with pytest.raises(InputValidationError): validate_product_input([])
def test_empty_product_is_rejected():
    with pytest.raises(InputValidationError): validate_product_input({})
def test_missing_fields_are_reported():
    p=validate_product_input({"name":"Прибор","manufacturer":"","specs":{"питание":""},"description":""})
    m=collect_missing_fields(p)
    assert any("manufacturer" in x for x in m) and any("description" in x for x in m) and any("питание" in x for x in m)
def test_characteristics_are_copied():
    p=validate_product_input({"name":"Прибор","manufacturer":"Производитель","specs":{"диапазон":"0–1,6 МПа","питание":""},"description":"Описание"})
    assert build_characteristics(p)==[{"name":"диапазон","value":"0–1,6 МПа"},{"name":"питание","value":"данных нет"}]
