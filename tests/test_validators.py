from getopt import error
import errors as err

from validators import validate_fields

def test_validate_fields():
    fields = [
        {"id": "f1", "label": "Имя", "type": "text"},
        {"id": "f2", "label": "Возраст", "type": "number"},
        {"id": "f3", "label": "ОВЗ", "type": "boolean"}
    ]
    ok, error = validate_fields(fields)
    assert error is None
    assert ok is True

def test_empty_label():
    fields = [
        {"id": "f1", "label": "", "type": "text"},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.MISSING_LABEL


def test_empty_fields():
    fields = [
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.EMPTY_FIELDS

def test_fields_is_string():
    fields = "hello world"
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.EMPTY_FIELDS

def test_fields_no_label():
    fields = [{"id": "f1", "type": "text"}]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.MISSING_LABEL

def test_empty_type():
    fields = [
        {"id": "f1", "label": "empty_type", "type": ""},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.WRONG_TYPE

def test_fields_no_type():
    fields = [
        {"id": "f1", "label": "no_type"},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.MISSING_TYPE

def test_fields_wrong_type():
    fields = [
        {"id": "f1", "label": "wrong_type", "type": "wrong_type"},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == err.ErrorMessages.WRONG_TYPE