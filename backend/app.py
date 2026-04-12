from flask import Flask, render_template, request, redirect
from datetime import date

from routes.entry_routes import entry_bp
from routes.page_routes import page_bp

app = Flask(__name__)

app.register_blueprint(entry_bp)
app.register_blueprint(page_bp)

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
    app.run(debug=True)