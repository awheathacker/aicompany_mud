# tests/utils/test_room_object_query.py
from types import SimpleNamespace

import utils.room_object_query as roq


class FakeObj:
    def __init__(
        self,
        key: str,
        dbref: str,
        shortdesc: str = "",
        notable: bool = False,
        kind: str = "prop",  # "prop" | "exit" | "char"
    ):
        self.key = key
        self.dbref = dbref
        self.db = SimpleNamespace(shortdesc=shortdesc, notable=notable)
        self._kind = kind
        self.deleted = False

    def delete(self):
        self.deleted = True


class FakeRoom:
    def __init__(self, contents):
        self.contents = contents


def patch_inherits_from(monkeypatch):
    """
    room_object_query imports inherits_from at module import time, so we patch the module var.
    """
    def fake_inherits_from(obj, path: str) -> bool:
        if not obj:
            return False
        if path.endswith("DefaultExit"):
            return getattr(obj, "_kind", None) == "exit"
        if path.endswith("DefaultCharacter"):
            return getattr(obj, "_kind", None) == "char"
        return False

    monkeypatch.setattr(roq, "inherits_from", fake_inherits_from)


def test_iter_notable_props_filters_non_props(monkeypatch):
    patch_inherits_from(monkeypatch)

    p1 = FakeObj("Lamp", "#10", notable=True, kind="prop")
    p2 = FakeObj("Sofa", "#11", notable=False, kind="prop")
    ex = FakeObj("North", "#12", notable=True, kind="exit")
    ch = FakeObj("Bob", "#13", notable=True, kind="char")
    room = FakeRoom([p1, p2, ex, ch, None])

    got = list(roq.iter_notable_props(room))
    assert got == [p1]


def test_list_notables_with_dbref_formats_and_limits(monkeypatch):
    patch_inherits_from(monkeypatch)

    room = FakeRoom([
        FakeObj("A", "#1", notable=True),
        FakeObj("B", "#2", notable=True),
        FakeObj("C", "#3", notable=True),
    ])

    assert roq.list_notables_with_dbref(room, limit=2) == "A(#1), B(#2)"


def test_find_object_by_dbref_returns_any_kind(monkeypatch):
    patch_inherits_from(monkeypatch)

    ex = FakeObj("North", "#77", kind="exit")
    room = FakeRoom([ex])
    assert roq.find_object_in_room(room, "#77") is ex


def test_find_object_exact_match_key_case_insensitive(monkeypatch):
    patch_inherits_from(monkeypatch)

    lamp = FakeObj("Seafoam Brass Lamp", "#10", shortdesc="a brass lamp", notable=True)
    room = FakeRoom([lamp])

    assert roq.find_object_in_room(room, "seafoam brass lamp") is lamp
    assert roq.find_object_in_room(room, "SEAFOAM BRASS LAMP") is lamp


def test_find_object_exact_match_shortdesc(monkeypatch):
    patch_inherits_from(monkeypatch)

    lamp = FakeObj("Lamp", "#10", shortdesc="a brass lamp")
    room = FakeRoom([lamp])

    assert roq.find_object_in_room(room, "a brass lamp") is lamp


def test_find_object_unique_substring_match(monkeypatch):
    patch_inherits_from(monkeypatch)

    lamp = FakeObj("Seafoam Brass Lamp", "#10", shortdesc="a brass lamp")
    room = FakeRoom([lamp])

    assert roq.find_object_in_room(room, "seafoam") is lamp
    assert roq.find_object_in_room(room, "brass") is lamp


def test_find_object_ambiguous_substring_returns_none(monkeypatch):
    patch_inherits_from(monkeypatch)

    lamp1 = FakeObj("Seafoam Brass Lamp", "#10", shortdesc="a brass lamp")
    lamp2 = FakeObj("Brass Lamp", "#11", shortdesc="a brass lamp")
    room = FakeRoom([lamp1, lamp2])

    assert roq.find_object_in_room(room, "brass") is None


def test_find_object_notable_only_filters(monkeypatch):
    patch_inherits_from(monkeypatch)

    notable = FakeObj("Newspaper", "#20", notable=True)
    plain = FakeObj("Table", "#21", notable=False)
    room = FakeRoom([notable, plain])

    assert roq.find_object_in_room(room, "table", notable_only=True) is None
    assert roq.find_object_in_room(room, "newspaper", notable_only=True) is notable


def test_delete_by_dbref_deletes_any_kind(monkeypatch):
    patch_inherits_from(monkeypatch)

    ex = FakeObj("North", "#77", kind="exit")
    room = FakeRoom([ex])

    removed = roq.delete_object_by_selector(room, "#77")
    assert removed == {"key": "North", "dbref": "#77"}
    assert ex.deleted is True


