from flask import Blueprint, render_template, request, redirect
from datetime import date, timedelta
from services.entry_service import *

page_bp = Blueprint("pages", __name__)

username = "test_user"


def get_current_week():
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    days = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        days.append({
            "dow": day.strftime("%a").upper(),
            "num": day.day,
            "month": day.strftime("%b"),
            "date": day.strftime("%Y-%m-%d"),
            "active": day == today
        })
    return days


@page_bp.route("/")
def home():
    entries = get_all_entries(username)
    current_week = get_current_week()
    return render_template("home.html", entries=entries, current_week=current_week)


@page_bp.route("/day")
def today():
    today_str = str(date.today())
    entry = get_entry_by_date(username, today_str)
    return render_template("day.html", date=today_str, entry=entry)


@page_bp.route("/day/<date>")
def day(date):
    entry = get_entry_by_date(username, date)
    return render_template("day.html", date=date, entry=entry)


@page_bp.route("/entries/new", methods=["POST"])
def create_entry_page():
    entry_date = request.form["date"]
    entry_data = {
        "transcript": request.form["transcript"],
        "mood": request.form.get("mood", ""),
        "timestamp": request.form.get("timestamp", "")
    }

    create_entry(username, entry_date, entry_data)
    return redirect(f"/day/{entry_date}")


@page_bp.route("/entries/<date>/edit/<int:entry_index>", methods=["POST"])
def update_entry_page(date, entry_index):
    data = {
        "transcript": request.form["transcript"],
        "mood": request.form.get("mood", ""),
        "timestamp": request.form.get("timestamp", "")
    }
    update_entry(username, date, entry_index, data)
    return redirect(f"/day/{date}")


@page_bp.route("/entries/<date>/delete/<int:entry_index>", methods=["POST"])
def delete_entry_page(date, entry_index):
    delete_entry(username, date, entry_index)
    return redirect(f"/day/{date}")