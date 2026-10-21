from dataclasses import fields
from getopt import error

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for
from db import query_db
from validators import validate_fields
import json

app = Flask(__name__)

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

            if field["type"] == "number":
                if value == "":
                    return render_template("fill.html", template=template,
                                           fields=fields, error=f"Поле «{field['label']}» должно быть числом")
                else:
                    if value == "":
                        return render_template("fill.html", template=template, fields=fields,
                                               error=f"Поле «{field['label']}» обязательно")

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

    return render_template("responses.html", template=template, fields=fields, responses=rows)