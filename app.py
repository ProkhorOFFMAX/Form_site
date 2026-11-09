from dataclasses import fields
from getopt import error
from os.path import exists

from dotenv import load_dotenv
from sqlalchemy.engine import row

load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, jsonify
from db import query_db, get_connection
from validators import validate_fields
import json
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/')
def index():
    templates = query_db("SELECT id, name, created_at FROM templates ORDER BY id")
    return render_template("index.html", templates=templates)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form.get('name', "").strip()
        fields_json = request.form.get('fields_json', "").strip()

        if not name:
            return render_template("create.html", error="Название обязательно")
        try:
            fields = json.loads(fields_json)
            ok, error = validate_fields(fields)
            if not ok:
                return render_template("create.html", error=error)
        except (json.JSONDecodeError, ValueError) as e:
            return render_template("create.html", error=f"Ошибка в полях: {e}")

        query_db(
            "INSERT INTO templates (name, fields) VALUES (%s, %s)",
            (name, json.dumps(fields)),
            fetch=False
        )

        return redirect(url_for("index"))
    return render_template("create.html")

@app.route('/fill/<int:template_id>', methods=['GET', 'POST'])
def fill(template_id):
    templates = query_db("SELECT id, name, fields FROM templates WHERE id = %s", (template_id,))
    if not templates:
        return "Шаблон не найден", 404

    template = templates[0]
    fields = template["fields"]

    if request.method == 'POST':
        data = {}
        for field in fields:
            value = request.form.get(field["id"], "").strip()

            if field["type"] == "boolean":
                raw = request.form.get(field["id"], "")
                if raw == "":
                    return render_template("fill.html", template=template, fields=fields,
                                               error=f"Поле «{field['label']}» обязательно")
                value = (raw == "true")
            elif field["type"] == "number":
                if value == "":
                    return render_template("fill.html", template=template,
                                           fields=fields, error=f"Поле «{field['label']}» должно быть числом")
                else:
                    if value == "":
                        return render_template("fill.html", template=template, fields=fields,
                                               error=f"Поле «{field['label']}» обязательно")
            elif field["type"] == "institution":
                raw = request.form.get(field["id"], "")
                if raw == "":
                    return render_template("fill.html", template=template, fields=fields,
                                           error=f"Поле «{field['label']}» обязательно")
                # Проверяем, что ID существует
                exists = query_db(
                    "SELECT id FROM educational_institutions WHERE id = %s",
                    (int(raw),)
                )
                if not exists:
                    return render_template("fill.html", template=template, fields=fields, error=f"Выбранное ОУ не найдено")
                value = int(raw)
            elif field["type"] == "custom_select":
                value = request.form.get(field["id"], "").strip()
                if field.get("required", True) and value == "":
                    return render_template("fill.html", template=template, fields=fields,
                                           error=f"Поле «{field['label']}» обязательно")
                # Если значение выбрано, проверяем, что оно существует и принадлежит этому справочнику
                if value != "":
                    exists = query_db(
                        "SELECT id FROM field_options WHERE id = %s AND field_id = %s",
                        (int(value), field["field_id"])
                    )
                    if not exists:
                        return render_template("fill.html", template=template, fields=fields,
                                               error=f"Недопустимое значение для поля «{field['label']}»")
                    data[field["id"]] = int(value)
            else:
                data[field["id"]] = value

            # Сохраняем
        query_db(
        "INSERT INTO responses (template_id, data) VALUES (%s, %s)",
        (template_id, json.dumps(data)),
        fetch=False
        )

        return redirect(url_for("responses", template_id=template_id))

    return render_template("fill.html", template=template, fields=fields)

