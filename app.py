from dataclasses import fields
from getopt import error
from os.path import exists
import os
from dotenv import load_dotenv
from sqlalchemy.engine import row

load_dotenv()
from models import User
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash
from db import query_db, get_connection
from validators import validate_fields
import json
from flasgger import Swagger

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"] # обязательно для сессий

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # куда редиректить неавторизованных

@login_manager.user_loader
def load_user(user_id):
    rows = query_db("SELECT id, email, password_hash, role FROM users WHERE id = %s", (user_id,))
    if not rows:
        return None
    return User(rows[0]["id"], rows[0]["email"], rows[0]["password_hash"], rows[0]["role"])

swagger = Swagger(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        rows = query_db("SELECT id, email, password_hash, role FROM users WHERE email = %s", (email,))
        if not rows:
            return render_template("login.html", error="Неверный email или пароль")

        user = User(rows[0]["id"], rows[0]["email"], rows[0]["password_hash"], rows[0]["role"])
        if not user.check_password(password):
            return render_template("login.html", error="Неверный email или пароль")

        login_user(user)
        # Редирект в зависимости от роли
        if user.is_admin():
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("index"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

import click

@app.cli.command("create-admin")
@click.argument("email")
@click.argument("password")
def create_admin(email, password):
    """Создать администратора."""
    password_hash = generate_password_hash(password)
    query_db(
        "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'admin')",
        (email, password_hash),
        fetch=False
    )
    print(f"Админ {email} создан")

@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        return "Доступ запрещён", 403
    return f"<h1>Админ-панель</h1><p>Вы вошли как {current_user.email}</p><a href='/'>На главную</a><br><a href='/logout'>Выйти</a>"


@app.route("/admin/users/create", methods=["GET", "POST"])
@login_required
def admin_create_user():
    if not current_user.is_admin():
        return "Доступ запрещён", 403

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user").strip()

        # Валидация
        if not email or not password:
            return render_template("admin_create_user.html", error="Email и пароль обязательны")

        if role not in ("user", "admin"):
            return render_template("admin_create_user.html", error="Неверная роль")

        if len(password) < 6:
            return render_template("admin_create_user.html", error="Пароль должен быть не короче 6 символов")

        # Проверка на дубликат (email UNIQUE)
        exists = query_db("SELECT id FROM users WHERE email = %s", (email,))
        if exists:
            return render_template("admin_create_user.html", error="Пользователь с таким email уже существует")

        # Создание
        password_hash = generate_password_hash(password)
        query_db(
            "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
            (email, password_hash, role),
            fetch=False
        )

        return redirect(url_for("admin_users"))

    return render_template("admin_create_user.html")


@app.route("/admin/users")
@login_required
def admin_users():
    if not current_user.is_admin():
        return "Доступ запрещён", 403

    users = query_db("SELECT id, email, role, created_at FROM users ORDER BY created_at DESC")
    return render_template("admin_users.html", users=users)


@login_required
def admin_create_user():
    if not current_user.is_admin():
        return "Доступ запрещён", 403

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user").strip()

        # Валидация
        if not email or not password:
            return render_template("admin_create_user.html", error="Email и пароль обязательны")

        if role not in ("user", "admin"):
            return render_template("admin_create_user.html", error="Неверная роль")

        if len(password) < 6:
            return render_template("admin_create_user.html", error="Пароль должен быть не короче 6 символов")

        # Проверка на дубликат (email UNIQUE)
        exists = query_db("SELECT id FROM users WHERE email = %s", (email,))
        if exists:
            return render_template("admin_create_user.html", error="Пользователь с таким email уже существует")

        # Создание
        password_hash = generate_password_hash(password)
        query_db(
            "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
            (email, password_hash, role),
            fetch=False
        )

        return redirect(url_for("admin_users"))

    return render_template("admin_create_user.html")

@app.route("/")
@login_required
def index():
    if current_user.is_admin():
        # Админ видит все шаблоны + кнопку создания
        templates = query_db(
            "SELECT id, name, created_at FROM templates ORDER BY created_at DESC"
        )
        return render_template("index_admin.html", templates=templates)
    else:
        # Пользователь видит только разрешённые
        templates = query_db("""
            SELECT t.id, t.name, t.created_at
            FROM templates t
            JOIN template_access a ON a.template_id = t.id
            WHERE a.user_id = %s
            ORDER BY t.created_at DESC
        """, (current_user.id,))
        return render_template("index_user.html", templates=templates)


@app.route("/admin/templates/<int:template_id>/access", methods=["GET", "POST"])
@login_required
def admin_template_access(template_id):
    if not current_user.is_admin():
        return "Доступ запрещён", 403

    # Проверяем, что шаблон существует
    template = query_db("SELECT id, name FROM templates WHERE id = %s", (template_id,))
    if not template:
        return "Шаблон не найден", 404

    if request.method == "POST":
        # Получаем список выбранных user_id
        user_ids = request.form.getlist("user_ids")

        # Удаляем старые разрешения
        query_db("DELETE FROM template_access WHERE template_id = %s", (template_id,), fetch=False)

        # Добавляем новые
        for uid in user_ids:
            query_db(
                "INSERT INTO template_access (template_id, user_id) VALUES (%s, %s)",
                (template_id, int(uid)),
                fetch=False
            )

        return redirect(url_for("admin_template_access", template_id=template_id))

    # GET: показываем всех пользователей и отмечаем, у кого есть доступ
    users = query_db("SELECT id, email FROM users WHERE role = 'user' ORDER BY email")
    access_rows = query_db(
        "SELECT user_id FROM template_access WHERE template_id = %s",
        (template_id,)
    )
    allowed_ids = {r["user_id"] for r in access_rows}

    return render_template(
        "admin_template_access.html",
        template=template[0],
        users=users,
        allowed_ids=allowed_ids
    )



@app.route('/create_template', methods=['GET', 'POST'])
def create_template():
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

@app.route('/fill/<int:template_id>')
@login_required  # только авторизованные
def fill(template_id):
    templates = query_db("SELECT id, name, fields FROM templates WHERE id = %s", (template_id,))
    if not templates:
        return "Шаблон не найден", 404

    template = templates[0]
    fields = template["fields"]
    return render_template("fill.html", template=template, fields=fields)

@app.route('/api/responses', methods=['POST'])
@login_required
def api_responses():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Нет данных"}), 400
    template_id = data.get("template_id")
    answers = data.get("answers", {})
    if not template_id:
        return jsonify({"success": False, "error": "template_id обязателен"}), 400
    templates = query_db("SELECT fields FROM templates WHERE id = %s", (template_id,))
    if not templates:
        return jsonify({"success": False, "error": "Шаблон не найден"}), 404

    fields = templates[0]["fields"]
    # Валидация ответов (упрощённо — проверяем, что все обязательные поля заполнены)
    #for field in fields:
    #    if field.get("required") and not answers.get(field["id"]):
    #        return jsonify({"success": False, "error": f"Поле «{field['label']}» обязательно"}), 400

    for field in fields:
        if field.get("type") == "reference_text":
            answer = answers.get(field["id"])
            if isinstance(answer, dict) and answer.get("original"):
                match = query_db(
                    "SELECT id FROM reference_items WHERE dict_id = %s AND label = %s",
                    (field["dict_id"], answer["original"])
                )
                answer["linked_id"] = match[0]["id"] if match else None
                answers[field["id"]] = answer
        #elif field["type"] == "institution":
        #    answer = answers.get(field["id"])
        #    answers[field["id"]] = int(answer)

    # Сохраняем с привязкой к пользователю
    rows = query_db(
        "INSERT INTO responses (template_id, data, user_id) VALUES (%s, %s, %s) RETURNING id",
        (template_id, json.dumps(answers), current_user.id), #current_user.id — Flask-Login
        fetch=False
    )

    return jsonify({"success": True, "id": rows[0]["id"]}), 201

@app.route("/admin/responses")
@login_required
def admin_responses():
    if not current_user.is_admin():
        return "Доступ запрещён", 403

    rows = query_db("""
        SELECT r.id, r.data, r.submitted_at, u.email, t.name AS template_name
        FROM responses r
        JOIN users u ON u.id = r.user_id
        JOIN templates t ON t.id = r.template_id
        ORDER BY r.submitted_at DESC
    """)
    return render_template("admin_responses.html", responses=rows)


@app.route("/responses/<int:template_id>")
@login_required
def responses(template_id):
    templates = query_db("SELECT id, name, fields FROM templates WHERE id = %s", (template_id,))
    if not templates:
        return "Шаблон не найден", 404

    template = templates[0]
    fields = template["fields"]

    if current_user.is_admin():
        # Админ видит ВСЕ ответы с email пользователей
        rows = query_db("""
            SELECT r.id, r.data, r.submitted_at, u.email
            FROM responses r
            LEFT JOIN users u ON u.id = r.user_id
            WHERE r.template_id = %s
            ORDER BY r.submitted_at DESC
        """, (template_id,))
    else:
        # Пользователь видит ТОЛЬКО свои ответы
        rows = query_db("""
            SELECT r.id, r.data, r.submitted_at
            FROM responses r
            WHERE r.template_id = %s AND r.user_id = %s
            ORDER BY r.submitted_at DESC
        """, (template_id, current_user.id))

    # --- Сбор названий ОУ (как раньше) ---
    all_inst_ids = set()
    for row in rows:
        for field in fields:
            if field.get("type") == "institution":
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

    # --- Сбор названий вариантов custom_select ---
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

    return render_template(
        "responses.html",
        template=template,
        fields=fields,
        responses=rows,
        inst_names=inst_names,
        option_labels=option_labels,
        is_admin=current_user.is_admin()  # <-- передаём флаг в шаблон
    )

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