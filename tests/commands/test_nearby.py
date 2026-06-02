"""
tests/commands/test_nearby.py

Unit tests for the `nearby` command.
"""
import pytest
from commands.nearby import CmdNearby


class FakeNotable:
    """Mock a notable object."""
    def __init__(self, key="Prop"):
        self.key = key
        self.db = type("db", (), {"notable": True, "shortdesc": ""})()


class FakeOccupant:
    """Mock a character (notable=False, has accounts attribute)."""
    def __init__(self, key="Player"):
        self.key = key
        self.db = type("db", (), {"notable": False})()
        self.accounts = type("accounts", (), {"all": lambda: []})()
        self.destination = None


class FakeExit:
    """Mock exit with destination."""
    def __init__(self, key="north", dest=None):
        self.key = key
        self.destination = dest


class FakeRoom:
    """Mock room with exits and contents."""
    def __init__(self, key="Room", dbref=1):
        self.key = key
        self.dbref = dbref
        self.exits = []
        self.contents = []


class FakeCaller:
    """Mock caller with location and msg."""
    def __init__(self, location=None):
        self.location = location
        self.msg_calls = []

    def msg(self, text):
        self.msg_calls.append(text)


class FakeCmd:
    """Wrapper to call CmdNearby.func()."""
    def __init__(self, caller):
        self.caller = caller
        self.args = ""

    def func(self):
        cmd = CmdNearby()
        cmd.caller = self.caller
        cmd.args = self.args
        cmd.func()


def test_nearby_no_exits():
    """When there are no exits, show 'No exits lead to other rooms.'"""
    room = FakeRoom()
    caller = FakeCaller(location=room)
    cmd = FakeCmd(caller)
    cmd.func()
    assert len(caller.msg_calls) == 1
    assert "No exits" in caller.msg_calls[0]


def test_nearby_single_exit():
    """When there is one exit, show it."""
    dest = FakeRoom(key="Kitchen", dbref=12)
    room = FakeRoom(key="Lobby", dbref=10)
    room.exits = [FakeExit(key="north", dest=dest)]
    caller = FakeCaller(location=room)
    cmd = FakeCmd(caller)
    cmd.func()
    assert len(caller.msg_calls) == 1
    output = caller.msg_calls[0]
    assert "north" in output
    assert "Kitchen" in output


def test_nearby_shows_notable_objects():
    """Notable objects in an adjacent room should appear in the brief view."""
    prop = FakeNotable(key="brass cat idol")
    prop.db.shortdesc = "a brass cat idol"
    dest = FakeRoom(key="Kitchen", dbref=12)
    dest.contents = [prop]
    room = FakeRoom(key="Lobby", dbref=10)
    room.exits = [FakeExit(key="north", dest=dest)]
    caller = FakeCaller(location=room)
    cmd = FakeCmd(caller)
    cmd.func()
    output = caller.msg_calls[0]
    assert "brass cat idol" in output


def test_nearby_shows_occupant_count():
    """Occupants in an adjacent room should show a count."""
    player = FakeOccupant(key="Alice")
    dest = FakeRoom(key="Hallway", dbref=8)
    dest.contents = [player]
    room = FakeRoom(key="Lobby", dbref=10)
    room.exits = [FakeExit(key="south", dest=dest)]
    caller = FakeCaller(location=room)
    cmd = FakeCmd(caller)
    cmd.func()
    output = caller.msg_calls[0]
    assert "1 occupant" in output


def test_nearby_detail_mode():
    """Detail mode should list occupants by name."""
    player = FakeOccupant(key="Alice")
    dest = FakeRoom(key="Hallway", dbref=8)
    dest.contents = [player]
    room = FakeRoom(key="Lobby", dbref=10)
    room.exits = [FakeExit(key="south", dest=dest)]
    caller = FakeCaller(location=room)
    cmd = FakeCmd(caller)
    cmd.args = "detail"
    cmd.func()
    output = caller.msg_calls[0]
    assert "Alice" in output
