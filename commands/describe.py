"""
Describe command: set a short description of your character.

When other characters look at you, they see this description.
"""

from evennia import Command


class CmdDescribe(Command):
    """
    Set or view your short description.

    Usage:
      describe          (view your current description)
      describe <text>   (set a new description)

    This description is shown when other characters examine you.
    Type "describe" to see your current one.

    Examples:
      describe A tall orc with a battered axe
      describe A nervous accountant clutching a leather briefcase
      describe (view current)
    """
    key = "describe"
    aliases = ["desc"]
    locks = "cmd:all()"
    help_category = "Character"

    def func(self):
        caller = self.caller
        args = (self.args or "").strip()

        if not args:
            # No args: show current description
            desc = getattr(caller.db, "short_desc", "") or "No one in particular."
            caller.msg(f"Your short description: |w{desc}|n")
            return

        # Set new description
        if len(args) > 120:
            caller.msg(
                f"Description is a bit long ({len(args)} chars). Keep it under 120."
            )
            return

        caller.db.short_desc = args
        caller.msg(f"Your short description is now: |w{args}|n")

        # Announce to the room so others can see the change
        room = caller.location
        if room and hasattr(room, "db"):
            # Subtly announce without spamming
            for occupant in room.contents:
                if occupant != caller and hasattr(occupant, "msg"):
                    occupant.msg(
                        f"|n|y{caller.key} describes themselves: |w{args}|n"
                    )
