"""
Audio routes
"""

from datetime import datetime
import os
import uuid

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

    db.audio_jobs.insert_one(
        {
            "username": current_user.username,
            "created_at": datetime.utcnow(),
            "audio_path": file_path,
            "status": "unprocessed",
            "transcription": None,
            "emotion": None,
        }
    )

    # we need to have a return statement for it to work
    return jsonify({"message": "Audio uploaded successfully"}), 200
