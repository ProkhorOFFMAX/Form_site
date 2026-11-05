import errors as err

# Валидатор полей для заявки
def validate_fields(fields):
    if not isinstance(fields, list) or len(fields) == 0:
        return False, err.ErrorMessages.EMPTY_FIELDS

    for f in fields:
        if not isinstance(f, dict):
            return False, err.ErrorMessages.WRONG_FIELD

        if f.get("type") == "custom_select":
            if "field_id" not in f:
                return False, err.ErrorMessages.WRONG_CUSTOM_FIELD
            if not isinstance(f["field_id"], int):
                return False, err.ErrorMessages.WRONG_CUSTOM_FIELD_TYPE
            if "label" not in f or not f["label"].strip():
                return False, "У поля custom_select должен быть label"
            continue

        # Обычные поля: label и type обязательны
        if 'label' not in f or not f['label'].strip():
            return False, err.ErrorMessages.MISSING_LABEL
        if 'type' not in f:
            return False, err.ErrorMessages.MISSING_TYPE
        if f['type'] not in ("text", "number", "boolean", "institution"):
            return False, err.ErrorMessages.WRONG_TYPE
    return True, None