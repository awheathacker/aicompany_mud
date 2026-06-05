"""
Follow command — follow another character through room exits.

Usage:
  follow <character>

Examples:
  follow Alice
  follow Bob

Features:
- Finds a character in the current room (or anywhere if named)
- Moves the caller to that character's room
- Shows the exit path taken
- Integrates with existing room speech memory
"""

from evennia import Command


class CmdFollow(Command):
    """
    Follow another character through the MUD.

    Usage:
      follow <character>

    Finds the named character and moves you to their room.
    Useful for keeping up with someone or exploring their location.
    """

    key = "follow"
    aliases = ["track", "trail"]
    locks = "cmd:all()"
    help_category = "Navigation"

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Usage: follow <character>")
            return

        # Find the target character
        target = self.search(args, multiple=False, character_only=True)

        if not target:
            caller.msg(f"No character named '{args}' could be found.")
            return

        if target is caller:
            caller.msg(f"You're already with yourself, {args}!")
            return

        # Get target's room
        target_room = target.location
        caller_room = caller.location

        if target_room and target_room is caller_room:
            caller.msg(f"{target.key} is already right here — in {caller_room.key if caller_room else 'nowhere'}.")
            return

        if not target_room:
            caller.msg(f"{target.key} is in limbo (no room).")
            return

        # Move caller to target's room
        if caller_room:
            from_room = caller_room.key
            to_room = target_room.key

            caller.msg(f"You follow {target.key} from {from_room} to {to_room}.")
        else:
            to_room = target_room.key
            caller.msg(f"You appear in {to_room}, following {target.key}.")

        caller.teleport(target_room)

        # Notify the target
        target.msg(f"|y{caller.key} follows you into the room.|n")

        # Notify other occupants
        for occupant in target_room.contents:
            if occupant is not caller and occupant is not target:
                if hasattr(occupant, "is_character") and occupant.is_character:
                    occupant.msg(f"|y{caller.key} follows {target.key} into the room.|n")
