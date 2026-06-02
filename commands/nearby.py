"""
commands/nearby.py

Nearby command: shows adjacent rooms and a quick overview of their contents.

Usage:
  nearby              Show adjacent rooms with exit names
  nearby brief        Compact one-line summary (default)
  nearby detail       Show occupants and notable objects in each adjacent room

Helps players orient themselves in a larger world without entering every room.
"""

from evennia import Command


class CmdNearby(Command):
    """
    Show adjacent rooms connected by exits from your current location.

    Usage:
      nearby              — brief overview of adjacent rooms
      nearby brief        — same as plain nearby
      nearby detail       — include occupants and notable objects

    Example output (brief):
      |wNearby:|n
      north  → Kitchen (#12)
      south  → Hallway (#8) [2 occupants]
      east   → Garden (#15) [notable: brass cat idol]

    The detail mode expands each room to show who/what is there.
    """
    key = "nearby"
    aliases = ["around", "adjacent", "surroundings"]
    help_category = "Navigation"
    locks = "cmd:all()"

    def _get_adjacent(self):
        """
        Return list of (exit_key, destination_room) tuples for the current room.
        """
        room = self.caller.location
        if not room:
            return []

        adjacents = []
        for ex in room.exits:
            dest = getattr(ex, "destination", None)
            if dest:
                adjacents.append((ex.key or "unknown", dest))
        return adjacents

    def _get_notable_objects(self, room):
        """Return list of notable object shortdescs or keys in the room."""
        notables = []
        for obj in room.contents:
            if not obj:
                continue
            # Skip exits and the room itself
            if hasattr(obj, "destination"):
                continue
            if obj.db.notable:
                label = obj.db.shortdesc or obj.key
                notables.append(label)
        return notables

    def _get_occupants(self, room):
        """Return list of character keys in the room (excluding objects)."""
        occupants = []
        for obj in room.contents:
            if not obj:
                continue
            # Skip exits
            if hasattr(obj, "destination"):
                continue
            # Skip props (notable objects)
            if obj.db.notable:
                continue
            # Characters have a puppeted_by or accounts relationship
            if hasattr(obj, "accounts"):
                occupants.append(obj.key)
        return occupants

    def _format_brief(self):
        """Format the brief view of adjacent rooms."""
        adjacents = self._get_adjacents()
        if not adjacents:
            return "|yNo exits lead to other rooms.|n"

        lines = ["|wNearby:|n"]
        for exit_key, dest in adjacents:
            room_name = dest.key or "Unnamed Room"
            ref = dest.dbref
            notable = self._get_notable_objects(dest)
            occupants = self._get_occupants(dest)

            suffix = ""
            if occupants:
                suffix += f" [{len(occupants)} occupant{'' if len(occupants) == 1 else 's'}]"
            if notable:
                suffix += f" [notable: {', '.join(notable[:3])}]"
                if len(notable) > 3:
                    suffix += f" (+{len(notable) - 3} more)"

            lines.append(f"  |c{exit_key}|n → {room_name} ({ref}){suffix}")

        return "\n".join(lines)

    def _format_detail(self):
        """Format the detailed view with occupants and objects."""
        adjacents = self._get_adjacents()
        if not adjacents:
            return "|yNo exits lead to other rooms.|n"

        lines = ["|wNearby (detailed):|n"]
        for exit_key, dest in adjacents:
            room_name = dest.key or "Unnamed Room"
            ref = dest.dbref
            notable = self._get_notable_objects(dest)
            occupants = self._get_occupants(dest)

            lines.append(f"  |c{exit_key}|n → {room_name} ({ref})")
            if occupants:
                lines.append(f"    Occupants: {', '.join(occupants)}")
            if notable:
                lines.append(f"    Notable: {', '.join(notable)}")

        return "\n".join(lines)

    def func(self):
        """Execute the nearby command."""
        args = (self.args or "").strip().lower()

        if args == "detail":
            self.caller.msg(self._format_detail())
        else:
            self.caller.msg(self._format_brief())
