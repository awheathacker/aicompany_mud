# commands/mood.py
"""
Mood Command

Sets or displays the atmospheric mood of the current room.
Adds an emotional tone layer that complements weather and whispers.

Usage:
  mood                (show current mood)
  mood set <mood>     (set a new mood)
  mood clear          (clear the mood)
"""
from evennia import Command


class CmdMood(Command):
    """
    Set or view the emotional mood of the current room.

    A mood adds atmosphere — things like "tense", "euphoric",
    "haunting", or "boisterous". The mood is displayed when
    players look at the room, helping set the tone of a scene.

    Usage:
      mood                Show current mood
      mood set tense      Set the room's mood
      mood clear          Clear the mood
      mood <mood_word>    Quick set (shorthand)

    Examples:
      mood set eerie
      mood boisterous
      mood clear
    """
    key = "mood"
    aliases = ["ambiance", "tone", "atmosphere"]
    locks = "cmd:all()"
    help_category = "World"

    def func(self):
        room = self.caller.location
        if not room:
            self.caller.msg("You are nowhere — no mood to read.")
            return

        args = (self.args or "").strip()

        # --- Show current mood (no args) ---
        if not args:
            current = room.db.mood if hasattr(room, "db") else None
            if current:
                self.caller.msg(f"|mThe room feels |y{current}|m.|n")
            else:
                self.caller.msg("The room has no distinct mood right now.")
            return

        # --- Set mood ---
        if args.lower() == "clear":
            if hasattr(room, "db"):
                room.db.mood = room.db.mood or ""
                if room.db.mood:
                    old = room.db.mood
                    room.db.mood = ""
                    self.caller.msg(f"|mThe feeling of |y{old}|m fades from the room.|n")
                else:
                    self.caller.msg("The room's mood was already blank.")
            return

        if args.lower() == "set":
            mood = args.split(" ", 2)[-1]
            if not mood:
                self.caller.msg("Set the mood to what? Try: |wmood set mysterious|n")
                return
            if hasattr(room, "db"):
                room.db.mood = mood
                self.caller.msg(f"|mThe room takes on a |y{mood}|m quality.|n")
            return

        # --- Shorthand: mood <word> (direct set) ---
        if hasattr(room, "db"):
            room.db.mood = args
            self.caller.msg(f"|mThe room feels |y{args}|m now.|n")
