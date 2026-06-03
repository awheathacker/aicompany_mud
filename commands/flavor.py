"""
commands/flavor.py

Flavor command: set a short status/appearance text displayed next to your
character name in the room.

Usage:
  flavor <text>          — set your flavor text
  flavor clear           — clear the current flavor text
  flavor (no args)       — show your current flavor text
  flavor <character>     — view another character's flavor text

This gives players a lightweight way to add personality and status
information to their character without changing their display name.
"""

from evennia import Command
from evennia.utils.search import search_object


class CmdFlavor(Command):
    """
    Set or view a short "flavor" text for your character.

    Usage:
      flavor <text>          — set your flavor text
      flavor clear           — clear the current flavor text
      flavor                  — show your current flavor text
      flavor <character>      — view another character's flavor text

    Examples:
      flavor The grizzled veteran of a thousand battles
      flavor Lost in thought...
      flavor clear
      flavor Elara

    Flavor text is stored as the character's `db.flavor_text` attribute
    and can be appended to room listings by the room's look output.
    """
    key = "flavor"
    aliases = ["flav", "status_text", "tag"]
    help_category = "Character"
    locks = "cmd:all()"

    MAX_LENGTH = 120

    def func(self):
        """Execute the flavor command."""
        caller = self.caller
        args = (self.args or "").strip()

        # No args: show current flavor
        if not args:
            current = getattr(caller.db, "flavor_text", "") or ""
            if current:
                caller.msg(f"|wYour flavor text:|n {current}")
            else:
                caller.msg("|nYou have no flavor text set. Use |wflavor <text>|n to set one.")
            return

        # Clear flavor
        if args.lower() == "clear":
            caller.db.flavor_text = ""
            caller.msg("|wFlavor text cleared.|n")
            return

        # Try to look up another character first
        target = search_object(args)
        if target and not isinstance(target, list):
            if not hasattr(target, "db"):
                target = [target]
        if target:
            if isinstance(target, list):
                target = target[0] if target else None
            if target:
                flavor_text = getattr(target.db, "flavor_text", "") or "None set"
                caller.msg(f"|w{target.key}'s flavor:|n {flavor_text}")
                return

        # Set flavor (treat the args as the flavor text)
        flavor_text = args[:self.MAX_LENGTH].strip()
        if len(args) > self.MAX_LENGTH:
            caller.msg(f"|yWarning:|n Flavor text was truncated to {self.MAX_LENGTH} characters.")
            flavor_text = flavor_text[:self.MAX_LENGTH]

        caller.db.flavor_text = flavor_text
        caller.msg(f"|wFlavor text set:|n {flavor_text}")
