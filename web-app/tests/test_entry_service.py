'''
testing entry service functions
'''
import services.entry_service as entry_service

class FakeUpdateResult:
    def __init__(self, modified_count=1, upserted_id=None):
        self.modified_count = modified_count
        self.upserted_id = upserted_id

class FakeCollection:
    def __init__(self):
        self.find_one_result = None
        self.find_result = []
        self.update_one_result = FakeUpdateResult()
        self.last_find_query = None
        self.last_update_one_args = None
        self.last_update_one_kwargs = None

    def find_one(self, query):
        self.last_find_query = query
        return self.find_one_result

    def update_one(self, *args, **kwargs):
        self.last_update_one_args = args
        self.last_update_one_kwargs = kwargs
        return self.update_one_result

def test_create_entry_adds_entry():
    fake_collection = FakeCollection()
    entry_service.db.entries = fake_collection

    # Simulate no existing entry
    fake_collection.find_one_result = None

    result = entry_service.create_entry("test_user", "test_page", "test_content")

    assert result == True
    assert fake_collection.last_find_query == {"username": "test_user", "page_name": "test_page"}
    assert fake_collection.last_update_one_args[0] == {"username": "test_user", "page_name": "test_page"}
    assert "$set" in fake_collection.last_update_one_kwargs["update"]
    assert fake_collection.last_update_one_kwargs["upsert"] == True

def test_get_all_entres_for_page():
    fake_collection = FakeCollection()
    entry_service.db.entries = fake_collection

    # Simulate some entries for the page
    fake_collection.find_result = [
        {"username": "user1", "page_name": "test_page", "content": "entry1"},
        {"username": "user2", "page_name": "test_page", "content": "entry2"},
    ]

    result = entry_service.get_all_entries_for_page("test_page")

    assert result == [
        {"username": "user1", "page_name": "test_page", "content": "entry1"},
        {"username": "user2", "page_name": "test_page", "content": "entry2"},
    ]
    assert fake_collection.last_find_query == {"page_name": "test_page"}

def test_get_entry_by_date_sort_entries_and_adds_tasks():
    fake_collection = FakeCollection()
    entry_service.db.entries = fake_collection

    # Simulate some entries for the page
    fake_collection.find_result = [
        {"username": "user1", "page_name": "test_page", "content": "entry1", "date": "2024-01-01"},
        {"username": "user2", "page_name": "test_page", "content": "entry2", "date": "2024-01-02"},
    ]

    result = entry_service.get_entry_by_date("test_page")

    assert result == [
        {"username": "user2", "page_name": "test_page", "content": "entry2", "date": "2024-01-02"},
        {"username": "user1", "page_name": "test_page", "content": "entry1", "date": "2024-01-01"},
    ]
    assert fake_collection.last_find_query == {"page_name": "test_page"}

def test_update_entry_changes_requested_entry():
    fake_collection = FakeCollection()
    entry_service.db.entries = fake_collection

    # Simulate existing entry
    fake_collection.find_one_result = {"username": "test_user", "page_name": "test_page", "content": "old_content"}

    result = entry_service.update_entry("test_user", "test_page", "new_content")

    assert result == True
    assert fake_collection.last_find_query == {"username": "test_user", "page_name": "test_page"}
    assert fake_collection.last_update_one_args[0] == {"username": "test_user", "page_name": "test_page"}
    assert "$set" in fake_collection.last_update_one_kwargs["update"]
    assert fake_collection.last_update_one_kwargs["update"]["$set"]["content"] == "new_content"
    assert fake_collection.last_update_one_kwargs["upsert"] == True

