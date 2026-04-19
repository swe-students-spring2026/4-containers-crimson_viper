from flask import Flask
from flask_login import LoginManager, UserMixin, login_user
import os
import routes.page_routes as page_routes
page_routes.render_template = lambda template, **kwargs: str(kwargs)

class DummyUser(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


def make_app():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "..", "templates")
    )
    app.config["SECRET_KEY"] = "test-secret"
    app.config["LOGIN_DISABLED"] = False

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return DummyUser(user_id, "lan")

    @app.route("/force-login")
    def force_login():
        login_user(DummyUser("1", "lan"))
        return "logged in"

    app.register_blueprint(page_routes.page_bp)
    return app


def login(client):
    client.get("/force-login")


def test_reflect_default_prompt_mode():
    app = make_app()
    client = app.test_client()
    login(client)

    old_day_context = page_routes._day_context
    old_get_prompt_entry = page_routes._get_prompt_entry

    try:
        page_routes._day_context = lambda username, selected_date: (
            "2026-04-18",
            {},
            "2026-04-17",
            "2026-04-19",
        )
        page_routes._get_prompt_entry = lambda day_doc: (None, None)

        response = client.get("/reflect?date=2026-04-18")
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "'mode': 'prompt'" in text
        assert "'current_prompt': 'What stayed with you most today?'" in text
    finally:
        page_routes._day_context = old_day_context
        page_routes._get_prompt_entry = old_get_prompt_entry

def test_reflect_continue_mode_uses_existing_prompt_entry():
    app = make_app()
    client = app.test_client()
    login(client)

    old_day_context = page_routes._day_context
    old_get_prompt_entry = page_routes._get_prompt_entry

    try:
        page_routes._day_context = lambda username, selected_date: (
            "2026-04-18",
            {"journal_entries": []},
            "2026-04-17",
            "2026-04-19",
        )
        page_routes._get_prompt_entry = lambda day_doc: (
            0,
            {
                "prompt_text": "Old saved prompt",
                "transcript": "saved words",
                "mood_score": "7",
                "stress_score": "3",
                "entry_type": "prompt",
            },
        )

        response = client.get("/reflect?date=2026-04-18&mode=continue")
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "'mode': 'continue'" in text
        assert "'current_prompt': 'Old saved prompt'" in text
        assert "'transcript_value': 'saved words'" in text
        assert "'mood_score': '7'" in text
        assert "'stress_score': '3'" in text
    finally:
        page_routes._day_context = old_day_context
        page_routes._get_prompt_entry = old_get_prompt_entry

def test_reflect_selected_prompt_overrides_default():
    app = make_app()
    client = app.test_client()
    login(client)

    old_day_context = page_routes._day_context
    old_get_prompt_entry = page_routes._get_prompt_entry

    try:
        page_routes._day_context = lambda username, selected_date: (
            "2026-04-18",
            {},
            "2026-04-17",
            "2026-04-19",
        )
        page_routes._get_prompt_entry = lambda day_doc: (None, None)

        response = client.get(
            "/reflect?date=2026-04-18&prompt=What%20challenged%20you%20today%3F"
        )
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "'current_prompt': 'What challenged you today?'" in text
    finally:
        page_routes._day_context = old_day_context
        page_routes._get_prompt_entry = old_get_prompt_entry

def test_history_shows_saved_count():
    app = make_app()
    client = app.test_client()
    login(client)

    old_get_day_document = page_routes._get_day_document

    try:
        page_routes._get_day_document = lambda username, selected_date: {
            "journal_entries": [
                {"transcript": "one"},
                {"transcript": "two"},
            ]
        }

        response = client.get("/history/2026-04-18")
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "'saved_count': 2" in text
        assert "'date': '2026-04-18'" in text
    finally:
        page_routes._get_day_document = old_get_day_document

def test_create_entry_page_with_timestamp():
    app = make_app()
    client = app.test_client()
    login(client)

    captured = {}
    old_create_entry = page_routes.create_entry

    try:
        def fake_create_entry(username, entry_date, entry_data):
            captured["username"] = username
            captured["entry_date"] = entry_date
            captured["entry_data"] = entry_data

        page_routes.create_entry = fake_create_entry

        response = client.post(
            "/entries/new",
            data={
                "date": "2026-04-18",
                "transcript": "hello world",
                "entry_type": "prompt",
                "prompt_text": "What challenged you today?",
                "mood_score": "6",
                "stress_score": "3",
                "timestamp": "10:30",
            },
        )

        assert response.status_code == 302
        assert captured["username"] == "lan"
        assert captured["entry_date"] == "2026-04-18"
        assert captured["entry_data"]["transcript"] == "hello world"
        assert captured["entry_data"]["entry_type"] == "prompt"
        assert captured["entry_data"]["timestamp"] == "10:30"
    finally:
        page_routes.create_entry = old_create_entry

def test_create_entry_page_without_timestamp():
    app = make_app()
    client = app.test_client()
    login(client)

    captured = {}
    old_create_entry = page_routes.create_entry

    try:
        def fake_create_entry(username, entry_date, entry_data):
            captured["entry_data"] = entry_data

        page_routes.create_entry = fake_create_entry

        response = client.post(
            "/entries/new",
            data={
                "date": "2026-04-18",
                "transcript": "journal text",
                "entry_type": "journal",
            },
        )

        assert response.status_code == 302
        assert "timestamp" not in captured["entry_data"]
        assert captured["entry_data"]["entry_type"] == "journal"
    finally:
        page_routes.create_entry = old_create_entry

