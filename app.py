from dataclasses import fields
from getopt import error
from os.path import exists

from dotenv import load_dotenv
from sqlalchemy.engine import row

load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, jsonify
from db import query_db
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

    return render_template("responses.html", template=template, fields=fields, responses=rows, inst_names=inst_names)

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