from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template
from db import query_db

app = Flask(__name__)

@app.route('/')
def index():
    templates = query_db("SELECT id, name, created_at FROM templates ORDER BY id")
    return render_template("index.html", templates=templates)
