# pylint: disable=too-few-public-methods
"""
testing app.py routes
"""

from bson.objectid import ObjectId
import app as app_module


class FakeUsersCollection:
    """fake users collection that mimics pymongo collection for testing app routes"""

    def __init__(self):
        self.users = []
        self.inserted_docs = []

    def find_one(self, query):
        """return the first user that matches the query"""
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
        """insert a new user document and return the inserted id"""
        new_doc = dict(doc)
        if "_id" not in new_doc:
            new_doc["_id"] = ObjectId()
        self.users.append(new_doc)
        self.inserted_docs.append(new_doc)
        return {"inserted_id": new_doc["_id"]}


class FakeDB:
    """fake db that mimics the structure of the real db for testing app routes"""

    def __init__(self, users_collection):
        """initialize the fake db with a users collection"""
        self.users = users_collection


def make_client_with_fake_db(fake_users):
    """create a test client with a fake db and return the client and the old db"""
    old_db = app_module.db
    app_module.db = FakeDB(fake_users)

    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    return client, old_db


def restore_db(old_db):
    """helper function to restore the original db after a test"""
    app_module.db = old_db


def test_load_user_returns_none_for_bad_object_id():
    """test that load_user returns None when given an invalid object id"""
    fake_users = FakeUsersCollection()
    old_db = app_module.db
    app_module.db = FakeDB(fake_users)

    try:
        result = app_module.load_user("not-a-valid-object-id")
        assert result is None
    finally:
        restore_db(old_db)


def test_load_user_returns_user_for_valid_id():
    """test that load_user returns a User object with the correct fields"""
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
    """test that GET /login renders the login page"""
    fake_users = FakeUsersCollection()
    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.get("/login")
        assert response.status_code == 200
    finally:
        restore_db(old_db)


def test_login_post_invalid_credentials_shows_error():
    """for POST /login with invalid credentials re-renders"""
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
    """test that POST /login with valid credentials redirects to the home page"""
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
    """test that GET /signup renders the signup page"""
    fake_users = FakeUsersCollection()
    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.get("/signup")
        assert response.status_code == 200
    finally:
        restore_db(old_db)


def test_signup_missing_fields_shows_error():
    """test that POST /signup re-renders the signup page with an error message"""
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
    """re-renders an error message about the email being taken"""
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


def test_signup_success_inserts_user_and_redirects_to_login():
    """inserts a new user into the database and redirects"""
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
    """redirects to the login page when the user is not authenticated"""
    fake_users = FakeUsersCollection()
    client, old_db = make_client_with_fake_db(fake_users)

    try:
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
    finally:
        restore_db(old_db)


def test_index_redirects_logged_in_user_to_home():
    """GET / redirects to the home page and doesn't include /login in the redirect url"""
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
