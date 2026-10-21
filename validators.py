def validate_fields(fields):
    if not isinstance(fields, list) or len(fields) == 0:
        return False, "Должен быть не пустой массив полей"

    for f in fields:
        if not isinstance(f, dict):
            return False, "Каждое поле должно быть объектом"
        if 'label' not in f or not f['label'].strip():
            return False, "У каждого поля должен быть label"
        if 'type' not in f:
            return False, "У каждого поля должен быть type"
        if f['type'] not in ("text", "number"):
            return False, "Тип поля должен быть text или number"
    return True, None