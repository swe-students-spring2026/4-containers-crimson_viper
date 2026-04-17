"""
Audio routes
"""

from datetime import datetime
import os
import uuid

from bson import ObjectId
from flask import Blueprint, request, jsonify
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

    insert_result = db.audio_jobs.insert_one(
        {
            "username": current_user.username,
            "date": selected_date,
            "created_at": datetime.utcnow(),
            "audio_path": file_path,
            "status": "unprocessed",
            "transcription": None,
            "emotion": None,
        }
    )

    return jsonify(
        {
            "message": "Audio uploaded successfully",
            "job_id": str(insert_result.inserted_id),
        }
    ), 200

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

    return jsonify(
        {
            "status": job.get("status"),
            "transcription": job.get("transcription"),
            "emotion": job.get("emotion"),
        }
    ), 200
