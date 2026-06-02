"""
commands/trail.py

Trail command: tracks recent room visits and lets players retrace their steps.

Usage:
  trail              Show recent rooms visited
  trail list         Same as plain trail
  trail back         Go back one room
  trail back 3       Go back 3 rooms
  trail 2            Teleport to room #2 in the trail

This is the in-game equivalent of "breadcrumbs" — a simple way to navigate
without relying on `dig` to create named exits.
"""

from evennia import Command


class CmdTrail(Command):
    """
    Track and retrace your recent path through rooms.

    Usage:
      trail          — show recent rooms
      trail list     — same as `trail`
      trail back [N] — go back N steps (default 1)
      trail <N>      — jump to room at position N in the trail (1-based)

    The trail records every room you enter (max 20). Duplicate consecutive
    rooms are collapsed so the list stays readable.
    """
    key = "trail"
    aliases = ["breadcrumbs", "path", "retrace"]
    help_category = "Navigation"
    locks = "cmd:all()"

    TRAIL_MAX = 20

    def _get_trail(self):
        """Return the list of recent room dbrefs from the character's ndb."""
        trail = getattr(self.caller.ndb, "trail", [])
        return trail

    def _set_trail(self, trail):
        self.caller.ndb.trail = trail

    def _record_room(self):
        """
        Append the current room to the trail (delegated by at_room_change hook).
        This method is called via the Character's at_object_leave/receive cycle
        through the room-change tracker.
        """
        room = self.caller.location
        if not room:
            return
        trail = self._get_trail()
        # Collapse consecutive duplicates
        if trail and trail[-1] == room.dbref:
            return
        trail.append(room.dbref)
        self._set_trail(trail[-self.TRAIL_MAX:])

    def _format_trail(self):
        """Return a formatted string of the current trail."""
        trail = self._get_trail()
        if not trail:
            return "Your trail is empty — you haven't moved yet."

        lines = ["|wYour trail:|n"]
        current = self.caller.location
        current_dbref = current.dbref if current else None

        for i, ref in enumerate(trail, 1):
            room = self.caller.search(f"#{ref}")
            if isinstance(room, list):
                room = room[0] if room else None
            name = room.key if room else f"Room #{ref}"
            marker = " |r<-- you are here|n" if ref == current_dbref else ""
            lines.append(f"  |y{i}.|n {name} (#{ref}){marker}")

        return "\n".join(lines)

    def _navigate_to_dbref(self, dbref):
        """Move the caller to the room with the given dbref."""
        target = self.caller.search(f"#{dbref}")
        if isinstance(target, list):
            target = target[0] if target else None

        if target:
            self.caller.msg(f"You step back to {target.key}.")
            self.caller.move_to(target)
            # Record the jump in the trail
            trail = self._get_trail()
            if not trail or trail[-1] != target.dbref:
                trail.append(target.dbref)
                self._set_trail(trail[-self.TRAIL_MAX:])
            return True
        else:
            self.caller.msg(f"Room #{dbref} no longer exists.")
            return False

    def func(self):
        args = (self.args or "").strip().split()
        if not args:
            # Show trail
            self.caller.msg(self._format_trail())
            # Also record current room
            self._record_room()
            return

        subcmd = args[0].lower()

        if subcmd in ("list", "show"):
            self.caller.msg(self._format_trail())
            self._record_room()
            return

        if subcmd == "back":
            trail = self._get_trail()
            if not trail:
                self.caller.msg("Your trail is empty.")
                self._record_room()
                return

            steps = 1
            if len(args) > 1:
                try:
                    steps = int(args[1])
                except ValueError:
                    self.caller.msg(f"Usage: trail back [N]")
                    return
                if steps < 1:
                    self.caller.msg("Trail back needs a positive integer.")
                    return

            # The last entry is the current room; go back `steps` from there.
            idx = len(trail) - steps
            if idx < 0:
                # Go as far back as possible
                idx = 0
            target_dbref = trail[idx]
            self._navigate_to_dbref(target_dbref)
            self._record_room()
            return

        # Try to interpret as a direct index (1-based position in trail)
        try:
            idx = int(subcmd)
        except ValueError:
            self.caller.msg(
                f"Unknown subcommand '{subcmd}'.\n"
                "Usage: trail  |  trail list  |  trail back [N]  |  trail <N>"
            )
            self._record_room()
            return

        if idx < 1:
            self.caller.msg("Trail positions are 1-based.")
            self._record_room()
            return

        trail = self._get_trail()
        # Convert 1-based index to 0-based
        pos = idx - 1
        if pos >= len(trail):
            self.caller.msg(f"Trail only has {len(trail)} entries. Use 'trail list' to see them.")
            self._record_room()
            return

        target_dbref = trail[pos]
        self._navigate_to_dbref(target_dbref)
        self._record_room()
