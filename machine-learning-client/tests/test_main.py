import os
import sys
import importlib
import types
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class FakeAudioCollection:
    def __init__(self, job):
        self.job = job
        self.find_one_calls = []
        self.update_one_calls = []

    def find_one(self, query):
        self.find_one_calls.append(query)
        return self.job

    def update_one(self, query, update, upsert=False):
        self.update_one_calls.append(
            {
                "query": query,
                "update": update,
                "upsert": upsert,
            }
        )


class FakeEntriesCollection:
    def __init__(self):
        self.update_one_calls = []

    def update_one(self, query, update, upsert=False):
        self.update_one_calls.append(
            {
                "query": query,
                "update": update,
                "upsert": upsert,
            }
        )


class FakeModel:
    def __init__(self, result_text="default transcript"):
        self.result_text = result_text
        self.transcribe_calls = []

    def transcribe(self, path, language="en"):
        self.transcribe_calls.append({"path": path, "language": language})
        return {"text": self.result_text}


def load_main_with_fakes(fake_model=None, fake_emotion_output=None):
    """
    Import main.py with fake whisper / transformers / pymongo modules
    so import-time model loading does not hit real external dependencies.
    """
    if fake_model is None:
        fake_model = FakeModel()

    if fake_emotion_output is None:
        fake_emotion_output = [{"label": "joy"}]

    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = lambda name: fake_model

    fake_transformers = types.ModuleType("transformers")
    fake_transformers.pipeline = lambda *args, **kwargs: (
        lambda text, truncation=True: fake_emotion_output
    )

    class FakeMongoClient:
        def __init__(self, uri):
            self.uri = uri

        def __getitem__(self, name):
            return {
                "audio_jobs": None,
                "entries": None,
            }

    fake_pymongo = types.ModuleType("pymongo")
    fake_pymongo.MongoClient = FakeMongoClient

    sys.modules["whisper"] = fake_whisper
    sys.modules["transformers"] = fake_transformers
    sys.modules["pymongo"] = fake_pymongo

    if "main" in sys.modules:
        del sys.modules["main"]

    return importlib.import_module("main")


def stop_after_one_loop(module):
    def fake_sleep(_seconds):
        raise KeyboardInterrupt

    module.time.sleep = fake_sleep


def test_processes_unprocessed_audio_job_with_audio_path():
    fake_model = FakeModel("Hello from audio")
    main = load_main_with_fakes(
        fake_model=fake_model,
        fake_emotion_output=[{"label": "joy"}],
    )

    job = {
        "_id": "job123",
        "status": "unprocessed",
        "audio_path": "/tmp/test.wav",
        "username": "kara",
        "created_at": datetime(2026, 4, 18, 12, 0, 0),
        "date": "2026-04-18",
        "entry_type": "journal",
        "prompt_text": "How are you feeling?",
    }

    audio_collection = FakeAudioCollection(job)
    entries_collection = FakeEntriesCollection()

    main.audio_collection = audio_collection
    main.entries_collection = entries_collection
    stop_after_one_loop(main)

    try:
        main.main()
    except KeyboardInterrupt:
        pass

    assert audio_collection.find_one_calls == [{"status": "unprocessed"}]
    assert fake_model.transcribe_calls == [
        {"path": "/tmp/test.wav", "language": "en"}
    ]

    assert len(audio_collection.update_one_calls) == 1
    audio_update = audio_collection.update_one_calls[0]
    assert audio_update["query"] == {"_id": "job123"}
    assert audio_update["update"]["$set"]["transcription"] == "Hello from audio"
    assert audio_update["update"]["$set"]["emotion"] == "joy"
    assert audio_update["update"]["$set"]["status"] == "processed"

    assert len(entries_collection.update_one_calls) == 1
    entry_update = entries_collection.update_one_calls[0]
    assert entry_update["query"] == {"username": "kara", "date": "2026-04-18"}
    assert entry_update["upsert"] is True

    pushed_entry = entry_update["update"]["$push"]["journal_entries"]
    assert pushed_entry["transcript"] == "Hello from audio"
    assert pushed_entry["emotion"] == "joy"
    assert pushed_entry["entry_type"] == "journal"
    assert pushed_entry["prompt_text"] == "How are you feeling?"
    assert pushed_entry["created_at"] == "2026-04-18T12:00:00"


