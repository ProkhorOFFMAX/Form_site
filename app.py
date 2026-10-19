from dataclasses import fields
from getopt import error

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for
from db import query_db
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
            if not isinstance(fields, list) or len(fields) == 0:
                raise ValueError("Должно быть хотя бы одно поле для ввода")
            for field in fields:
                if "label" not in field or "type" not in field:
                    raise ValueError("У каждого поля должны быть label и type")
                if field["type"] not in ('text', 'number'):
                    raise ValueError("Тип поля должен быть text или number")
        except (json.JSONDecodeError, ValueError) as e:
            return render_template("create.html", error=f"Ошибка в полях: {e}")

        query_db(
            "INSERT INTO templates (name, fields) VALUES (%s, %s)",
            (name, json.dumps(fields)),
            fetch=False
        )

        return redirect(url_for("index"))
    return render_template("create.html")