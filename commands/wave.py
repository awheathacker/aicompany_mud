"""
Wave command — send a quick non-verbal gesture to nearby characters.

Usage:
  wave
  wave <target>
  wave <message>
  w

Examples:
  wave
  wave Elara
  wave goodbye

Features:
- Broadcasts a brief gesture to all characters in the room
- Can target a specific character by name
- Optional message for a personalized gesture
- Shows the gesture to both the waver and recipients

Aliases: w
Help category: Social
"""

from evennia import Command


class CmdWave(Command):
    """
    Wave to characters in the room, or send a quick gesture.

    Usage:
      wave
      wave <target>
      wave <message>

    Without arguments, you give a simple wave to everyone in the room.
    With a target name, you gesture specifically to that character.
    With a message, you add context to your gesture.

    Examples:
      wave        — You wave to the room.
      wave Elara  — You wave at Elara.
      wave hello  — You wave, "Hello!"
      wave goodbye — You wave a silent goodbye.
    """

    key = "wave"
    aliases = ["w", "gesture", "gest"]
    locks = "cmd:all()"
    help_category = "Social"

    def func(self):
        caller = self.caller
        room = caller.location

        if not room:
            caller.msg("You're nowhere — nothing to wave at.")
            return

        args = (self.args or "").strip()

        # Find other characters in the room
        others = [
            obj for obj in room.contents
            if obj is not caller
            and hasattr(obj, "is_character") and obj.is_character
        ]

        if args:
            # Check if the argument is a character name in the room
            target = None
            for obj in others:
                if obj.key.lower() == args.lower():
                    target = obj
                    break

            if target:
                # Targeted wave
                caller.msg(f"You wave at {target.name}.")
                target.msg(
                    f"\x1b[36m{caller.name} waves at you.\x1b[0m"
                )

                # Notify the room's LLM context
                if hasattr(room, "handle_speech"):
                    try:
                        room.handle_speech(
                            caller,
                            f"[waves at {target.name}]"
                        )
                    except Exception:
                        pass
            else:
                # Treat as a message - wave with a message to everyone
                msg = args
                caller.msg(f"You wave, \"{msg}\"")
                for target in others:
                    target.msg(
                        f"\x1b[36m{caller.name} waves: \"{msg}\"\x1b[0m"
                    )

                # Notify the room's LLM context
                if hasattr(room, "handle_speech"):
                    try:
                        room.handle_speech(
                            caller,
                            f"[waves and says: {msg}]"
                        )
                    except Exception:
                        pass
        else:
            # Simple wave to everyone in the room
            if others:
                caller.msg("You wave to the room.")
                for target in others:
                    target.msg(
                        f"\x1b[36m{caller.name} waves.\x1b[0m"
                    )
            else:
                caller.msg("You wave at the empty room.")

            # Notify the room's LLM context
            if hasattr(room, "handle_speech"):
                try:
                    room.handle_speech(
                        caller,
                        "[waves]"
                    )
                except Exception:
                    pass
