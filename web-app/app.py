from flask import Flask, render_template, request, redirect, url_for
from datetime import date

# for the login
import os
from pymongo import MongoClient
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from bson.objectid import ObjectId

from routes.entry_routes import entry_bp
from routes.page_routes import page_bp

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret-key")

app.register_blueprint(entry_bp)
app.register_blueprint(page_bp)

# set up the database #database is different from backend's diary_db
mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017/crimson_viper")
client = MongoClient(mongo_uri)
db = client["crimson_viper"]


# flask login 
login_manager = LoginManager()
login_manager.init_app(app)

# this is where we redirect to if we are not logged in
login_manager.login_view = "login" 

class User(UserMixin):
    def __init__(self, user):
        self.id = str(user["_id"])
        self.email = user["email"]
        self.username = user["username"]

@login_manager.user_loader
def load_user(user_id):
    # session stores user's _id; load user by _id
    try:
        oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
        user = db.users.find_one({"_id": oid})
        if user:
            return User(user)
    except Exception:
        pass
    return None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        # check the database
        user = db.users.find_one({"email": email})
        if user and user["password"] == password:
            login_user(User(user))

            # this should be updated to point to the home page
            # return redirect(url_for("home"))

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not email or not username or not password:
            return render_template("signup.html", error="All fields are required.")

        if db.users.find_one({"email": email}):
            return render_template("signup.html", error="Email already taken.")

        # can input new fields later
        db.users.insert_one({
            "email": email,
            "username": username,
            "password": password,
        })

        return redirect(url_for("login"))
    return render_template("signup.html")

# this is for logging out when we set it up later

# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for("login"))

# @app.route("/")
# def home():
#     return render_template("base.html")

# @app.route("/day/<date>")
# def day(date):
#     entry = get_entry_by_date(date)
#     return render_template("day.html", date=date, entry=entry)

# @app.route("/entries", methods=["POST"])
# def create_entry_route():
#     data = {
#         "date": request.form["date"],
#         "transcript": request.form["transcript"]
#     }
#     create_entry(data)
#     return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)