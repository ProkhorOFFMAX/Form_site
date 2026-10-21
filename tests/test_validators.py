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
