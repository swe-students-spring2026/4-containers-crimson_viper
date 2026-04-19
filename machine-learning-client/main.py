"""
Machine learning client transcribing audio
- Checks MongoDB for unprocessed audio files
- Uses Whisper to transcribe the audio files
- Updates the transcription in MongoDB
"""

import time

import whisper
from pymongo import MongoClient
from transformers import pipeline

client = MongoClient("mongodb://mongodb:27017/")
database = client["crimson_viper"]
audio_collection = database["audio_jobs"]
entries_collection = database["entries"]

model = whisper.load_model("tiny")

emotion_analyzer = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    return_all_scores=False,
)
ALLOWED_EMOTIONS = {"anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"}


def main():
    """main loop that continuously checks for unprocessed audio files and processes them"""
    while True:
        job = audio_collection.find_one({"status": "unprocessed"})

        if job:
            print("found an unprocessed audio file")
            path = job["audio_path"]
            username = job["username"]
            created_at = job["created_at"]
            date = job.get("date")
            entry_type = job.get("entry_type", "journal")
            prompt_text = job.get("prompt_text", "")

            if path:
                transcription_result = model.transcribe(path, language="en")
                print("transcribed audio file")
                text = transcription_result["text"]
            else:
                text = job.get("transcription", "")

            if text and text.strip():
                emotion_result = emotion_analyzer(text, truncation=True)
                emotion_label = emotion_result[0]["label"].lower()
                if emotion_label not in ALLOWED_EMOTIONS:
                    emotion_label = "neutral"
            else:
                emotion_label = "neutral"

            audio_collection.update_one(
                {"_id": job["_id"]},
                # only update the text and status fields
                {
                    "$set": {
                        "transcription": text,
                        "emotion": emotion_label,
                        "status": "processed",
                    }
                },
            )

            entries_collection.update_one(
                {"username": username, "date": date},
                {
                    "$setOnInsert": {"username": username, "date": date, "tasks": []},
                    "$push": {
                        "journal_entries": {
                            "transcript": text,
                            "emotion": emotion_label,
                            "entry_type": entry_type,
                            "prompt_text": prompt_text,
                            "created_at": created_at.isoformat(),
                        }
                    },
                },
                upsert=True,
            )

            print("updated database")
        time.sleep(2)


if __name__ == "__main__":
    main()