@app.route("/responses/<int:template_id>")
def responses(template_id):
    templates = query_db("SELECT id, name, fields FROM templates WHERE id = %s", (template_id,))
    if not templates:
        return "Шаблон не найден", 404

    template = templates[0]
    fields = template["fields"]

    rows = query_db(
        "SELECT id, data, submitted_at FROM responses WHERE template_id = %s ORDER BY submitted_at DESC",
        (template_id,)
    )

    all_inst_ids = set()
    for row in rows:
        for field in fields:
            if field["type"] == "institution":
                inst_id = row["data"].get(field["id"])
                if inst_id:
                    all_inst_ids.add(inst_id)

    inst_names = {}
    if all_inst_ids:
        placeholders = ",".join(["%s"] * len(all_inst_ids))
        inst_rows = query_db(
            f"SELECT id, short_name FROM educational_institutions WHERE id IN ({placeholders})",
            tuple(all_inst_ids)
        )
        inst_names = {r["id"]: r["short_name"] for r in inst_rows}


    # Собираем все ID вариантов из ответов
    all_option_ids = set()
    for row in rows:
        for field in fields:
            if field.get("type") == "custom_select":
                opt_id = row["data"].get(field["id"])
                if opt_id:
                    all_option_ids.add(opt_id)

    option_labels = {}
    if all_option_ids:
        placeholders = ",".join(["%s"] * len(all_option_ids))
        opt_rows = query_db(
            f"SELECT id, label FROM field_options WHERE id IN ({placeholders})",
            tuple(all_option_ids)
        )
        option_labels = {r["id"]: r["label"] for r in opt_rows}

    return render_template("responses.html", template=template, fields=fields, responses=rows,
                           inst_names=inst_names, option_labels=option_labels )

@app.route("/api/institutions/<string:inst_type>")
def get_institutions(inst_type):
    """
    Получить список образовательных учреждений по типу
    Это описание появится в Swagger UI
    ---
    parameters:
     - name: inst_type
       in: path
       type: string
       enum: ['ГБОУ', 'ГБДОУ', 'ОДОД']
       required: true
       description: Тип учреждения
    responses:
     200:
      description: Успешный ответ со списком ОУ
      schema:
       type: array
       items:
        type: object
        properties:
         id:
          type: integer
         full_name:
          type: string
         short_name:
          type: string
     400:
      description: Неверный тип учреждения
    """
    if inst_type not in ('ГБОУ', "ГБДОУ", "ОДОД"):
        return jsonify({"error": "Неверный тип"}), 400

    rows = query_db(
        "SELECT id, full_name, short_name FROM educational_institutions "
        "WHERE type = %s ORDER BY short_name",
        (inst_type,)
    )

    return  jsonify([
        {"id": r["id"],"full_name": r["full_name"],"short_name": r["short_name"]}
        for r in rows
    ])

@app.route("/api/institutions/id/<int:inst_id>")
def get_institution(inst_id):
    rows = query_db("SELECT id, full_name, short_name, type "
                    "FROM educational_institutions "
                    "WHERE id = %s",
                    (inst_id,)
                    )
    if not rows:
        return jsonify({"success": False, "error": "ОУ не найдено"}), 404
    return jsonify(rows[0])

@app.route("/api/institutions", methods=["POST"])
def api_create_institution():
    data = request.get_json() if request.is_json else request.form
    full_name = data.get("full_name", "").strip()
    short_name = data.get("short_name", "").strip()
    inst_type = data.get("type", "").strip()
    if not full_name or not short_name:
        return jsonify({"success": False, "error": "Заполните все поля"}), 400
    if inst_type not in ("ГБОУ", "ГБДОУ", "ОДОД"):
        return jsonify({"success": False, "error": "Неверный тип"}), 400

    rows = query_db("INSERT INTO educational_institutions (full_name, short_name, type) "
        "VALUES (%s, %s, %s) RETURNING id",
        (full_name, short_name, inst_type),
        fetch=False
    )
    new_id = rows[0]["id"]
    return jsonify({"success": True, "id": new_id}), 201

@app.route("/api/institutions/<int:inst_id>", methods=["PUT"])
def api_edit_institution(inst_id):
    data = request.get_json() if request.is_json else request.form
    full_name = data.get("full_name", "").strip()
    short_name = data.get("short_name", "").strip()
    inst_type = data.get("type", "").strip()

    # Валидация
    if not full_name or not short_name:
        return jsonify({"success": False, "error": "Заполните все поля"}), 400
    if inst_type not in ("ГБОУ", "ГБДОУ", "ОДОД"):
        return jsonify({"success": False, "error": "Неверный тип"}), 400

    # Проверка существования
    exists = query_db("SELECT id FROM educational_institutions WHERE id = %s", (inst_id,))
    if not exists:
        return jsonify({"success": False, "error": "ОУ не найдено"}), 404

    # Обновление
    query_db(
        "UPDATE educational_institutions SET full_name = %s, short_name = %s, type = %s WHERE id = %s",
        (full_name, short_name, inst_type, inst_id),
        fetch=False
    )

    return jsonify({"success": True})

