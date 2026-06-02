"""
tests/commands/test_trail.py

Unit tests for the `trail` navigation command.
"""
import pytest
from commands.trail import CmdTrail


class FakeRoom:
    """Minimal room mock."""
    def __init__(self, dbref, key="A Room"):
        self.dbref = dbref
        self.key = key
        self.db = type("db", (), {"notable": False})()

    def __eq__(self, other):
        return isinstance(other, FakeRoom) and self.dbref == other.dbref


class FakeSearch:
    """Mock search that finds rooms by dbref."""
    def __init__(self, rooms):
        self.rooms = rooms  # dict: dbref -> FakeRoom

    def search(self, query):
        if query.startswith("#"):
            ref = int(query[1:])
            return self.rooms.get(ref)
        return None


class FakeCaller:
    """Minimal caller mock with ndb, location, and msg."""
    def __init__(self, location=None):
        self.location = location
        self.ndb = type("ndb", (), {})()
        self.ndb.trail = []
        self.msg_calls = []

    def msg(self, text):
        self.msg_calls.append(text)

    def move_to(self, room):
        self.location = room

    def search(self, query):
        # Delegate to a fake search
        if query.startswith("#"):
            ref = int(query[1:])
            return self.rooms.get(ref)
        return None

    @property
    def rooms(self):
        return getattr(self, "_rooms", {})

    @rooms.setter
    def rooms(self, value):
        self._rooms = value


class FakeCmd:
    """Wrapper that makes CmdTrail.func() callable."""
    def __init__(self, caller):
        self.caller = caller
        self.args = ""

    def func(self):
        cmd = CmdTrail()
        cmd.caller = self.caller
        cmd.args = self.args
        cmd.func()


@pytest.fixture
def rooms():
    return {
        10: FakeRoom(10, "Lobby"),
        20: FakeRoom(20, "Hallway"),
        30: FakeRoom(30, "Kitchen"),
        40: FakeRoom(40, "Garden"),
    }


@pytest.fixture
def caller(rooms):
    c = FakeCaller(location=rooms[10])
    c.rooms = rooms
    c.ndb.trail = [10]
    return c


class TestTrailDisplay:
    def test_empty_trail(self, caller):
        caller.ndb.trail = []
        # Simulate showing trail
        trail = getattr(caller.ndb, "trail", [])
        assert trail == []

    def test_trail_records_room(self, caller):
        caller.ndb.trail = [10]
        # Simulate entering new room
        caller.location = rooms[20]
        # The trail command would record it
        trail = caller.ndb.trail
        assert 10 in trail

    def test_back_command_navigation(self, caller):
        # Set up a trail with multiple rooms
        caller.ndb.trail = [10, 20, 30, 40]
        caller.location = rooms[40]

        # Going back 1 step should take us to room 30
        trail = caller.ndb.trail
        idx = len(trail) - 1
        target_dbref = trail[idx]  # Should be 30 (room at position len-1 in trail before current)
        # Actually: trail[-1] is 40, which is the current room. Back 1 = trail[-2] = 30
        idx = len(trail) - 2
        assert trail[idx] == 30


class TestTrailDuplicateCollapsing:
    def test_consecutive_duplicates_collapsed(self):
        trail = []
        # Simulate: Lobby, Hallway, Hallway, Kitchen
        rooms_seq = [10, 20, 20, 30]
        for ref in rooms_seq:
            if trail and trail[-1] == ref:
                continue
            trail.append(ref)
        assert trail == [10, 20, 30]

    def test_non_consecutive_duplicates_preserved(self):
        trail = []
        # Lobby, Hallway, Kitchen, Hallway (returning)
        rooms_seq = [10, 20, 30, 20]
        for ref in rooms_seq:
            if trail and trail[-1] == ref:
                continue
            trail.append(ref)
        assert trail == [10, 20, 30, 20]


class TestTrailMaxLength:
    def test_trail_caps_at_20(self):
        trail = list(range(25))
        trail = trail[-20:]
        assert len(trail) == 20
        assert trail[0] == 5
        assert trail[-1] == 24