def test_uses_existing_transcription_when_audio_path_missing():
    fake_model = FakeModel("should not be used")
    main = load_main_with_fakes(
        fake_model=fake_model,
        fake_emotion_output=[{"label": "sadness"}],
    )

    job = {
        "_id": "job456",
        "status": "unprocessed",
        "audio_path": None,
        "transcription": "Typed fallback text",
        "username": "kara",
        "created_at": datetime(2026, 4, 18, 13, 0, 0),
        "date": "2026-04-18",
    }

    audio_collection = FakeAudioCollection(job)
    entries_collection = FakeEntriesCollection()

    main.audio_collection = audio_collection
    main.entries_collection = entries_collection
    stop_after_one_loop(main)

    try:
        main.main()
    except KeyboardInterrupt:
        pass

    assert fake_model.transcribe_calls == []

    audio_update = audio_collection.update_one_calls[0]
    assert audio_update["update"]["$set"]["transcription"] == "Typed fallback text"
    assert audio_update["update"]["$set"]["emotion"] == "sadness"

    pushed_entry = entries_collection.update_one_calls[0]["update"]["$push"]["journal_entries"]
    assert pushed_entry["transcript"] == "Typed fallback text"
    assert pushed_entry["entry_type"] == "journal"
    assert pushed_entry["prompt_text"] == ""


def test_defaults_to_neutral_for_blank_text():
    fake_model = FakeModel("   ")
    main = load_main_with_fakes(
        fake_model=fake_model,
        fake_emotion_output=[{"label": "joy"}],
    )

    job = {
        "_id": "job789",
        "status": "unprocessed",
        "audio_path": "/tmp/blank.wav",
        "username": "kara",
        "created_at": datetime(2026, 4, 18, 14, 0, 0),
        "date": "2026-04-18",
    }

    audio_collection = FakeAudioCollection(job)
    entries_collection = FakeEntriesCollection()

    main.audio_collection = audio_collection
    main.entries_collection = entries_collection
    stop_after_one_loop(main)

    try:
        main.main()
    except KeyboardInterrupt:
        pass

    audio_update = audio_collection.update_one_calls[0]
    assert audio_update["update"]["$set"]["emotion"] == "neutral"

    pushed_entry = entries_collection.update_one_calls[0]["update"]["$push"]["journal_entries"]
    assert pushed_entry["emotion"] == "neutral"


def test_defaults_to_neutral_for_disallowed_emotion():
    fake_model = FakeModel("I feel something odd")
    main = load_main_with_fakes(
        fake_model=fake_model,
        fake_emotion_output=[{"label": "LOVE"}],
    )

    job = {
        "_id": "job999",
        "status": "unprocessed",
        "audio_path": "/tmp/emotion.wav",
        "username": "kara",
        "created_at": datetime(2026, 4, 18, 15, 0, 0),
        "date": "2026-04-18",
    }

    audio_collection = FakeAudioCollection(job)
    entries_collection = FakeEntriesCollection()

    main.audio_collection = audio_collection
    main.entries_collection = entries_collection
    stop_after_one_loop(main)

    try:
        main.main()
    except KeyboardInterrupt:
        pass

    audio_update = audio_collection.update_one_calls[0]
    assert audio_update["update"]["$set"]["emotion"] == "neutral"


def test_does_nothing_when_no_unprocessed_job():
    main = load_main_with_fakes()

    audio_collection = FakeAudioCollection(None)
    entries_collection = FakeEntriesCollection()

    main.audio_collection = audio_collection
    main.entries_collection = entries_collection
    stop_after_one_loop(main)

    try:
        main.main()
    except KeyboardInterrupt:
        pass

    assert audio_collection.find_one_calls == [{"status": "unprocessed"}]
    assert audio_collection.update_one_calls == []
    assert entries_collection.update_one_calls == []