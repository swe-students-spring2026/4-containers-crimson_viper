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
db = client["crimson_viper"]

# we still need to decide how we are handling the audio files.
# where is the path to the files stored? It would make sense if
# we just make an entirely separate collection that stores:
# 1) userid of whoever created the audio file
# 2) the date that the audio file was uploaded to the database
# 3) whether or not the audio file has been processed
# 4) the file path to the audio file itself
# that is how this is handled here.

collection = db["audio_jobs"]

model = whisper.load_model("tiny")

emotion_analyzer = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    return_all_scores=False,
)
ALLOWED_EMOTIONS = {"anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"}

while True:
    # i think this makes sense for us to be able to find any audio
    # files that haven't yet been processed by the ml model
    job = collection.find_one({"status": "unprocessed"})

    # if there exists an audio file that hasn't yet been processed,
    # then we process it and then update the database
    if job:
        print("found an unprocessed audio file")
        path = job["audio_path"]

        result = model.transcribe(path, language="en")
        print("transcribed audio file")

        text = result["text"]
        if text and text.strip():
            emotion_result = emotion_analyzer(text, truncation=True)
            emotion_label = emotion_result[0]["label"].lower()
            if emotion_label not in ALLOWED_EMOTIONS:
                emotion_label = "neutral"
        else:
            emotion_label = "neutral"

        collection.update_one(
            {"_id": job["_id"]},
            # only update the text and status fields
            {
                "$set": {
                    "transcription": result["text"],
                    "emotion": emotion_label,
                    "status": "processed"
                }
            },
        )

        print("updated database")
    time.sleep(2)