def test_delete_by_exact_match_deletes_prop_only(monkeypatch):
    patch_inherits_from(monkeypatch)

    lamp = FakeObj("Lamp", "#10", shortdesc="a brass lamp", kind="prop")
    room = FakeRoom([lamp])

    removed = roq.delete_object_by_selector(room, "lamp")
    assert removed == {"key": "Lamp", "dbref": "#10"}
    assert lamp.deleted is True


def test_delete_by_unique_substring_deletes(monkeypatch):
    patch_inherits_from(monkeypatch)

    lamp = FakeObj("Seafoam Brass Lamp", "#10", shortdesc="a brass lamp", kind="prop")
    room = FakeRoom([lamp])

    removed = roq.delete_object_by_selector(room, "seafoam")
    assert removed == {"key": "Seafoam Brass Lamp", "dbref": "#10"}
    assert lamp.deleted is True


def test_delete_ambiguous_substring_returns_none(monkeypatch):
    patch_inherits_from(monkeypatch)

    lamp1 = FakeObj("Seafoam Brass Lamp", "#10", shortdesc="a brass lamp")
    lamp2 = FakeObj("Brass Lamp", "#11", shortdesc="a brass lamp")
    room = FakeRoom([lamp1, lamp2])

    removed = roq.delete_object_by_selector(room, "brass")
    assert removed is None
    assert lamp1.deleted is False
    assert lamp2.deleted is False


# --- Tests for iter_props (generic prop iterator) ---

def test_iter_props_yields_all_props(monkeypatch):
    patch_inherits_from(monkeypatch)

    p1 = FakeObj("Lamp", "#10", kind="prop")
    p2 = FakeObj("Sofa", "#11", kind="prop")
    ex = FakeObj("North", "#12", kind="exit")
    ch = FakeObj("Bob", "#13", kind="char")
    room = FakeRoom([p1, p2, ex, ch, None])

    got = list(roq.iter_props(room))
    assert got == [p1, p2]


def test_iter_props_empty_room(monkeypatch):
    patch_inherits_from(monkeypatch)

    room = FakeRoom([])
    got = list(roq.iter_props(room))
    assert got == []


def test_iter_props_filters_non_props(monkeypatch):
    patch_inherits_from(monkeypatch)

    ex = FakeObj("North", "#12", kind="exit")
    ch = FakeObj("Bob", "#13", kind="char")
    room = FakeRoom([ex, ch, None])

    got = list(roq.iter_props(room))
    assert got == []


# --- Tests for find_object_by_dbref ---

def test_find_object_by_dbref_finds_prop(monkeypatch):
    patch_inherits_from(monkeypatch)

    lamp = FakeObj("Lamp", "#10", kind="prop")
    sofa = FakeObj("Sofa", "#11", kind="prop")
    room = FakeRoom([lamp, sofa])

    assert roq.find_object_by_dbref(room, "#10") is lamp
    assert roq.find_object_by_dbref(room, "#11") is sofa


def test_find_object_by_dbref_finds_exit(monkeypatch):
    patch_inherits_from(monkeypatch)

    ex = FakeObj("North", "#77", kind="exit")
    room = FakeRoom([ex])

    assert roq.find_object_by_dbref(room, "#77") is ex


def test_find_object_by_dbref_returns_none(monkeypatch):
    patch_inherits_from(monkeypatch)

    lamp = FakeObj("Lamp", "#10", kind="prop")
    room = FakeRoom([lamp])

    assert roq.find_object_by_dbref(room, "#99") is None
    assert roq.find_object_by_dbref(room, "10") is None  # missing # prefix shouldn't match as dbref lookup


def test_find_object_by_dbref_empty_room(monkeypatch):
    patch_inherits_from(monkeypatch)

    room = FakeRoom([])
    assert roq.find_object_by_dbref(room, "#1") is None


# --- Tests for iter_notable_props uses iter_props internally ---

def test_iter_notable_props_is_subset_of_iter_props(monkeypatch):
    patch_inherits_from(monkeypatch)

    p1 = FakeObj("Lamp", "#10", notable=True, kind="prop")
    p2 = FakeObj("Sofa", "#11", notable=True, kind="prop")
    p3 = FakeObj("Cushion", "#12", notable=False, kind="prop")
    ex = FakeObj("North", "#13", kind="exit")
    room = FakeRoom([p1, p2, p3, ex, None])

    all_props = list(roq.iter_props(room))
    notables = list(roq.iter_notable_props(room))
    assert set(n for n in notables) == {p1, p2}
    assert all(n in all_props for n in notables)


def test_iter_props_and_notable_empty_contents(monkeypatch):
    patch_inherits_from(monkeypatch)

    room = FakeRoom(None)  # None contents (edge case)
    assert list(roq.iter_props(room)) == []
    assert list(roq.iter_notable_props(room)) == []

