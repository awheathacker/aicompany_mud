"""
Take command — pick up an object from your current room.

Usage:
  take <object_name>
  get <object_name>
  grab <object_name>

Examples:
  take lamp
  get key
  take rusty sword

Features:
- Pick up objects from the room into your inventory
- Re-lift an already-held object for a closer look
- Descriptive pickup messages
- Notifies other characters in the room
- Integrates with room speech buffer for LLM context

Help category: Inventory
"""

from evennia import Command


class CmdTake(Command):
    """
    Pick up an object from your current room.

    Usage:
      take <object_name>
      get <object_name>
      grab <object_name>

    Pick up an object lying in the room. If the object is already
    in your inventory, it is lifted back into your hands for a
    closer look.
    """

    key = "take"
    aliases = ["get", "grab"]
    locks = "cmd:all()"
    help_category = "Inventory"

    def func(self):
        caller = self.caller
        room = caller.location
        args = self.args.strip()

        if not args:
            caller.msg("Take what? Describe the object you want to pick up.\nUsage: take <object_name>")
            return

        if not room:
            caller.msg("You're nowhere — hard to take anything without a room.")
            return

        # Check if it's already in inventory (re-lift)
        in_pack = caller.inventory_get(args, multiple=False)
        if in_pack:
            caller.msg(f"You lift {in_pack.name} from your pack for a closer look.")
            return

        # Look for the object in the room
        target = room.objects_get(args, multiple=False)
        if not target:
            caller.msg(f"You look around, but don't see a '{args}' anywhere here.")
            return

        # Pick it up — move from room to caller's inventory
        target.location = caller

        caller.msg(f"You pick up {target.name}.")

        # Notify others in the room
        others = [
            obj for obj in room.contents
            if obj is not caller
            and hasattr(obj, "is_character") and obj.is_character
        ]
        for other in others:
            other.msg(f"\x1b[33m{caller.name} picks up {target.name}.\x1b[0m")

        # Notify the room's LLM context
        if hasattr(room, "handle_speech"):
            try:
                room.handle_speech(caller, f"[{caller.name} picks up {target.name}]")
            except Exception:
                pass
