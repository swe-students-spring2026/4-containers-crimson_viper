"""
Audio routes
"""

from datetime import datetime
import os
import uuid

from bson import ObjectId
from flask import Blueprint, request, redirect, url_for, jsonify
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

    selected_date = request.form.get("date")

    db.audio_jobs.insert_one(
        {
            "username": current_user.username,
            "date": selected_date,
            "created_at": datetime.utcnow(),
            "audio_path": file_path,
            "status": "unprocessed",
            "transcription": None,
            "emotion": None,
            "entry_type": request.form.get("entry_type"),
            "prompt_text": request.form.get("prompt_text"),
        }
    )
    return redirect(
        url_for(
            "pages.day",
            username=request.form.get("username"),
        )
    )


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
            "date": request.form.get("date"),
            "entry_type": request.form.get("entry_type"),
            "prompt_text": request.form.get("prompt_text"),
        }
    )
    return redirect(
        url_for(
            "pages.day",
            username=request.form.get("username"),
        )
    )


@audio_bp.route("/audio-status/<job_id>", methods=["GET"])
@login_required
def audio_status(job_id):
    """Returns the processing status of one audio job."""
    job = db.audio_jobs.find_one(
        {
            "_id": ObjectId(job_id),
            "username": current_user.username,
        }
    )

    if not job:
        return jsonify({"error": "Audio job not found"}), 404

    return (
        jsonify(
            {
                "status": job.get("status"),
                "transcription": job.get("transcription"),
                "emotion": job.get("emotion"),
            }
        ),
        200,
    )
