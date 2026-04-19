"""Flask application for audio journal management and authentication."""

import os

from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import Flask, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_user,
    login_required,
    logout_user,
)

from routes.entry_routes import entry_bp
from routes.page_routes import page_bp
from routes.audio_routes import audio_bp

# we need to grab the database from the db.py file
from models.db import db

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret-key")

app.register_blueprint(entry_bp)
app.register_blueprint(page_bp)
app.register_blueprint(audio_bp)


# flask login
login_manager = LoginManager()
login_manager.init_app(app)

# this is where we redirect to if we are not logged in
login_manager.login_view = "login"


class User(UserMixin):
    """User model used by Flask-Login to track authenticated sessions."""

    def __init__(self, user_data):
        """Populate the session-facing user fields from a database document."""
        self.id = str(user_data["_id"])
        self.email = user_data["email"]
        self.username = user_data["username"]


@login_manager.user_loader
def load_user(user_id):
    """Load a user document by id from the session cookie."""
    try:
        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        user = db.users.find_one({"_id": oid})
        if user:
            return User(user)
    except (InvalidId, TypeError):
        return None
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a user with an email address and password."""
    if request.method == "POST":
        # Normalize email input because email addresses are case-insensitive.
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.users.find_one({"email": email})
        if user and user["password"] == password:
            login_user(User(user))
            return redirect(url_for("pages.home"))

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Create a new user account when the submitted form is valid."""
    if request.method == "POST":
        # Normalize email input because email addresses are case-insensitive.
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not email or not username or not password:
            return render_template("signup.html", error="All fields are required.")

        if db.users.find_one({"email": email}):
            return render_template("signup.html", error="Email already taken.")

        if db.users.find_one({"username": username}):
            return render_template("signup.html", error="Username already taken.")

        db.users.insert_one(
            {
                "email": email,
                "username": username,
                "password": password,
            }
        )

        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route("/logout")
@login_required
def logout():
    """Log out the current user and return them to the login page."""
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
def index():
    """Redirect authenticated users home and guests to the login page."""
    if current_user.is_authenticated:
        return redirect(url_for("pages.home", username=current_user.username))
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
