"""
Weather command — atmospheric world state for the MUD.

Usage:
  weather              (show current weather)
  weather set <type>  (set weather, e.g. "sunny", "rainy", "storm")
  weather cycle       (advance to the next weather type)

Weather affects the atmosphere of rooms and can be used for roleplay,
quests, and environmental storytelling.

Example:
  weather
  weather set storm
  weather cycle
"""
from commands.command import Command

WEATHER_TYPES = [
    "sunny",
    "cloudy",
    "rainy",
    "windy",
    "storm",
    "clear"
]

WEATHER_DESCRIPTIONS = {
    "sunny": "|wThe sun blazes down, casting golden light across the landscape.|n",
    "cloudy": "|hSoft clouds drift overhead, diffusing the light.|n",
    "rainy": "|HRain patters steadily, drumming against the world.|n",
    "windy": "|gWinds howl through the spaces between things.|n",
    "storm": "|rThunder rumbles and lightning cracks across the sky.|n",
    "clear": "|WCrystal-clear skies stretch in every direction.|n",
}

WEATHER_FLAVOR = {
    "sunny": "Bright warmth fills the air. Everything sparkles.",
    "cloudy": "A gentle overcast hangs above. Temperate and calm.",
    "rainy": "Drops of water bead on every surface. The world smells of fresh earth.",
    "windy": "Leaves and loose objects sway. The air feels alive.",
    "storm": "The world trembles with power. Rain and thunder dominate.",
    "clear": "The air is sharp and still. Stars (or sun) shine with perfect clarity.",
}


def get_weather(caller=None):
    """Get the current weather type from server ndb."""
    if caller:
        server = caller._session and getattr(caller._session, "server", None)
        if server:
            weather = getattr(server.ndb, "weather", None)
            if weather:
                return weather
    # Fallback: return the first (default) weather
    return "sunny"


def set_weather(caller, weather_type):
    """Set the global weather state on server ndb."""
    weather_type = weather_type.lower().strip()
    if weather_type not in WEATHER_TYPES:
        return False

    if caller:
        server = caller._session and getattr(caller._session, "server", None)
        if server:
            server.ndb.weather = weather_type

    return True


def next_weather(current):
    """Cycle to the next weather type."""
    idx = WEATHER_TYPES.index(current)
    return WEATHER_TYPES[(idx + 1) % len(WEATHER_TYPES)]


class CmdWeather(Command):
    """
    Check or set the weather in the world.

    Usage:
      weather              (show current weather)
      weather set <type>   (set weather: sunny, cloudy, rainy, windy, storm, clear)
      weather cycle        (advance to the next weather type)

    The weather sets the mood of the world. You can check it at any time
    or influence it if you're feeling creative.
    """
    key = "weather"
    aliases = ["climate", "atmosphere", "sky"]
    help_category = "Environment"

    def func(self):
        caller = self.caller
        args = (self.args or "").strip()

        if not args:
            # Show current weather
            current = get_weather(caller)
            caller.msg(WEATHER_DESCRIPTIONS.get(current, "|?Unknown weather...|n"))
            caller.msg(f"|nThe weather is |w{current}|n. {WEATHER_FLAVOR.get(current, '')}")
            return

        if args.startswith("set "):
            weather_type = args[4:].strip()
            if weather_type not in WEATHER_TYPES:
                caller.msg(f"Unknown weather type: '{weather_type}'.")
                caller.msg(f"Available: {', '.join(WEATHER_TYPES)}")
                return

            if set_weather(caller, weather_type):
                caller.msg(WEATHER_DESCRIPTIONS[weather_type])
                caller.msg(f"|nThe weather is now |w{weather_type}|n.")
                # Broadcast to room
                room = caller.get_location()
                if room:
                    room.msg_contents(
                        f"|mThe sky shifts… {WEATHER_DESCRIPTIONS[weather_type]}|n"
                    )
            else:
                caller.msg("The weather resists change.")
            return

        if args == "cycle":
            current = get_weather(caller)
            nxt = next_weather(current)
            if set_weather(caller, nxt):
                caller.msg(WEATHER_DESCRIPTIONS[nxt])
                caller.msg(f"|nWeather cycled: |w{current}|n → |w{nxt}|n")
                # Broadcast to room
                room = caller.get_location()
                if room:
                    room.msg_contents(
                        f"|mThe atmosphere shifts from {current} to {nxt}…|n"
                    )
            else:
                caller.msg("The weather refuses to change.")
            return

        if args == "types" or args == "list":
            caller.msg("Weather types:")
            for w in WEATHER_TYPES:
                caller.msg(f"  |w{w}|n — {WEATHER_FLAVOR[w][:60]}")
            return

        caller.msg(f"Unknown weather command: '{args}'. Try 'weather set <type>' or 'weather cycle'.")
        caller.msg(f"Available types: {', '.join(WEATHER_TYPES)}")
