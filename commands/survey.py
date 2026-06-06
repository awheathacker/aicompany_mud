"""
Survey command

Usage: survey

Displays a structured overview of the current room including:
- Room name and description
- Visible exits with destinations
- Notable objects/furnishings
- Characters present
- Ambient mood (if set)

This is a quick-scanning alternative to `look` that prioritizes
structure and brevity over prose.
"""

from evennia import Command


class CmdSurvey(Command):
    """
    Survey the current room for a structured overview.

    Usage:
      survey

    Shows a concise summary of the room: exits, objects, occupants,
    and any ambient details — ideal for quick situational awareness
    without reading the full description.

    Example:
      > survey
      |nThe Grand Atrium|n
      A vast open space with light streaming through stained glass.

      Exits: north (Library), south (Garden), east (Corridor)
      Objects: a brass fountain, a cracked hourglass
      Characters: Elara, Thorned Sentinel
    """
    key = "survey"
    aliases = ["overview", "scan"]
    locks = "cmd:all()"
    help_category = "Movement"

    def func(self):
        caller = self.caller
        room = caller.location

        if not room:
            caller.msg("You are standing in nowhere.")
            return

        # --- Room name + short description ---
        room_name = room.key
        desc = room.db.desc or room.long_description or ""
        # Truncate description to one line
        if "\n" in desc:
            desc = desc.split("\n", 1)[0]
        if len(desc) > 120:
            desc = desc[:117] + "..."
        caller.msg(f"|y{room_name}|n")
        caller.msg(f"{desc}\n")

        # --- Exits ---
        exits = [ex for ex in room.exits if not ex.hidden]
        if exits:
            exit_parts = []
            for ex in exits:
                dest = ex.destination
                dest_name = dest.key if dest else "??"
                exit_parts.append(f"{ex.key} ({dest_name})")
            caller.msg(f"|WExits:|n {', '.join(exit_parts)}")
        else:
            caller.msg("|WExits:|n (none visible)")

        # --- Notable objects ---
        objects = [
            obj for obj in room.contents
            if obj is not caller
            and not obj.exit_typeclass
            and not obj.char_typeclass
        ]
        if objects:
            obj_names = []
            for obj in objects:
                # Prefer shortdesc, then key
                name = obj.db.shortdesc or obj.key or "?"
                if len(name) > 40:
                    name = name[:37] + "..."
                obj_names.append(name)
            caller.msg(f"|WObjects:|n {', '.join(obj_names)}")
        else:
            caller.msg("|WObjects:|n (nothing stands out)")

        # --- Characters ---
        chars = [
            obj for obj in room.contents
            if obj.char_typeclass
            and obj is not caller
        ]
        if chars:
            char_names = [c.key for c in chars]
            caller.msg(f"|WCharacters:|n {', '.join(char_names)}")
        else:
            caller.msg("|WCharacters:|n (you are alone)")
