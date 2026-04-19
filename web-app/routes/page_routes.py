"""Has the page routes for the app."""

from datetime import date as dt_date, datetime, timedelta
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from services.entry_service import (
    add_task,
    create_entry,
    delete_entry,
    delete_task,
    edit_task,
    get_all_entries,
    get_entry_by_date,
    update_entry,
)

page_bp = Blueprint("pages", __name__)

PROMPTS = [
    "What stayed with you most today?",
    "What challenged you today?",
    "What made you feel calm today?",
    "What do you want to carry into tomorrow?",
    "How did you handle stress or frustration today?",
    "What felt unfinished today?",
    "What are you grateful for today?",
    "What do you need more of right now?",
]


def _parse_date(date_str):
    """Parse a date string."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return dt_date.today()


def _get_day_document(username, selected_date):
    """Get a document for a username and date."""
    return get_entry_by_date(username, selected_date) or {}


def _get_current_week(selected_date=None):
    """Get the current week."""
    current_date = _parse_date(selected_date) if selected_date else dt_date.today()
    start_of_week = current_date - timedelta(days=current_date.weekday())

    days = []
    for i in range(7):
        curr_day = start_of_week + timedelta(days=i)
        days.append(
            {
                "dow": curr_day.strftime("%a").upper(),
                "num": curr_day.day,
                "month": curr_day.strftime("%b"),
                "date": curr_day.isoformat(),
                "active": curr_day == current_date,
            }
        )
    return days


def _get_journal_entries(day_doc):
    """Get the journal entries for a certain day."""
    return day_doc.get("journal_entries", []) if isinstance(day_doc, dict) else []


def _get_prompt_entry(day_doc):
    """Get the most recent prompt entry for a day."""
    journal_entries = _get_journal_entries(day_doc)
    prompt_entries = [
        (index, journal_entry)
        for index, journal_entry in enumerate(journal_entries)
        if journal_entry.get("entry_type") == "prompt"
    ]
    if not prompt_entries:
        return None, None
    return prompt_entries[-1]


def _build_prompt_choices(current_prompt=None):
    """Generate prompt choices excluding the current prompt."""
    return [prompt for prompt in PROMPTS if prompt != current_prompt][:3]


def _day_context(username, selected_date):
    """Get day context for a user and date."""
    current_date = _parse_date(selected_date)
    normalized_date = current_date.isoformat()
    day_doc = _get_day_document(username, normalized_date)
    prev_date = (current_date - timedelta(days=1)).isoformat()
    next_date = (current_date + timedelta(days=1)).isoformat()
    return normalized_date, day_doc, prev_date, next_date


@page_bp.route("/", methods=["GET"])
@login_required
def home():
    """Render home.html."""
    username = current_user.username
    entries = get_all_entries(username)
    selected_date = request.args.get("date")
    current_week = _get_current_week(selected_date)
    current_day = dt_date.today().isoformat()
    return render_template(
        "home.html",
        entries=entries,
        username=username,
        current_week=current_week,
        date=current_day,
    )


@page_bp.route("/day")
@login_required
def today():
    """Render day.html for today or selected date."""
    username = current_user.username
    selected_date = request.args.get("date") or str(dt_date.today())
    normalized_date, entry, prev_date, next_date = _day_context(username, selected_date)
    return render_template(
        "day.html",
        date=normalized_date,
        entry=entry,
        username=username,
        prev_date=prev_date,
        next_date=next_date,
    )


@page_bp.route("/day/<date>")
@login_required
def day(date):
    """Render day.html for a specific date."""
    username = current_user.username
    normalized_date, entry, prev_date, next_date = _day_context(username, date)
    return render_template(
        "day.html",
        date=normalized_date,
        entry=entry,
        username=username,
        prev_date=prev_date,
        next_date=next_date,
    )


@page_bp.route("/reflect")
@login_required
def reflect():
    """Render reflect.html."""
    username = current_user.username
    selected_date = request.args.get("date") or str(dt_date.today())
    mode = request.args.get("mode", "prompt")
    selected_date, day_doc, _, _ = _day_context(username, selected_date)
    _, existing_entry = _get_prompt_entry(day_doc)

    selected_prompt = request.args.get("prompt")

    if mode == "continue" and existing_entry and not selected_prompt:
        current_prompt = existing_entry.get("prompt_text") or PROMPTS[0]
        mood_score = existing_entry.get("mood_score", "")
        stress_score = existing_entry.get("stress_score", "")
    else:
        current_prompt = selected_prompt or PROMPTS[0]
        mood_score = 5
        stress_score = ""

    return render_template(
        "reflect.html",
        username=username,
        date=selected_date,
        mode=mode,
        current_prompt=current_prompt,
        mood_score=mood_score,
        stress_score=stress_score,
    )


@page_bp.route("/history/<date>")
@login_required
def history(date):
    """Render history.html."""
    username = current_user.username
    selected_date = _parse_date(date).isoformat()
    day_doc = _get_day_document(username, selected_date)
    same_day_entries = _get_journal_entries(day_doc)
    saved_count = len(same_day_entries)
    return render_template(
        "history.html",
        date=selected_date,
        same_day_entries=same_day_entries,
        saved_count=saved_count,
        username=username,
    )


@page_bp.route("/entries/new", methods=["POST"])
@login_required
def create_entry_page():
    """Create an entry."""
    username = current_user.username
    entry_date = _parse_date(request.form["date"]).isoformat()
    entry_data = {
        "transcript": request.form["transcript"],
        "mood": request.form.get("mood", ""),
        "entry_type": request.form.get("entry_type", "journal"),
        "prompt_text": request.form.get("prompt_text", ""),
        "mood_score": request.form.get("mood_score", ""),
        "stress_score": request.form.get("stress_score", ""),
    }

    timestamp = request.form.get("timestamp")
    if timestamp:
        entry_data["timestamp"] = timestamp

    create_entry(username, entry_date, entry_data)
    return redirect(url_for("pages.today", username=username, date=entry_date))


@page_bp.route("/entries/<date>/<int:entry_index>/edit", methods=["POST"])
@login_required
def update_entry_page(date, entry_index):
    """Update an entry."""
    username = current_user.username
    entry_date = _parse_date(date).isoformat()
    updated_data = {
        "transcript": request.form["transcript"],
        "mood": request.form.get("mood", ""),
        "entry_type": request.form.get("entry_type", "journal"),
        "prompt_text": request.form.get("prompt_text", ""),
        "mood_score": request.form.get("mood_score", ""),
        "stress_score": request.form.get("stress_score", ""),
    }

    timestamp = request.form.get("timestamp")
    if timestamp:
        updated_data["timestamp"] = timestamp

    update_entry(username, entry_date, entry_index, updated_data)
    return redirect(url_for("pages.today", username=username, date=entry_date))


@page_bp.route("/entries/<date>/<int:entry_index>/delete", methods=["POST"])
@login_required
def delete_entry_page(date, entry_index):
    """Delete an entry."""
    username = current_user.username
    entry_date = _parse_date(date).isoformat()
    delete_entry(username, entry_date, entry_index)
    return redirect(url_for("pages.today", username=username, date=entry_date))


@page_bp.route("/tasks/new", methods=["POST"])
@login_required
def create_task_page():
    """Create a task."""
    username = current_user.username
    entry_date = _parse_date(request.form["date"]).isoformat()
    title = request.form.get("title", "").strip()
    deadline = request.form.get("deadline")
    deadline_value = deadline.strip() if deadline else None

    if title:
        add_task(
            username,
            entry_date,
            {"title": title, "completed": False, "deadline": deadline_value},
        )
    return redirect(
        url_for("pages.today", username=username, date=entry_date) + "#tasks"
    )


@page_bp.route("/tasks/<date>/<int:task_index>/edit", methods=["POST"])
@login_required
def update_task_page(date, task_index):
    """Update a task."""
    username = current_user.username
    entry_date = _parse_date(date).isoformat()
    title = request.form.get("title", "").strip()
    completed = request.form.get("completed") == "on"
    updated_task = {
        "title": title or "Untitled task",
        "completed": completed,
    }
    edit_task(username, entry_date, task_index, updated_task)
    return redirect(
        url_for("pages.today", username=username, date=entry_date) + "#tasks"
    )


@page_bp.route("/tasks/<date>/<int:task_index>/toggle", methods=["POST"])
@login_required
def toggle_task_page(date, task_index):
    """Toggle a task's completed state."""
    username = current_user.username
    entry_date = _parse_date(date).isoformat()
    day_doc = _get_day_document(username, entry_date)
    tasks = day_doc.get("tasks", []) if isinstance(day_doc, dict) else []

    if 0 <= task_index < len(tasks):
        task = tasks[task_index]
        updated_task = {
            **task,
            "title": task.get("title") or task.get("name") or "Untitled task",
            "completed": not task.get("completed", False),
        }
        edit_task(username, entry_date, task_index, updated_task)

    return redirect(
        url_for("pages.today", username=username, date=entry_date) + "#tasks"
    )


@page_bp.route("/tasks/<date>/<int:task_index>/delete", methods=["POST"])
@login_required
def delete_task_page(date, task_index):
    """Delete a task."""
    username = current_user.username
    entry_date = _parse_date(date).isoformat()
    delete_task(username, entry_date, task_index)
    return redirect(
        url_for("pages.today", username=username, date=entry_date) + "#tasks"
    )
