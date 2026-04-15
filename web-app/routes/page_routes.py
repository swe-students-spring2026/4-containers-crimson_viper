"""
Has the page routes for the app
"""

from datetime import date as dt_date, datetime, timedelta
import random

from flask import Blueprint, abort, redirect, render_template, request, url_for

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


def _get_username(required=True):
    """Gets username"""
    username = (
        request.args.get("username")
        or request.form.get("username")
        or request.values.get("username")
    )
    if required and not username:
        abort(400, description="username is required")
    return username


def _parse_date(date_str):
    """Parses a date string"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return dt_date.today()


def _get_day_document(username, selected_date):
    """Gets a document for a username and date"""
    return get_entry_by_date(username, selected_date) or {}


def _get_current_week(selected_date=None):
    """Gets the current week"""
    current_date = _parse_date(selected_date) if selected_date else dt_date.today()
    start_of_week = current_date - timedelta(days=current_date.weekday())

    days = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        days.append(
            {
                "dow": day.strftime("%a").upper(),
                "num": day.day,
                "month": day.strftime("%b"),
                "date": day.isoformat(),
                "active": day == current_date,
            }
        )
    return days


def _get_journal_entries(day_doc):
    """Gets the journal entries for a certain day"""
    return day_doc.get("journal_entries", []) if isinstance(day_doc, dict) else []


def _get_prompt_entry(day_doc):
    """Gets the prompt for a certain day"""
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
    """Generates the prompt choices"""
    pool = PROMPTS[:]
    if len(pool) >= 3:
        prompt_choices = random.sample(pool, 3)
    else:
        prompt_choices = pool

    if current_prompt:
        prompt_choices = [
            prompt for prompt in prompt_choices if prompt != current_prompt
        ]
        prompt_choices.insert(0, current_prompt)

    seen = []
    deduped = []
    for prompt in prompt_choices:
        if prompt not in seen:
            seen.append(prompt)
            deduped.append(prompt)
    return deduped[:3]


def _day_context(username, selected_date):
    """Gets the context for a user for a certain day"""
    current_date = _parse_date(selected_date)
    normalized_date = current_date.isoformat()
    day_doc = _get_day_document(username, normalized_date)
    prev_date = (current_date - timedelta(days=1)).isoformat()
    next_date = (current_date + timedelta(days=1)).isoformat()
    return normalized_date, day_doc, prev_date, next_date


@page_bp.route("/", methods=["GET"])
def home():
    """Renders home.html"""
    username = _get_username(required=False)
    entries = get_all_entries(username) if username else []
    selected_date = request.args.get("date")
    current_week = _get_current_week(selected_date)
    return render_template(
        "home.html",
        entries=entries,
        username=username,
        current_week=current_week,
    )


@page_bp.route("/day")
def today():
    """Renders day.html"""
    username = _get_username()
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
def day(date):
    """Renders day.html"""
    username = _get_username()
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
def reflect():
    """Renders reflect.html"""
    username = _get_username()
    selected_date = request.args.get("date") or str(dt_date.today())
    mode = request.args.get("mode", "prompt")
    selected_date, day_doc, _, _ = _day_context(username, selected_date)
    existing_entry_index, existing_entry = _get_prompt_entry(day_doc)

    if mode == "continue" and existing_entry:
        current_prompt = existing_entry.get("prompt_text") or PROMPTS[0]
        transcript_value = existing_entry.get("transcript", "")
        mood_score = existing_entry.get("mood_score", "")
        stress_score = existing_entry.get("stress_score", "")
    else:
        current_prompt = request.args.get("prompt") or PROMPTS[0]
        transcript_value = ""
        mood_score = ""
        stress_score = ""
        existing_entry = None
        existing_entry_index = None

    prompt_choices = _build_prompt_choices(current_prompt)

    return render_template(
        "reflect.html",
        username=username,
        date=selected_date,
        mode=mode,
        prompts=prompt_choices,
        current_prompt=current_prompt,
        existing_entry=existing_entry,
        existing_entry_index=existing_entry_index,
        transcript_value=transcript_value,
        mood_score=mood_score,
        stress_score=stress_score,
    )


@page_bp.route("/history/<date>")
def history(date):
    """Renders history.html"""
    username = _get_username(required=False)
    selected_date = _parse_date(date).isoformat()
    day_doc = _get_day_document(username, selected_date) if username else {}
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
def create_entry_page():
    """Creates an entry page"""
    username = _get_username()
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

    if entry_data["entry_type"] == "prompt":
        return redirect(url_for("pages.today", username=username, date=entry_date))
    return redirect(url_for("pages.today", username=username, date=entry_date))


@page_bp.route("/entries/<date>/<int:entry_index>/edit", methods=["POST"])
def update_entry_page(date, entry_index):
    """Updates an entry page"""
    username = _get_username()
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

    if updated_data["entry_type"] == "prompt":
        return redirect(url_for("pages.today", username=username, date=entry_date))
    return redirect(url_for("pages.today", username=username, date=entry_date))


@page_bp.route("/entries/<date>/<int:entry_index>/delete", methods=["POST"])
def delete_entry_page(date, entry_index):
    """Deletes an entry page"""
    username = _get_username()
    entry_date = _parse_date(date).isoformat()
    delete_entry(username, entry_date, entry_index)
    return redirect(url_for("pages.today", username=username, date=entry_date))


@page_bp.route("/tasks/new", methods=["POST"])
def create_task_page():
    """Creates a task page"""
    username = _get_username()
    entry_date = _parse_date(request.form["date"]).isoformat()
    title = request.form.get("title", "").strip()
    if title:
        add_task(
            username,
            entry_date,
            {
                "title": title,
                "completed": False,
            },
        )
    return redirect(
        url_for("pages.today", username=username, date=entry_date) + "#tasks"
    )


@page_bp.route("/tasks/<date>/<int:task_index>/edit", methods=["POST"])
def update_task_page(date, task_index):
    """Updates a task page"""
    username = _get_username()
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
def toggle_task_page(date, task_index):
    """Toggles the task page"""
    username = _get_username()
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
def delete_task_page(date, task_index):
    """Deletes a task page"""
    username = _get_username()
    entry_date = _parse_date(date).isoformat()
    delete_task(username, entry_date, task_index)
    return redirect(
        url_for("pages.today", username=username, date=entry_date) + "#tasks"
    )
