# tests/commands/test_mood.py
"""
Tests for the Mood Command

Verifies that the mood command correctly sets, displays, and clears
the room mood attribute.
"""
import pytest
from commands.mood import CmdMood


class FakeDB:
    """Minimal db attribute container."""
    def __init__(self):
        self.mood = "eerie"


class FakeRoom:
    """Minimal room with a db attribute."""
    def __init__(self):
        self.db = FakeDB()


class FakeCaller:
    """Minimal caller with a location and message collector."""
    def __init__(self, room=None):
        self.location = room
        self._messages = []

    def msg(self, text):
        self._messages.append(text)

    def get_messages(self):
        return self._messages


@pytest.fixture
def caller_with_room():
    """Provide a FakeCaller standing in a FakeRoom."""
    room = FakeRoom()
    return FakeCaller(room)


@pytest.fixture
def caller_without_room():
    """Provide a FakeCaller with no location."""
    return FakeCaller(None)


def _make_cmd(caller):
    """Create a CmdMood instance with the given caller."""
    cmd = CmdMood()
    cmd.caller = caller
    cmd.args = ""
    return cmd


def test_show_mood_when_set(caller_with_room):
    """Show mood when room.db.mood exists."""
    cmd = _make_cmd(caller_with_room)
    cmd.func()
    msgs = caller_with_room.get_messages()
    assert len(msgs) == 1
    assert "eerie" in msgs[0]


def test_show_mood_when_blank(caller_with_room):
    """Show mood message when room has no mood set."""
    room = caller_with_room.location
    room.db.mood = ""
    cmd = _make_cmd(caller_with_room)
    cmd.func()
    msgs = caller_with_room.get_messages()
    assert len(msgs) == 1


def test_no_room(caller_without_room):
    """Calling mood when nowhere gives a message."""
    cmd = _make_cmd(caller_without_room)
    cmd.func()
    msgs = caller_without_room.get_messages()
    assert len(msgs) == 1


def test_set_mood_shorthand(caller_with_room):
    """Shorthand: mood <word> sets the mood."""
    room = caller_with_room.location
    cmd = _make_cmd(caller_with_room)
    cmd.args = "mysterious"
    cmd.func()
    assert room.db.mood == "mysterious"


def test_clear_mood(caller_with_room):
    """mood clear resets the mood attribute to empty."""
    room = caller_with_room.location
    cmd = _make_cmd(caller_with_room)
    cmd.args = "clear"
    cmd.func()
    assert room.db.mood == ""


def test_set_with_keyword(caller_with_room):
    """mood set <word> works via the 'set' keyword."""
    room = caller_with_room.location
    cmd = _make_cmd(caller_with_room)
    cmd.args = "set boisterous"
    cmd.func()
    assert room.db.mood == "boisterous"


def test_clear_when_already_blank(caller_with_room):
    """Clearing a blank mood reports it was already blank."""
    room = caller_with_room.location
    room.db.mood = ""
    cmd = _make_cmd(caller_with_room)
    cmd.args = "clear"
    cmd.func()
    msgs = caller_with_room.get_messages()
    assert len(msgs) == 1