@app.route("/api/institutions/<int:inst_id>", methods=["DELETE"])
def api_delete_institution(inst_id):
    # Проверка существования
    exists = query_db("SELECT id FROM educational_institutions WHERE id = %s", (inst_id,))
    if not exists:
        return jsonify({"success": False, "error": "ОУ не найдено"}), 404
    query_db("DELETE FROM educational_institutions WHERE id = %s", (inst_id,), fetch=False)
    return jsonify({"success": True})

@app.route("/api/custom_fields", methods=["POST"])
def api_create_custom_field():
    data = request.get_json() if request.is_json else request.form
    label = data.get("label", "").strip()
    field_type = data.get("type", "select").strip()
    options = data.get("options", [])

    # Валидация
    if not label:
        return jsonify({"success": False, "error": "Название поля обязательно"}), 400
    if field_type != "select":
        return jsonify({"success": False, "error": "Неподдерживаемый тип"}), 400
    if not isinstance(options, list) or len(options) == 0:
        return jsonify({"success": False, "error": "Отсутсвтуют варианты для выбора"}), 400

    cleaned = []
    for opt in options:
        opt = str(opt).strip()
        if opt and opt not in cleaned:
            cleaned.append(opt)

    if not cleaned:
        return jsonify({"success": False, "error": "Все варианты пустые"}), 400

    row = query_db(
        "INSERT INTO custom_fields (label, type) VALUES (%s, %s) RETURNING id",
        (label, field_type),
        fetch=False
    )
    field_id = row[0]["id"]

    for i, opt_label in enumerate(cleaned):
        query_db(
            "INSERT INTO field_options (field_id, label, sort_order) VALUES (%s, %s, %s)",
            (field_id, opt_label, i),
            fetch=False
        )

    return jsonify({"success": True, "id": field_id}), 201

# список кастомных полей
@app.route("/api/custom_fields")
def api_get_custom_fields():
    """
    Получить список существующих полей с выбором ответа
    Это описание появится в Swagger UI
    ---
    parameters:
     - name: inst_type
       in: path
    responses:
     200:
      description: Успешный ответ со списком полей с выбором ответа
      schema:
       type: array
       items:
        type: object
        properties:
         id:
          type: integer
         label:
          type: string
         type:
          type: string
    """
    fields = query_db(
        "SELECT id, label, type FROM custom_fields ORDER BY label"
    )
    return jsonify(fields)

@app.route("/api/custom_fields/<int:field_id>/options")
def api_get_custom_fields_options(field_id):
    options = query_db(
        "SELECT id, label, sort_order FROM field_options "
        "WHERE field_id = %s ORDER BY sort_order, id",
        (field_id,)
    )
    return jsonify(options)

@app.route("/institutions")
def institutions_list():
    """Страница управления ОУ с таблицей."""

    inst_type = request.args.get("type", 'ГБОУ')
    if inst_type not in ("ГБОУ", "ГБДОУ", "ОДОД"):
        inst_type = "ГБОУ"

    institutions = query_db(
        "SELECT id, full_name, short_name FROM educational_institutions "
        "WHERE type = %s ORDER BY short_name",
        (inst_type,)
    )
    return render_template("institutions_manage.html", institutions=institutions, current_type=inst_type)

@app.route("/institutions/delete/<int:inst_id>", methods=["POST"])
def delete_institution(inst_id):
    exists = query_db("SELECT id FROM educational_institutions WHERE id = %s", (inst_id,))
    if not exists:
        return jsonify({"error": "ОУ не найдено"}), 404

    query_db("DELETE FROM educational_institutions WHERE id = %s", (inst_id,), fetch=False)
    return jsonify({"success": True})

