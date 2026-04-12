from flask import Blueprint, render_template, request, redirect
from datetime import date
from services.entry_service import *

page_bp = Blueprint("pages", __name__)

@page_bp.route("/")
def home():
    entries = get_all_entries()
    goals = [
        {"name": "Coffee Chat", "deadline": "Tues @8"},
        {"name": "Do HW", "deadline": "Wed @1"},
        {"name": "Reflect", "deadline": "Wed @2"},
    ]
    return render_template("home.html", entries=entries, goals=goals)

@page_bp.route("/day")
def today():
    today_str = str(date.today())
    entry = get_entry_by_date(today_str)
    return render_template("day.html", date=today_str, entry=entry)

@page_bp.route("/day/<date>")
def day(date):
    entry = get_entry_by_date(date)
    return render_template("day.html", date=date, entry=entry)

@page_bp.route("/entries/new", methods=["POST"])
def create_entry_page():
    data = {
        "date": request.form["date"],
        "transcript": request.form["transcript"],
        "mood": request.form.get("mood", "")
    }
    create_entry(data)
    return redirect(f"/day/{data['date']}")

@page_bp.route("/entries/<date>/edit", methods=["POST"])
def update_entry_page(date):
    data = {
        "transcript": request.form["transcript"],
        "mood": request.form.get("mood", "")
    }
    update_entry(date, data)
    return redirect(f"/day/{date}")

@page_bp.route("/entries/<date>/delete", methods=["POST"])
def delete_entry_page(date):
    delete_entry(date)
    return redirect("/")