def test_update_entry_page_with_timestamp():
    app = make_app()
    client = app.test_client()
    login(client)

    captured = {}
    old_update_entry = page_routes.update_entry

    try:
        def fake_update_entry(username, entry_date, entry_index, updated_data):
            captured["username"] = username
            captured["entry_date"] = entry_date
            captured["entry_index"] = entry_index
            captured["updated_data"] = updated_data

        page_routes.update_entry = fake_update_entry

        response = client.post(
            "/entries/2026-04-18/1/edit",
            data={
                "transcript": "edited text",
                "entry_type": "prompt",
                "prompt_text": "What stayed with you most today?",
                "mood_score": "8",
                "stress_score": "2",
                "timestamp": "11:45",
            },
        )

        assert response.status_code == 302
        assert captured["entry_index"] == 1
        assert captured["updated_data"]["timestamp"] == "11:45"
        assert captured["updated_data"]["transcript"] == "edited text"
    finally:
        page_routes.update_entry = old_update_entry

def test_create_task_page_with_deadline_calls_add_task():
    app = make_app()
    client = app.test_client()
    login(client)

    captured = {}

    old_add_task = page_routes.add_task

    try:
        def fake_add_task(username, entry_date, task_data):
            captured["username"] = username
            captured["entry_date"] = entry_date
            captured["task_data"] = task_data

        page_routes.add_task = fake_add_task

        response = client.post(
            "/tasks/new",
            data={
                "date": "2026-04-18",
                "title": "Eat",
                "deadline": "09:00",
            },
        )

        assert response.status_code == 302
        assert captured["username"] == "lan"
        assert captured["entry_date"] == "2026-04-18"
        assert captured["task_data"] == {
            "title": "Eat",
            "completed": False,
            "deadline": "09:00",
        }
    finally:
        page_routes.add_task = old_add_task


def test_create_task_page_blank_title_skips_add_task():
    app = make_app()
    client = app.test_client()
    login(client)

    called = {"add_task": False}
    old_add_task = page_routes.add_task

    try:
        def fake_add_task(username, entry_date, task_data):
            called["add_task"] = True

        page_routes.add_task = fake_add_task

        response = client.post(
            "/tasks/new",
            data={
                "date": "2026-04-18",
                "title": "   ",
                "deadline": "",
            },
        )

        assert response.status_code == 302
        assert called["add_task"] is False
    finally:
        page_routes.add_task = old_add_task


def test_update_task_page_blank_title_becomes_untitled_and_completed_true():
    app = make_app()
    client = app.test_client()
    login(client)

    captured = {}
    old_edit_task = page_routes.edit_task

    try:
        def fake_edit_task(username, entry_date, task_index, updated_task):
            captured["username"] = username
            captured["entry_date"] = entry_date
            captured["task_index"] = task_index
            captured["updated_task"] = updated_task

        page_routes.edit_task = fake_edit_task

        response = client.post(
            "/tasks/2026-04-18/0/edit",
            data={
                "title": "   ",
                "completed": "on",
            },
        )

        assert response.status_code == 302
        assert captured["updated_task"] == {
            "title": "Untitled task",
            "completed": True,
        }
    finally:
        page_routes.edit_task = old_edit_task


def test_toggle_task_page_valid_index_toggles_completed():
    app = make_app()
    client = app.test_client()
    login(client)

    captured = {}
    old_get_day_document = page_routes._get_day_document
    old_edit_task = page_routes.edit_task

    try:
        page_routes._get_day_document = lambda username, entry_date: {
            "tasks": [
                {"title": "Read", "completed": False}
            ]
        }

        def fake_edit_task(username, entry_date, task_index, updated_task):
            captured["updated_task"] = updated_task

        page_routes.edit_task = fake_edit_task

        response = client.post("/tasks/2026-04-18/0/toggle")

        assert response.status_code == 302
        assert captured["updated_task"]["title"] == "Read"
        assert captured["updated_task"]["completed"] is True
    finally:
        page_routes._get_day_document = old_get_day_document
        page_routes.edit_task = old_edit_task


def test_toggle_task_page_invalid_index_does_not_call_edit():
    app = make_app()
    client = app.test_client()
    login(client)

    called = {"edit_task": False}
    old_get_day_document = page_routes._get_day_document
    old_edit_task = page_routes.edit_task

    try:
        page_routes._get_day_document = lambda username, entry_date: {
            "tasks": []
        }

        def fake_edit_task(username, entry_date, task_index, updated_task):
            called["edit_task"] = True

        page_routes.edit_task = fake_edit_task

        response = client.post("/tasks/2026-04-18/0/toggle")

        assert response.status_code == 302
        assert called["edit_task"] is False
    finally:
        page_routes._get_day_document = old_get_day_document
        page_routes.edit_task = old_edit_task


def test_delete_task_page_calls_delete_task():
    app = make_app()
    client = app.test_client()
    login(client)

    captured = {}
    old_delete_task = page_routes.delete_task

    try:
        def fake_delete_task(username, entry_date, task_index):
            captured["username"] = username
            captured["entry_date"] = entry_date
            captured["task_index"] = task_index

        page_routes.delete_task = fake_delete_task

        response = client.post("/tasks/2026-04-18/2/delete")

        assert response.status_code == 302
        assert captured == {
            "username": "lan",
            "entry_date": "2026-04-18",
            "task_index": 2,
        }
    finally:
        page_routes.delete_task = old_delete_task