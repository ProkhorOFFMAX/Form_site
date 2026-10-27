from getopt import error
import errors as err
import pytest

from validators import validate_fields

@pytest.mark.unit
def test_validate_fields():
    fields = [
        {"id": "f1", "label": "Имя", "type": "text"},
        {"id": "f2", "label": "Возраст", "type": "number"},
        {"id": "f3", "label": "ОВЗ", "type": "boolean"},
        {"id": "f4", "label": "ОУ", "type": "institution"},
    ]
    ok, error = validate_fields(fields)
    assert error is None
    assert ok is True

@pytest.mark.unit
def test_empty_label():
    fields = [
        {"id": "f1", "label": "", "type": "text"},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.MISSING_LABEL

@pytest.mark.unit
def test_empty_fields():
    fields = [
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.EMPTY_FIELDS

@pytest.mark.unit
def test_fields_is_string():
    fields = "hello world"
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.EMPTY_FIELDS

@pytest.mark.unit
def test_fields_no_label():
    fields = [{"id": "f1", "type": "text"}]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.MISSING_LABEL

@pytest.mark.unit
def test_empty_type():
    fields = [
        {"id": "f1", "label": "empty_type", "type": ""},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.WRONG_TYPE

@pytest.mark.unit
def test_fields_no_type():
    fields = [
        {"id": "f1", "label": "no_type"},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.MISSING_TYPE

@pytest.mark.unit
def test_fields_wrong_type():
    fields = [
        {"id": "f1", "label": "wrong_type", "type": "wrong_type"},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.WRONG_TYPE