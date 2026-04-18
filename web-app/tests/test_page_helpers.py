'''
testiing page helper functions
'''
from datetime import date 
import routes.page_routes as page_routes

def test_parse_date_valid():
    result = page_routes.parse_date("2026-04-18")
    assert result.isoformat() == "2026-04-18"

def test_parse_date_invalid_returns_today():
    result = page_routes.parse_date("invalid-date")
    assert isinstance(result, date)

def test_get_journal_entries_returns_entries_from_day_doc():
    day_doc = {
        "journal_entries": [
            {"entry_type": "journal", "transcript": "Entry 1"},
            {"entry_type": "prompt", "transcript": "Entry 2"},
        ]
    }

    result = page_routes._get_journal_entries(day_doc)

    assert len(result) == 2
    assert result[0]["transcript"] == "Entry 1"
    assert result[1]["transcript"] == "Entry 2"

def test_get_journal_entries_returns_empty_list_for_bad_input():
    result = page_routes._get_journal_entries(None)
    assert result == []

def test_get_prompt_entry_returns_latest_prompt_entry():
    day_doc = {
        "journal_entries": [
            {"entry_type": "journal", "transcript": "Normal entry"},
            {"entry_type": "prompt", "prompt_text": "Old prompt"},
            {"entry_type": "prompt", "prompt_text": "Newest prompt"},
        ]
    }
    idx, entry = page_routes._get_prompt_entry(day_doc)

    assert idx == 2
    assert entry["prompt_text"] == "Newest prompt"

def test_get_prompt_entry_returns_none_when_no_prompt_exists():
    day_doc = {
        "journal_entries": [
            {"entry_type": "journal", "transcript": "Only normal entry"}
        ]
    }

    idx, entry = page_routes._get_prompt_entry(day_doc)

    assert idx is None
    assert entry is None

def test_get_prompt_entry_returns_none_when_no_prompt_exists():
    day_doc = {
        "journal_entries": [
            {"entry_type": "journal", "transcript": "Only normal entry"}
        ]
    }

    idx, entry = page_routes._get_prompt_entry(day_doc)

    assert idx is None
    assert entry is None

def test_build_prompt_choices_excludes_current_prompt():
    current = page_routes.PROMPTS[0]

    result = page_routes._build_prompt_choices(current)

    assert current not in result
    assert len(result) <= 3

def test_get_current_week_returns_seven_days():
    result = page_routes._get_current_week("2026-04-15")

    assert len(result) == 7
    assert all("date" in day for day in result)
    assert all("dow" in day for day in result)
    assert all("num" in day for day in result)


def test_get_current_week_marks_selected_day_active():
    result = page_routes._get_current_week("2026-04-15")

    active_days = [day for day in result if day["active"]]

    assert len(active_days) == 1
    assert active_days[0]["date"] == "2026-04-15"

def test_day_context_returns_prev_and_next_dates():
    normalized_date, _, prev_date, next_date = page_routes._day_context(
        "lan", "2026-04-15"
    )

    assert normalized_date == "2026-04-15"
    assert prev_date == "2026-04-14"
    assert next_date == "2026-04-16"

def test_format_time_converts_to_12_hour_clock():
    result = page_routes.format_time("14:30")
    assert result == "2:30 PM"


def test_format_time_returns_none_for_empty_input():
    result = page_routes.format_time(None)
    assert result is None
