"""
commands/search.py

Search command: find rooms, objects, or characters by keyword.

Usage:
  search <keyword>          — search all rooms by keyword
  search objects <keyword> — search objects in the current room
  search characters <type> — search characters globally
  search rooms <keyword>   — search rooms by keyword

Helps players find their way around or locate specific items and NPCs.
"""

from evennia import Command
from evennia.utils.search import search_objects, search_account


class CmdSearch(Command):
    """
    Search the game world for rooms, objects, or characters by keyword.

    Usage:
      search <keyword>           — search rooms by keyword in their name/description
      search objects <keyword>   — search objects in the current room
      search characters <keyword> — search characters globally
      search rooms <keyword>     — search rooms by keyword
      search all <keyword>       — search everything globally

    Examples:
      search kitchen
      search objects lamp
      search characters guard
      search all throne

    Shows matching results with location info to help navigation.
    """
    key = "search"
    aliases = ["find", "seek", "lookup"]
    help_category = "Navigation"
    locks = "cmd:all()"

    def _search_rooms(self, caller, keyword):
        """Search rooms by keyword in key or description."""
        kw = keyword.lower()
        all_rooms = search_objects("", category="room")
        matches = []
        for room in (all_rooms or []):
            rk = (getattr(room, "key", "") or "").lower()
            rd = (getattr(room, "db", None) and getattr(room.db, "desc", "") or "").lower()
            if kw in rk or kw in rd:
                occupants = []
                for c in (room.contents or []):
                    if c and hasattr(c, "key") and not hasattr(c, "exits"):
                        occupants.append(c.key)
                matches.append((room.key, room.dbref, occupants))

        if not matches:
            caller.msg(f"|nNo rooms matching '{keyword}'.|n")
            return

        caller.msg(f"|yRooms matching '{keyword}':|n")
        for name, dbref, occupants in matches[:20]:
            occ = f" ({len(occupants)} occupant{'s' if len(occupants) != 1 else ''})" if occupants else ""
            caller.msg(f"  {name} (#{dbref}){occ}")

    def _search_objects(self, caller, keyword):
        """Search for objects in the current room."""
        room = caller.location
        if not room:
            caller.msg("|nYou are nowhere to search from.|n")
            return

        kw = keyword.lower()
        matches = []
        for obj in (room.contents or []):
            if not obj:
                continue
            # Skip the caller themselves
            if obj.dbref == caller.dbref:
                continue
            # Skip exits
            if hasattr(obj, "destination") and getattr(obj, "destination", None) is not None:
                continue
            ok = (getattr(obj, "key", "") or "").lower()
            od = (getattr(obj, "db", None) and getattr(obj.db, "desc", "") or "").lower()
            osd = (getattr(obj, "db", None) and getattr(obj.db, "shortdesc", "") or "").lower()
            if kw in ok or kw in od or kw in osd:
                matches.append(obj.key)

        if not matches:
            caller.msg(f"|nNo objects matching '{keyword}' in this room.|n")
            return

        caller.msg(f"|yObjects in this room matching '{keyword}':|n")
        for name in matches:
            caller.msg(f"  {name}")

    def _search_characters(self, caller, keyword):
        """Search for characters globally."""
        kw = keyword.lower()
        all_chars = search_objects("", category="character")
        matches = []
        for char in (all_chars or []):
            ck = (getattr(char, "key", "") or "").lower()
            if kw in ck:
                loc = getattr(char, "location", None)
                loc_name = f"in {loc.key}" if loc else "nowhere"
                matches.append((char.key, loc_name))

        if not matches:
            caller.msg(f"|nNo characters matching '{keyword}'.|n")
            return

        caller.msg(f"|yCharacters matching '{keyword}':|n")
        for name, location in matches[:20]:
            caller.msg(f"  {name} — {location}")

    def _search_all(self, caller, keyword):
        """Search everything globally."""
        kw = keyword.lower()
        room_matches = []
        object_matches = []
        char_matches = []

        all_objs = search_objects("")
        for obj in (all_objs or []):
            ok = (getattr(obj, "key", "") or "").lower()
            if not obj or kw not in ok:
                continue

            # Classify
            if hasattr(obj, "exits") and not hasattr(obj, "destination"):
                # Room
                room_matches.append(obj.key)
            elif hasattr(obj, "destination") and getattr(obj, "destination", None) is not None:
                # Exit (skip)
                continue
            else:
                # Check if it's a character or object
                ck = getattr(obj, "__class__", lambda: None)
                if hasattr(obj, "account"):
                    char_matches.append(obj.key)
                else:
                    object_matches.append(obj.key)

        caller.msg(f"|ySearch results for '{keyword}':|n")
        if room_matches:
            caller.msg(f"  |wRooms:|n {', '.join(room_matches[:10])}")
        if object_matches:
            caller.msg(f"  |wObjects:|n {', '.join(object_matches[:10])}")
        if char_matches:
            caller.msg(f"  |wCharacters:|n {', '.join(char_matches[:10])}")

        if not room_matches and not object_matches and not char_matches:
            caller.msg("|nNo results found.|n")

    def func(self):
        """Execute the search command."""
        caller = self.caller
        args = (self.args or "").strip()

        if not args:
            caller.msg("Usage: search <keyword> | search objects <keyword> | search characters <keyword> | search all <keyword>")
            return

        parts = args.split(maxsplit=1)
        category = parts[0].lower()

        if category == "all":
            if len(parts) < 2 or not parts[1]:
                caller.msg("Usage: search all <keyword>")
                return
            self._search_all(caller, parts[1])
            return

        if category == "rooms" or category == "room":
            if len(parts) < 2 or not parts[1]:
                caller.msg("Usage: search rooms <keyword>")
                return
            self._search_rooms(caller, parts[1])
            return

        if category == "objects" or category == "object":
            if len(parts) < 2 or not parts[1]:
                caller.msg("Usage: search objects <keyword>")
                return
            self._search_objects(caller, parts[1])
            return

        if category == "characters" or category == "character" or category == "char":
            if len(parts) < 2 or not parts[1]:
                caller.msg("Usage: search characters <keyword>")
                return
            self._search_characters(caller, parts[1])
            return

        # Default: search rooms
        self._search_rooms(caller, args)
