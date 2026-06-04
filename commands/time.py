"""
Time command — show in-game time of day and passage tracking.

Displays the current game time (hour of day) with a descriptive label
(dawn, morning, noon, afternoon, dusk, evening, night, midnight)
and shows a simple 24-hour clock. Players can also pass time
(sleep, wait) to advance the clock.

Examples:
  time            — show current time
  time pass 2     — advance time by 2 hours
  time sleep      — sleep until morning (6:00)
"""
from evennia import Command


HOUR_NAMES = {
    0: "midnight",
    1: "midnight",
    2: "the deepest night",
    3: "the deep night",
    4: "the pre-dawn dark",
    5: "dawn",
    6: "early morning",
    7: "morning",
    8: "mid-morning",
    9: "late morning",
    10: "midday",
    11: "near noon",
    12: "noon",
    13: "early afternoon",
    14: "afternoon",
    15: "late afternoon",
    16: "dusk",
    17: "early evening",
    18: "evening",
    19: "dusk",
    20: "early night",
    21: "nightfall",
    22: "late night",
    23: "near midnight",
}


def get_time_of_day(hour: int) -> str:
    """Return a descriptive label for the given 24-hour clock hour."""
    return HOUR_NAMES.get(hour, "an unknown hour")


def format_time(hour: int) -> str:
    """Format a 24-hour hour into a nice string like '2:30 PM'."""
    h = hour % 24
    if h == 0:
        return "12:00 AM"
    elif h < 12:
        return f"{h}:00 AM"
    elif h == 12:
        return "12:00 PM"
    else:
        return f"{h - 12}:00 PM"


class CmdTime(Command):
    """
    Check or advance in-game time.

    Usage:
      time                    — show current time of day
      time pass <hours>      — advance time by N hours
      time sleep             — sleep until morning (6 AM)
    """
    key = "time"
    aliases = ["clock"]
    locks = "cmd:all()"
    help_category = "World"

    def _get_game_time(self):
        """Retrieve the current game hour from the room's db attribute."""
        room = self.caller.location
        if room:
            return int(room.db.game_hour) if hasattr(room.db, "game_hour") else 12
        return 12

    def _set_game_time(self, hour: int):
        """Set the game hour on the current room."""
        room = self.caller.location
        if room:
            hour = hour % 24
            room.db.game_hour = hour
            return hour
        return hour

    def _describe_time(self, hour: int) -> tuple:
        """Build a descriptive time message."""
        label = get_time_of_day(hour)
        clock = format_time(hour)
        if 6 <= hour < 12:
            mood = "The morning light filters through."
        elif 12 <= hour < 17:
            mood = "The sun is high and bright."
        elif 17 <= hour < 20:
            mood = "The golden hour gives everything a warm glow."
        elif 20 <= hour < 23 or 0 <= hour < 5:
            mood = "Shadows stretch long across the floor."
        else:
            mood = "The twilight is soft and brief."
        return clock, label, mood

    def func(self):
        caller = self.caller
        args = (self.args or "").strip().lower()

        if not args:
            # Default: show current time
            hour = self._get_game_time()
            clock, label, mood = self._describe_time(hour)
            caller.msg(f"|wCurrent time: {clock} ({label})|n")
            caller.msg(mood)
            return

        if args == "sleep":
            hour = self._get_game_time()
            target = 6  # morning
            if hour < 6:
                hours_passed = target - hour
            else:
                hours_passed = (24 - hour) + target
            new_hour = self._set_game_time(target)
            clock, label, mood = self._describe_time(new_hour)
            caller.msg(f"You sleep for {hours_passed} hour{'s' if hours_passed != 1 else ''}.")
            caller.msg(f"|wIt is now {clock} ({label}).|n")
            caller.msg(mood)
            return

        if args.startswith("pass "):
            try:
                hours_str = args.split(" ", 1)[1].strip()
                hours = int(hours_str)
            except (ValueError, IndexError):
                caller.msg(f"|wUsage: time pass <hours>|n")
                return
            if hours < 1 or hours > 12:
                caller.msg("Pass between 1 and 12 hours at a time.")
                return
            old_hour = self._get_game_time()
            new_hour = self._set_game_time(old_hour + hours)
            clock, label, mood = self._describe_time(new_hour)
            caller.msg(f"Time passes — {hours} hour{'s' if hours != 1 else ''} later...")
            caller.msg(f"|wIt is now {clock} ({label}).|n")
            caller.msg(mood)
            return

        # Fallback: show usage
        caller.msg("|wUsage: time [pass <hours> | sleep]|n")
        caller.msg("  time           — show current time of day")
        caller.msg("  time pass N    — advance time by N hours")
        caller.msg("  time sleep     — sleep until morning")
