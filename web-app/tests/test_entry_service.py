# pylint: disable=protected-access,unused-argument,too-few-public-methods
"""
testing entry service functions
"""

from services import entry_service


class FakeUpdateResult:
    """fake object that mimics pymongo update_one result"""

    def __init__(self, modified_count=1, upserted_id=None):
        self.modified_count = modified_count
        self.upserted_id = upserted_id


class FakeCollection:
    """fake collection that mimics pymongo collection for testing entry service functions"""

    def __init__(self):
        """fake collection that mimics pymongo collection"""
        self.find_one_result = None
        self.find_result = []
        self.update_one_result = FakeUpdateResult()
        self.last_find_one_query = None
        self.last_find_query = None
        self.last_update_one_args = None
        self.last_update_one_kwargs = None

    def find_one(self, query):
        """return configuerd fine_one result and store the query"""
        self.last_find_one_query = query
        return self.find_one_result

    def find(self, query):
        """return configured find result and store the query"""
        self.last_find_query = query
        return self.find_result

    def update_one(self, *args, **kwargs):
        """return configured update_one result and store the args/kwargs"""
        self.last_update_one_args = args
        self.last_update_one_kwargs = kwargs
        return self.update_one_result


def test_create_entry_adds_entry():
    """test that create_entry adds an entry to the correct day document"""
    fake_collection = FakeCollection()
    entry_service.entries_collection = fake_collection

    result = entry_service.create_entry(
        "test_user",
        "2026-04-18",
        {"transcript": "test content", "entry_type": "journal"},
    )

    assert result is True
    assert fake_collection.last_update_one_args[0] == {
        "username": "test_user",
        "date": "2026-04-18",
    }

    pushed_entry = fake_collection.last_update_one_args[1]["$push"]["journal_entries"]
    assert pushed_entry["transcript"] == "test content"
    assert pushed_entry["entry_type"] == "journal"
    assert "entry_id" in pushed_entry
    assert "created_at" in pushed_entry
    assert fake_collection.last_update_one_kwargs["upsert"] is True


def test_get_all_entries_returns_find_result():
    """test that get_all_entries returns the result of find with the correct query"""
    fake_collection = FakeCollection()
    entry_service.entries_collection = fake_collection

    fake_collection.find_result = [
        {"_id": 1, "username": "user1", "date": "2026-04-18"},
        {"_id": 2, "username": "user1", "date": "2026-04-19"},
    ]

    result = entry_service.get_all_entries("user1")

    assert len(result) == 2
    assert fake_collection.last_find_query == {"username": "user1"}


def test_get_entry_by_date_returns_day_document():
    """test that get_entry_by_date returns the correct day document with journal entries sorted by created_at"""
    fake_collection = FakeCollection()
    entry_service.entries_collection = fake_collection

    fake_collection.find_one_result = {
        "_id": 1,
        "username": "user1",
        "date": "2026-04-18",
        "journal_entries": [
            {"transcript": "later", "created_at": "2026-04-18T10:00:00"},
            {"transcript": "earlier", "created_at": "2026-04-18T09:00:00"},
        ],
    }

    result = entry_service.get_entry_by_date("user1", "2026-04-18")

    assert result["username"] == "user1"
    assert result["date"] == "2026-04-18"
    assert result["tasks"] == []
    assert result["journal_entries"][0]["transcript"] == "earlier"
    assert result["journal_entries"][1]["transcript"] == "later"


def test_update_entry_changes_requested_entry():
    """test that update_entry updates the correct entry and only updates the provided fields"""
    fake_collection = FakeCollection()
    entry_service.entries_collection = fake_collection

    fake_collection.find_one_result = {
        "journal_entries": [
            {"transcript": "old content", "entry_type": "journal", "mood": "sad"}
        ]
    }

    result = entry_service.update_entry(
        "test_user",
        "2026-04-18",
        0,
        {"transcript": "new content"},
    )

    assert result == 1
    assert fake_collection.last_update_one_args[0] == {
        "username": "test_user",
        "date": "2026-04-18",
    }

    updated_entry = fake_collection.last_update_one_args[1]["$set"]["journal_entries.0"]
    assert updated_entry["transcript"] == "new content"
    assert updated_entry["entry_type"] == "journal"
    assert updated_entry["mood"] == "sad"
