"""
Wait command — pause in the room and observe.

Usage:
  wait
  wait <seconds>

Examples:
  wait
  wait 30

Features:
- Pauses for a short duration (default 10s, up to 60s)
- Shows the current room state and any recent speech
- Notifies other characters that you've paused to observe
- Integrates with room speech buffer for LLM context
"""

from evennia import Command


class CmdWait(Command):
    """
    Wait and observe your surroundings.

    Usage:
      wait
      wait <seconds>

    Stands still and pays attention. Useful for timing actions
    or catching room activity you might otherwise miss.
    """

    key = "wait"
    aliases = ["pause", "still"]
    locks = "cmd:all()"
    help_category = "Social"

    def func(self):
        caller = self.caller
        room = caller.location
        args = self.args.strip()

        # Determine wait duration (displayed, not blocking for the caller)
        if args:
            try:
                duration = max(1, min(60, int(args)))
            except ValueError:
                caller.msg(f"Invalid duration: '{args}'. Use a number 1–60.")
                return
        else:
            duration = 10

        # Show current room state
        if room:
            caller.msg(
                f"|wYou pause and observe the room — standing still for {duration} seconds.|n"
            )

            # Show other occupants
            occupants = [
                obj for obj in room.contents
                if hasattr(obj, "is_character") and obj.is_character
            ]
            others = [o for o in occupants if o is not caller]

            if others:
                names = ", ".join(
                    getattr(o, "name", o.key) for o in others
                )
                caller.msg(f"|yOccupants: {names}|n")

            # Show room name
            caller.msg(f"|gYou are in: {room.key}|n")

            # Show recent room memory if available
            if hasattr(room, "get_memory_text"):
                memory = room.get_memory_text()
                if memory:
                    caller.msg("|mRecent activity:|n")
                    for line in memory:
                        caller.msg(f"  {line}")
        else:
            caller.msg("|wYou close your eyes and wait in limbo...|n")
