from getopt import error

from validators import validate_fields

def test_validate_fields():
    fields = [
        {"id": "f1", "label": "Имя", "type": "text"},
        {"id": "f2", "label": "Возраст", "type": "number"}
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
    assert error == "У каждого поля должен быть label"


def test_empty_fields():
    fields = [
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == "Должен быть не пустой массив полей"

def test_fields_is_string():
    fields = "hello world"
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == "Должен быть не пустой массив полей"

def test_fields_no_label():
    fields = [{"id": "f1", "type": "text"}]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == "У каждого поля должен быть label"

def test_empty_type():
    fields = [
        {"id": "f1", "label": "empty_type", "type": ""},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == "Тип поля должен быть text или number"

def test_fields_no_type():
    fields = [
        {"id": "f1", "label": "no_type"},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == "У каждого поля должен быть type"

def test_fields_wrong_type():
    fields = [
        {"id": "f1", "label": "wrong_type", "type": "wrong_type"},
    ]
    ok, error = validate_fields(fields)
    assert ok is False
    assert error == "Тип поля должен быть text или number"