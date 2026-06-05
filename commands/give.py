"""
Give command — hand an item to another character in the room.

Usage:
  give <item> to <character>
  give <character> <item>

Examples:
  give sword to Alice
  give Bob the golden key
  give letter to the guard

Features:
- Transfers a carried item from the caller to another character
- Supports flexible argument parsing (item-to-char or char-item)
- Shows animated give/receive messages to both parties
- Notifies other room occupants of the exchange
- Integrates with room speech buffer for LLM context
"""

from evennia import Command


class CmdGive(Command):
    """
    Give an item to another character in the room.

    Usage:
      give <item> to <character>
      give <character> <item>

    Transfers a carried object to another character in the current room.
    The item is removed from your inventory and added to the target's inventory.
    """

    key = "give"
    aliases = ["hand", "offer"]
    locks = "cmd:all()"
    help_category = "Inventory"

    def func(self):
        caller = self.caller
        room = caller.location

        if not room:
            caller.msg("You're floating in the void — no one to give things to.")
            return

        args = (self.args or "").strip()
        if not args:
            caller.msg("Usage: give <item> to <character>\nExample: give sword to Alice")
            return

        # Get other characters in the room (potential recipients)
        others = [
            obj for obj in room.contents
            if obj is not caller
            and hasattr(obj, "is_character") and obj.is_character
        ]

        if not others:
            caller.msg("You're alone here — no one to give anything to.")
            return

        # Parse the arguments: handle "item to character" or "character item"
        item_name, target = self._parse_give_args(args, others)

        if item_name is None or target is None:
            return

        # Find the item in the caller's inventory
        item = self._find_item(caller, item_name)
        if item is None:
            caller.msg(f"You don't seem to have a '{item_name}' on you.")
            return

        # Remove from caller, add to target
        item.move(destination=target, quiet=True)

        # Notify caller
        caller.msg(f"You give {item.key} to {target.name}.")

        # Notify target
        target.msg(f"{caller.name} gives you {item.key}.")

        # Notify other room occupants
        for occupant in room.contents:
            if occupant is not caller and occupant is not target:
                if hasattr(occupant, "is_character") and occupant.is_character:
                    occupant.msg(f"{caller.name} gives {item.key} to {target.name}.")

        # Notify the room's LLM context
        if hasattr(room, "handle_speech"):
            try:
                room.handle_speech(
                    caller,
                    f"[gives {item.key} to {target.name}]"
                )
            except Exception:
                pass

    def _parse_give_args(self, args, others):
        """
        Parse 'give' arguments into (item_name, target_character).
        Supports:
          "give sword to Alice"
          "give Alice sword"
        """
        # Try "item to character" format first
        if " to " in args:
            parts = args.split(" to ", 1)
            item_name = parts[0].strip()
            target_name = parts[1].strip()
            target = self._find_target_by_name(others, target_name)
            if target is None:
                caller = self.caller
                caller.msg(
                    f"Target not found. Characters in the room: "
                    f"{', '.join(o.name for o in others)}"
                )
            return (item_name, target)

        # Try "character item" format - first token is the character
        parts = args.split(None, 1)
        if len(parts) >= 2:
            first_word = parts[0].strip()
            rest = parts[1].strip()

            # Check if first word matches a character name
            target = self._find_target_by_name(others, first_word)
            if target is not None:
                return (rest, target)

            # First word might be an item, last word might be the character
            # Try parsing last word as target
            last_word = parts[-1].split()[-1]
            target = self._find_target_by_name(others, last_word)
            if target is not None:
                return (rest, target)

        # If nothing worked, list available characters
        caller = self.caller
        caller.msg(
            f"Usage: give <item> to <character>\n"
            f"Characters here: {', '.join(o.name for o in others)}"
        )
        return (None, None)

    def _find_target_by_name(self, others, name):
        """Find a character in the room by name (case-insensitive)."""
        low = name.lower()
        for obj in others:
            obj_name = getattr(obj, "name", obj.key)
            if obj_name:
                obj_name = str(obj_name)
            if obj_name.lower() == low or obj_name.lower().startswith(low):
                return obj
        return None

    def _find_item(self, caller, item_name):
        """Find an item in the caller's inventory by name."""
        low = item_name.lower()

        # Check direct children (items in the character's inventory)
        if hasattr(caller, "contents") or hasattr(caller, "children"):
            for child in getattr(caller, "children", []):
                name = getattr(child, "name", child.key)
                if name and str(name).lower() == low:
                    return child
                if name and str(name).lower().startswith(low):
                    return child

        # Fallback: check location's contents that caller carries
        if hasattr(caller, "locations"):
            for loc in caller.locations:
                if hasattr(loc, "contents"):
                    for obj in loc.contents:
                        name = getattr(obj, "name", obj.key)
                        if name and str(name).lower() == low:
                            return obj

        return None
