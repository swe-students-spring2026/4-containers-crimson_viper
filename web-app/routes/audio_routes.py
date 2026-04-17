"""
Audio routes
"""

from datetime import datetime
import os
import uuid

from flask import Blueprint, request, redirect, url_for
from flask_login import login_required, current_user

from models.db import db

audio_bp = Blueprint("audio", __name__)


@audio_bp.route("/upload-audio", methods=["POST"])
@login_required
def upload_audio():
    """Uploads the audio to database and adds to shared folder"""
    audio_file = request.files.get("audio")

    filename = f"{uuid.uuid4()}.wav"
    audio_dir = "/data/audio"

    os.makedirs(audio_dir, exist_ok=True)

    file_path = os.path.join(audio_dir, filename)
    audio_file.save(file_path)

    db.audio_jobs.insert_one(
        {
            "username": current_user.username,
            "created_at": datetime.utcnow(),
            "audio_path": file_path,
            "status": "unprocessed",
            "transcription": None,
            "emotion": None,
            "date": request.form.get("date"),  # Add this
            "entry_type": request.form.get("entry_type"),  # Add this
            "prompt_text": request.form.get("prompt_text"),  # Add this
        }
    )
    return redirect(url_for('pages.reflect', username=request.form.get('username'), date=request.form.get('date')))

@audio_bp.route("/upload-text", methods=["POST"])
@login_required
def upload_text():
    """Uploads the text to database"""
    db.audio_jobs.insert_one(
        {
            "username": request.form.get("username"),
            "created_at": datetime.utcnow(),
            "audio_path": None,
            "status": "unprocessed",
            "transcription": request.form.get("transcript"),
            "emotion": None,
            "date": request.form.get("date"),  # Add this
            "entry_type": request.form.get("entry_type"),  # Add this
            "prompt_text": request.form.get("prompt_text"),  # Add this
        }
    )
    return redirect(url_for('pages.reflect', username=request.form.get('username'), date=request.form.get('date')))
