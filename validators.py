import errors as err

ALLOWED_PART_TYPES = ("text", "number", "boolean", "institution", "custom_select", "reference_text")

# Валидатор полей для заявки
def validate_fields(fields):
    if not isinstance(fields, list) or len(fields) == 0:
        return False, err.ErrorMessages.EMPTY_FIELDS

    for f in fields:
        if not isinstance(f, dict):
            return False, err.ErrorMessages.WRONG_FIELD

        if f.get("type") == "composite": #Состовное поле
            if "parts" not in f or not isinstance(f["parts"], list) or len(f["parts"]) == 0:
                return False, "У composite-поля должны быть части (parts)"
            for part in f["parts"]:
                if "name" not in part or "label" not in part or "type" not in part:
                    return False, "У каждой части composite-поля должны быть name, label, type"
                if part["type"] not in ALLOWED_PART_TYPES:
                    return False, f"Недопустимый тип части: {part['type']}"
                # Дополнительные проверки для конкретных типов
                if part["type"] == "custom_select" and "field_id" not in part:
                    return False, "У части custom_select должен быть field_id"
                if part["type"] == "reference_text" and "dict_id" not in part:
                    return False, "У части reference_text должен быть dict_id"
            continue

        if f.get("type") == "reference_text":
            if "dict_id" not in f:
                return False, err.ErrorMessages.WRONG_CUSTOM_FIELD
            if not isinstance(f["dict_id"], int):
                return False, err.ErrorMessages.WRONG_CUSTOM_FIELD_TYPE
            if "label" not in f or not f["label"].strip():
                return False, "У поля reference_text должен быть label"
            continue

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