"""
describe command — set your character's appearance description.

Usage:
  describe [text]
  describe (empty to show current)
  describe   (trailing whitespace = clear)

Sets a short, in-world description that other players see when they
`look` at you or when you enter a room.

Examples:
  describe A tall elf with silver hair and a leather satchel.
  describe          (show current)
"""
from commands.command import Command


class CmdDescribe(Command):
    """
    Set your character's appearance description.

    Usage:
      describe [text]
      describe        (show current)
      describe         (with trailing whitespace = clear)

    Sets a short, in-world description that other players see when they
    `look` at you or when you enter a room.
    """
    key = "describe"
    aliases = ["desc"]
    help_category = "Character"

    MAX_DESC_LEN = 240

    def func(self):
        caller = self.caller
        args = self.args

        # Trailing whitespace only = clear
        if args is not None and args.strip() == "":
            caller.db.describe_text = ""
            caller.msg("Description cleared.")
            return

        # No argument = show current
        if args is None or args.strip() == "":
            current = getattr(caller.db, "describe_text", None)
            if current:
                caller.msg(f"Your description: {current}")
            else:
                caller.msg("You have no description set. Try: describe A tall elf with silver hair.")
            return

        # Set the description
        text = args.strip()
        if len(text) > self.MAX_DESC_LEN:
            text = text[:self.MAX_DESC_LEN]
            caller.msg(f"(Description truncated to {self.MAX_DESC_LEN} characters.)")

        caller.db.describe_text = text
        caller.msg(f"Your description is now: {text}")
