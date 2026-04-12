from flask import Flask, render_template, request, redirect
from datetime import date

from routes.entry_routes import entry_bp
from routes.page_routes import page_bp

app = Flask(__name__)

app.register_blueprint(entry_bp)
app.register_blueprint(page_bp)

if __name__ == "__main__":
    app.run(debug=True)