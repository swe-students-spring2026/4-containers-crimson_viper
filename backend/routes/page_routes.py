from flask import Blueprint, render_template, request, redirect
from datetime import date, timedelta
import json
from services.entry_service import *

page_bp = Blueprint("pages", __name__)


def load_mock_entries(username):
    with open("backend/mock_data.json") as f:
        data = json.load(f)
    # Return all journal_entries for the user, grouped by date
    return [
        {
            "date": entry["date"],
            "journal_entries": entry["journal_entries"],
            "todos": entry.get("todos", [])
        }
        for entry in data if entry["username"] == username
    ]

def load_mock_entry_by_date(username, date):
    with open("backend/mock_data.json") as f:
        data = json.load(f)
    # Return the entry for the user and date
    for entry in data:
        if entry["username"] == username and entry["date"] == date:
            return entry
    return None


def get_current_week():
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    days = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        days.append({
            "dow": day.strftime("%a").upper(),  # e.g. MON, TUE
            "num": day.day,
            "month": day.strftime("%b"),  # e.g. Jan, Feb
            "date": day.strftime("%Y-%m-%d"),
            "active": day == today
        })
    return days

@page_bp.route("/")
def home():
    entries = load_mock_entries("test_user")
    current_week = get_current_week()
    return render_template("home.html", entries=entries, current_week=current_week)

@page_bp.route("/day")
def today():
    today_str = str(date.today())
    entry = load_mock_entry_by_date("test_user", today_str)
    return render_template("day.html", date=today_str, entry=entry)

@page_bp.route("/day/<date>")
def day(date):
    entry = load_mock_entry_by_date("test_user", date)
    return render_template("day.html", date=date, entry=entry)

@page_bp.route("/entries/new", methods=["POST"])
def create_entry_page():
    data = {
        "date": request.form["date"],
        "transcript": request.form["transcript"],
        "mood": request.form.get("mood", "")
    }
    create_entry("test_user", data)
    return redirect(f"/day/{data['date']}")

@page_bp.route("/entries/<date>/edit", methods=["POST"])
def update_entry_page(date):
    data = {
        "transcript": request.form["transcript"],
        "mood": request.form.get("mood", "")
    }
    update_entry("test_user", date, data)
    return redirect(f"/day/{date}")

@page_bp.route("/entries/<date>/delete", methods=["POST"])
def delete_entry_page(date):
    delete_entry("test_user", date)
    return redirect("/")