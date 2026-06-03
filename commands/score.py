"""
commands/score.py

Score command: show your character's current stats.

Usage:
  score            — show your character's full scorecard
  stats            — same, shorter alias
"""

from evennia import Command


class CmdScore(Command):
    """
    Show your character's scorecard (stats).

    Usage:
      score
      stats

    Displays your character's name, location, and a summary of
    relevant attributes (health, inventory count, and any
    custom db-properties like title or level).
    """
    key = "score"
    aliases = ["stats", "charstats"]
    help_category = "Character"
    locks = "cmd:all()"

    def func(self):
        """Execute the score command."""
        caller = self.caller
        if not caller:
            return

        # Gather info
        name = caller.key
        location = caller.location
        loc_name = location.key if location else "Nowhere"

        # Inventory count
        if location:
            carried = [
                obj for obj in location.contents
                if obj is not caller
                and not hasattr(obj, "exits")
                and not obj.__class__.__name__ in ("Character", "DefaultCharacter")
            ]
            inv_count = len(carried)
        else:
            inv_count = 0

        # Custom attributes (common MUD stats)
        title = getattr(caller.db, "title", "Novice")
        level = getattr(caller.db, "level", 1)
        health = getattr(caller.db, "health", 100)
        max_health = getattr(caller.db, "max_health", 100)
        stamina = getattr(caller.db, "stamina", 50)
        max_stamina = getattr(caller.db, "max_stamina", 50)

        # Build output
        lines = [
            f"  ╔══════════════════════════════╗",
            f"  ║        Character Score       ║",
            f"  ╚══════════════════════════════╝",
            "",
            f"  Name:   {name}",
            f"  Title:  {title}",
            f"  Level:  {level}",
            f"  Health: {'█' * int(health / (max_health or 1) * 10)}{'░' * (10 - int(health / (max_health or 1) * 10))} {health}/{max_health}",
            f"  Stamina: {'█' * int(stamina / (max_stamina or 1) * 10)}{'░' * (10 - int(stamina / (max_stamina or 1) * 10))} {stamina}/{max_stamina}",
            f"  Carrying: {inv_count} item(s)",
            f"  Location: {loc_name}",
        ]

        # Show any extra custom db properties
        extras = []
        for prop in ("alignment", "class_name", "race", "age"):
            val = getattr(caller.db, prop, None)
            if val:
                extras.append(f"  {prop.replace('_', ' ').title()}: {val}")

        if extras:
            lines.append("")
            lines.extend(extras)

        caller.msg("\n".join(lines))
