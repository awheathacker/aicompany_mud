"""
Drop command — leave an object in your current room.

Usage:
  drop <object_name>
  lay <object_name>
  place <object_name>

Examples:
  drop lamp
  lay key
  place rusty sword

Features:
- Drop objects from your inventory back into the room
- Descriptive drop messages
- Notifies other characters in the room
- Integrates with room speech buffer for LLM context

Help category: Inventory
"""

from evennia import Command


class CmdDrop(Command):
    """
    Drop an object from your inventory into the current room.

    Usage:
      drop <object_name>
      lay <object_name>
      place <object_name>

    Sets down an item you're carrying and leaves it in the room.
    """

    key = "drop"
    aliases = ["lay", "place"]
    locks = "cmd:all()"
    help_category = "Inventory"

    def func(self):
        caller = self.caller
        room = caller.location
        args = self.args.strip()

        if not args:
            caller.msg("Drop what? Name the item you want to set down.\nUsage: drop <object_name>")
            return

        if not room:
            caller.msg("You're nowhere — hard to drop anything without a room.")
            return

        # Look for the item in the caller's inventory
        in_pack = caller.inventory_get(args, multiple=False)
        if not in_pack:
            caller.msg(f"You check your pack but don't seem to have a '{args}'.")
            return

        # Drop it — move from caller's inventory to the room
        in_pack.location = room

        caller.msg(f"You set down {in_pack.name} in the room.")

        # Notify others in the room
        others = [
            obj for obj in room.contents
            if obj is not caller
            and hasattr(obj, "is_character") and obj.is_character
        ]
        for other in others:
            other.msg(f"\x1b[33m{caller.name} drops {in_pack.name}.\x1b[0m")

        # Notify the room's LLM context
        if hasattr(room, "handle_speech"):
            try:
                room.handle_speech(caller, f"[{caller.name} drops {in_pack.name}]")
            except Exception:
                pass
