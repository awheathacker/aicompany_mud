"""
Shout command — broadcast a message to everyone in the room (and optionally adjacent rooms).

Usage:
  shout <message>
  s <message>

Examples:
  shout Help! The dragon approaches!
  s Anyone heading to the tavern?

Features:
- Broadcasts a message to all other characters in the same room
- With the /area modifier, also reaches characters in adjacent rooms
- The shout appears styled for all listeners
- Integrates with room speech buffer for LLM context

Aliases: s
Help category: Social
"""

from evennia import Command


class CmdShout(Command):
    """
    Shout a message to everyone in the room.

    Usage:
      shout <message>
      s <message>

    With the /area modifier, your shout carries to adjacent rooms too:

      shout /area Help! The dragon approaches!

    Everyone in the room (and nearby, if /area) hears your shout.
    """

    key = "shout"
    aliases = ["s"]
    locks = "cmd:all()"
    help_category = "Social"

    def func(self):
        caller = self.caller
        room = caller.location

        if not room:
            caller.msg("You're nowhere — no one to shout to.")
            return

        args = (self.args or "").strip()
        if not args:
            caller.msg("Usage: shout <message>\nAdd /area to carry your voice to adjacent rooms:\n  shout /area Hello out there!")
            return

        # Check for /area modifier
        area = False
        if args.startswith("/area"):
            area = True
            args = args[5:].strip()

        if not args:
            caller.msg("You shout … and say nothing at all.")
            return

        # Send the shout to everyone else in the room
        others = [
            obj for obj in room.contents
            if obj is not caller
            and hasattr(obj, "is_character") and obj.is_character
        ]

        for target in others:
            target.msg(
                f"\x1b[93m{caller.name} shouts: {args}\x1b[0m"
            )

        # Confirmation to the shouter
        if others:
            caller.msg(f"You shout to the room: {args}")
        else:
            caller.msg(f"You shout into the emptiness: {args}")

        # Also shout to adjacent rooms if /area was used
        if area:
            self._shout_to_adjacent(caller, room, args)

        # Notify the room's LLM context about this social interaction
        area_note = " [shouted to the area]" if area else ""
        if hasattr(room, "handle_speech"):
            try:
                room.handle_speech(
                    caller,
                    f"[shouts{area_note}: {args}]"
                )
            except Exception:
                pass

    def _shout_to_adjacent(self, caller, room, message):
        """
        Send the shout to characters in adjacent rooms.
        Adjacency is determined by exits leading to neighboring rooms.
        """
        # Find adjacent rooms via exits
        visited = {room.id}
        adjacent_rooms = []

        for exit_obj in room.exits:
            destination = exit_obj.destination
            if destination and destination.id not in visited:
                visited.add(destination.id)
                adjacent_rooms.append(destination)

        for adj_room in adjacent_rooms:
            for obj in adj_room.contents:
                if obj is not caller and hasattr(obj, "is_character") and obj.is_character:
                    # Distant shout — slightly different styling
                    obj.msg(
                        f"\x1b[33m(from nearby, {caller.name} shouts): {message}\x1b[0m"
                    )