@app.route("/institutions/edit/<int:inst_id>", methods=["POST"])
def edit_institution(inst_id):
    data = request.get_json() if request.is_json else request.form
    full_name = data.get("full_name", "").strip()
    short_name = data.get("short_name", "").strip()
    inst_type = data.get("type", "").strip()

    if not full_name or not short_name or inst_type not in ("ГБОУ", "ГБДОУ", "ОДОД"):
        return jsonify({"error": "Неверные данные"}), 400

    query_db(
        "UPDATE educational_institutions SET full_name = %s, short_name = %s, type = %s WHERE id = %s",
        (full_name, short_name, inst_type, inst_id),
        fetch=False
    )
    return jsonify({"success": True})


@app.route("/institutions/create", methods=["GET", "POST"])
def create_institution():
    if request.method == "POST":

        current_type = request.form.get("current_type", "ГБОУ")
        # Универсальное чтение: JSON или form-data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        full_name = data.get("full_name", "").strip()
        short_name = data.get("short_name", "").strip()
        inst_type = data.get("type", "").strip()

        # Валидация
        if not full_name or not short_name:
            error = "Заполните все поля"
            if request.is_json:
                return jsonify({"error": error}), 400
            return render_template("institution_form.html", error=error)

        if inst_type not in ("ГБОУ", "ГБДОУ", "ОДОД"):
            error = "Неверный тип"
            if request.is_json:
                return jsonify({"error": error}), 400
            return render_template("institution_form.html", error=error)

        # Сохранение
        query_db(
            "INSERT INTO educational_institutions (full_name, short_name, type) "
            "VALUES (%s, %s, %s)",
            (full_name, short_name, inst_type),
            fetch=False
        )

        # Ответ
        if request.is_json:
            return jsonify({"success": True}), 201
        return redirect(url_for("institutions_list", type=current_type))

    # GET — форма
    return render_template("institution_form.html")

# --- Словари для полей с расширяемыми вариантами ---

@app.route("/api/reference_dicts", methods=["GET", "POST"])
def api_reference_dicts():
    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form
        name = data.get("name", "").strip()

        if not name:
            return jsonify({"success": False, "error": "Название словаря обязательно"}), 400

        # Проверка на уникальность
        exists = query_db("SELECT id FROM reference_dicts WHERE name = %s", (name,))
        if exists:
            return jsonify({"success": False, "error": "Словарь с таким названием уже существует"}), 400

        rows = query_db(
            "INSERT INTO reference_dicts (name) VALUES (%s) RETURNING id",
            (name,),
            fetch=False
        )
        return jsonify({"success": True, "id": rows[0]["id"]}), 201

    # GET
    dicts = query_db("SELECT id, name FROM reference_dicts ORDER BY name")
    return jsonify(dicts)

# --- Значение словаря ---

@app.route("/api/reference_items", methods=["GET", "POST"])
def api_reference_items():
    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form
        dict_id = data.get("dict_id")
        label = data.get("label", "").strip()

        if not dict_id or not label:
            return jsonify({"success": False, "error": "Отсутствую dict_id и label"}), 400

        dict_exist = query_db("SELECT id FROM reference_dicts WHERE id = %s", (dict_id,))
        if not dict_exist:
            return jsonify({"success": False, "error": "Словарь не найден"}), 404

        dup = query_db(
            "SELECT id FROM reference_items WHERE dict_id = %s AND label = %s", (dict_id, label)
        )
        if dup:
            return jsonify({"success": False, "error": "Такое значение уже есть в словаре"}), 400
        rows = query_db(
            "INSERT INTO reference_items (dict_id, label) VALUES (%s, %s) RETURNING id",
            (dict_id, label),
            fetch=False
        )
        return jsonify({"success": True, "id": rows[0]["id"]}), 201

    #GET: Значения по dict_id
    dict_id = request.args.get("dict_id", type=int)
    if not dict_id:
        return jsonify({"error": "dict_id обязателен"}), 400

    items = query_db(
        "SELECT id, label FROM reference_items WHERE dict_id = %s ORDER BY label",
        (dict_id,)
    )
    return jsonify(items)