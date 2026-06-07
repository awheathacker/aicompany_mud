"""
Mark command: let players bookmark rooms as points of interest.

Usage:
  mark              — list all marked rooms
  mark <name>       — mark the current room with a name
  mark <name> unmark — remove a mark
  mark <name> note — view note for a mark
  mark <name> note <text> — update note for a mark
"""

from evennia import Command


class CmdMark(Command):
    """
    Bookmark rooms as points of interest.

    Usage:
      mark                  — list all marked rooms
      mark <name>          — mark current room
      mark <name> unmark   — remove a mark
      mark <name> note     — view note
      mark <name> note <text> — update note

    Examples:
      mark tavern
      mark tavern note Best ale in the realm
      mark tavern unmark
      mark
    """
    key = "mark"
    aliases = ["bookmark", "marker"]
    locks = "cmd:all()"
    help_category = "Navigation"

    def _get_marks(self):
        """Get the caller's mark dictionary from db property."""
        marks = self.caller.db.marked_rooms
        if marks is None:
            self.caller.db.marked_rooms = {}
            marks = self.caller.db.marked_rooms
        return marks

    def _get_room_id(self, room):
        """Get a stable ID for a room (dbref)."""
        if room:
            return room.dbid
        return None

    def func(self):
        caller = self.caller
        args = (self.args or "").strip()
        marks = self._get_marks()

        if not args:
            # No args: list all marks
            if not marks:
                caller.msg("You have no marked rooms.")
                caller.msg("Use |wmark <name>|n to bookmark the current room.")
                return

            caller.msg("Your marked rooms:")
            caller.msg("")
            for name, data in sorted(marks.items()):
                note = data.get("note", "")
                note_str = f" — {note}" if note else ""
                caller.msg(f"  |w{name}|n{note_str}")
            return

        parts = args.split()
        mark_name = parts[0].lower()
        subcmd = " ".join(parts[1:]) if len(parts) > 1 else ""

        if subcmd == "unmark":
            # Remove a mark
            if mark_name in marks:
                del marks[mark_name]
                caller.db.marked_rooms = marks
                caller.msg(f"Unmarked '{mark_name}'.")
            else:
                caller.msg(f"No mark named '{mark_name}'.")
            return

        if subcmd.startswith("note "):
            # Update note: mark <name> note <text>
            if mark_name in marks:
                marks[mark_name]["note"] = subcmd[5:]  # strip "note "
                caller.db.marked_rooms = marks
                caller.msg(f"Updated note for '{mark_name}'.")
            else:
                caller.msg(f"No mark named '{mark_name}' yet. Use |wmark {mark_name}|n first.")
            return

        if subcmd == "note":
            # View note
            if mark_name in marks:
                note = marks[mark_name].get("note", "No note.")
                caller.msg(f"{mark_name}: {note}")
            else:
                caller.msg(f"No mark named '{mark_name}'.")
            return

        # Default: create/update mark for current room
        room = caller.location
        if not room:
            caller.msg("You are nowhere — nothing to mark.")
            return

        room_id = self._get_room_id(room)
        marks[mark_name] = {
            "room_id": room_id,
            "room_name": room.key,
            "note": "",
        }
        caller.db.marked_rooms = marks
        caller.msg(f"Marked this room as '|w{mark_name}|n'.")
