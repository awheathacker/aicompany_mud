# commands/compass.py
"""
Compass Command

Displays all exits from the current room in a clean, compass-style layout.
Helpful for quickly understanding where you can go without typing `look`.
"""
from evennia import Command


class CmdCompass(Command):
    """
    Show all exits from the current room.

    Displays a quick-reference list of every exit visible here,
    grouped by direction for easy scanning. Useful for navigation
    without the overhead of a full `look`.

    Usage:
      compass
      comp
      exits
    """
    key = "compass"
    aliases = ["comp", "exits"]
    locks = "cmd:all()"
    help_category = "World"

    DIRECTION_ORDER = ["north", "south", "east", "west", "up", "down"]

    def func(self):
        room = self.caller.location
        if not room:
            self.caller.msg("You are nowhere — no exits to map.")
            return

        exits = [ex for ex in room.exits
                 if ex.destination is not None]

        if not exits:
            self.caller.msg("You see no exits here. It feels like a dead end.")
            return

        # Group exits by direction vs. named exits
        directional = []
        named = []

        for ex in exits:
            key_lower = (ex.key or "").lower().strip()
            all_keys = [key_lower]
            for alias in ex.aliases.all():
                all_keys.append(alias.lower().strip())

            if any(d in all_keys for d in self.DIRECTION_ORDER):
                directional.append(ex)
            else:
                named.append(ex)

        # Sort directional exits by canonical order
        def _dir_sort_key(ex):
            key_lower = (ex.key or "").lower().strip()
            alias_list = [alias.lower().strip() for alias in ex.aliases.all()]
            for d in self.DIRECTION_ORDER:
                if key_lower == d or d in alias_list:
                    return self.DIRECTION_ORDER.index(d)
            return 99

        directional.sort(key=_dir_sort_key)

        # Build output
        lines = []
        lines.append("|w— Exits from here —|n")

        # Directional exits with short display
        if directional:
            for ex in directional:
                dest = ex.destination
                dest_name = dest.key if dest else "nowhere"
                # Show the shortest alias (e.g., "n" instead of "north")
                display = self._shortest_exit_label(ex)
                lines.append(f"  {display:10} → {dest_name}")

        # Named exits (non-directional)
        if named:
            if directional:
                lines.append("")  # spacer
            for ex in named:
                dest = ex.destination
                dest_name = dest.key if dest else "nowhere"
                display = self._shortest_exit_label(ex)
                lines.append(f"  {display:10} → {dest_name}")

        self.caller.msg("\n".join(lines))

    def _shortest_exit_label(self, ex):
        """Return the shortest label for an exit (prefers aliases like 'n' over 'north')."""
        candidates = [(ex.key or "")]
        for alias in ex.aliases.all():
            candidates.append(alias)
        # Filter out empty strings
        candidates = [c for c in candidates if c.strip()]
        if not candidates:
            return ex.key or "exit"
        return min(candidates, key=len)
