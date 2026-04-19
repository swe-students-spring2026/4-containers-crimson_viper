"""
testing app.py routes
"""

from bson.objectid import ObjectId
import app as app_module


class FakeUsersCollection:
    def __init__(self):
        self.users = []
        self.inserted_docs = []

    def find_one(self, query):
        for user in self.users:
            matched = True
            for key, value in query.items():
                if user.get(key) != value:
                    matched = False
                    break
            if matched:
                return user
        return None

    def insert_one(self, doc):
        new_doc = dict(doc)
        if "_id" not in new_doc:
            new_doc["_id"] = ObjectId()
        self.users.append(new_doc)
        self.inserted_docs.append(new_doc)
        return {"inserted_id": new_doc["_id"]}


class FakeDB:
    def __init__(self, users_collection):
        self.users = users_collection


def make_client_with_fake_db(fake_users):
    old_db = app_module.db
    app_module.db = FakeDB(fake_users)

    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    return client, old_db


def restore_db(old_db):
    app_module.db = old_db


def test_load_user_returns_none_for_bad_object_id():
    fake_users = FakeUsersCollection()
    old_db = app_module.db
    app_module.db = FakeDB(fake_users)

    try:
        result = app_module.load_user("not-a-valid-object-id")
        assert result is None
    finally:
        restore_db(old_db)


def test_load_user_returns_user_for_valid_id():
    fake_users = FakeUsersCollection()
    user_id = ObjectId()
    fake_users.users.append(
        {
            "_id": user_id,
            "email": "lan@example.com",
            "username": "lan",
            "password": "pw",
        }
    )

    old_db = app_module.db
    app_module.db = FakeDB(fake_users)

    try:
        result = app_module.load_user(str(user_id))
        assert result is not None
        assert result.id == str(user_id)
        assert result.email == "lan@example.com"
        assert result.username == "lan"
    finally:
        restore_db(old_db)


def test_login_get_renders_page():
    fake_users = FakeUsersCollection()
    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.get("/login")
        assert response.status_code == 200
    finally:
        restore_db(old_db)


def test_login_post_invalid_credentials_shows_error():
    fake_users = FakeUsersCollection()
    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.post(
            "/login",
            data={
                "email": "wrong@example.com",
                "password": "badpassword",
            },
        )

        assert response.status_code == 200
        assert b"Invalid email or password." in response.data
    finally:
        restore_db(old_db)


def test_login_post_success_redirects_home():
    fake_users = FakeUsersCollection()
    fake_users.users.append(
        {
            "_id": ObjectId(),
            "email": "lan@example.com",
            "username": "lan",
            "password": "pw123",
        }
    )

    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.post(
            "/login",
            data={
                "email": "Lan@Example.com",
                "password": "pw123",
            },
        )

        assert response.status_code == 302
        assert "/login" not in response.headers["Location"]
    finally:
        restore_db(old_db)


def test_signup_get_renders_page():
    fake_users = FakeUsersCollection()
    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.get("/signup")
        assert response.status_code == 200
    finally:
        restore_db(old_db)


def test_signup_missing_fields_shows_error():
    fake_users = FakeUsersCollection()
    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.post(
            "/signup",
            data={
                "email": "",
                "username": "lan",
                "password": "pw123",
            },
        )

        assert response.status_code == 200
        assert b"All fields are required." in response.data
    finally:
        restore_db(old_db)


def test_signup_duplicate_email_shows_error():
    fake_users = FakeUsersCollection()
    fake_users.users.append(
        {
            "_id": ObjectId(),
            "email": "lan@example.com",
            "username": "someoneelse",
            "password": "pw123",
        }
    )

    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.post(
            "/signup",
            data={
                "email": "lan@example.com",
                "username": "lan",
                "password": "pw123",
            },
        )

        assert response.status_code == 200
        assert b"Email already taken." in response.data
    finally:
        restore_db(old_db)


def test_signup_duplicate_username_shows_error():
    fake_users = FakeUsersCollection()
    fake_users.users.append(
        {
            "_id": ObjectId(),
            "email": "other@example.com",
            "username": "lan",
            "password": "pw123",
        }
    )

    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.post(
            "/signup",
            data={
                "email": "lan@example.com",
                "username": "lan",
                "password": "pw123",
            },
        )

        assert response.status_code == 200
        assert b"Username already taken." in response.data
    finally:
        restore_db(old_db)


def test_signup_success_inserts_user_and_redirects_to_login():
    fake_users = FakeUsersCollection()
    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.post(
            "/signup",
            data={
                "email": "Lan@Example.com",
                "username": "lan",
                "password": "pw123",
            },
        )

        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

        assert len(fake_users.inserted_docs) == 1
        assert fake_users.inserted_docs[0]["email"] == "lan@example.com"
        assert fake_users.inserted_docs[0]["username"] == "lan"
    finally:
        restore_db(old_db)


def test_index_redirects_logged_out_user_to_login():
    fake_users = FakeUsersCollection()
    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
    finally:
        restore_db(old_db)


def test_index_redirects_logged_in_user_to_home():
    fake_users = FakeUsersCollection()
    user_id = ObjectId()
    fake_users.users.append(
        {
            "_id": user_id,
            "email": "lan@example.com",
            "username": "lan",
            "password": "pw123",
        }
    )

    client, old_db = make_client_with_fake_db(fake_users)

    try:
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user_id)
            sess["_fresh"] = True

        response = client.get("/")
        assert response.status_code == 302
        assert "/" in response.headers["Location"]
        assert "/login" not in response.headers["Location"]
    finally:
        restore_db(old_db)