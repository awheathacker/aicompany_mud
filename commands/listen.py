"""
commands/listen.py

Listen command: eavesdrop on speech and whispers from adjacent rooms.

Usage:
  listen [direction]  — listen through an exit
  listen              — listen at your current room

Shows the most recent speech from the target room (if the room tracks
whispers/speech memory).

Helps players gather intel from neighboring rooms before committing
to move in, or keep an ear on nearby activity.
"""

from evennia import Command
from evennia.utils.search import search_object


class CmdListen(Command):
    """
    Eavesdrop on speech from a room through an exit or by dbref.

    Usage:
      listen [direction]  — listen through the named exit
      listen              — listen at your current room
      listen #<dbref>     — listen at a specific room by dbref

    Shows recent speech/transmission in the target room so players can
    gauge the mood and activity of a space without entering.
    """
    key = "listen"
    aliases = ["eavesdrop", "hear"]
    help_category = "Navigation"
    locks = "cmd:all()"

    def _find_exit(self, room, name):
        """Find exit by key or alias, case-insensitive."""
        low = name.lower()
        for ex in room.exits:
            if (ex.key or "").lower() == low:
                return ex
            if low in [a.lower() for a in ex.aliases.all()]:
                return ex
        return None

    def _get_room_speech_summary(self, room):
        """
        Gather speech/whispers from a room.

        Tries multiple sources:
        1. SmartRoom.db.memory (list of {"who": ..., "msg": ...} dicts)
        2. room.db.whispers or room.db.speech (list of strings/tuples)
        3. room.whisper_buffer (if available)
        """
        room_key = getattr(room, "key", str(room))

        # --- Try SmartRoom.db.memory (list of {"who": X, "msg": Y}) ---
        memory = getattr(room.db, "memory", None)
        if memory and isinstance(memory, list) and memory:
            max_shown = min(len(memory), 10)
            lines = [f"|wListening at {room_key}:|n"]
            lines.append("|yRecent speech:|n")
            for entry in memory[-max_shown:]:
                if isinstance(entry, dict):
                    speaker = entry.get("who", "??")
                    text = entry.get("msg", "")
                    lines.append(f"  {speaker}: {text}")
                elif isinstance(entry, (list, tuple)):
                    lines.append(f"  {entry[0]}: {entry[1] if len(entry) > 1 else ''}")
                else:
                    lines.append(f"  {entry}")
            return "\n".join(lines)

        # --- Try db.whispers / db.speech (legacy) ---
        speech = getattr(room.db, "whispers", None) or getattr(room.db, "speech", None)
        if speech and isinstance(speech, list) and speech:
            lines = [f"|wListening at {room_key}:|n"]
            lines.append("|yRecent speech:|n")
            max_shown = min(len(speech), 10)
            for entry in speech[-max_shown:]:
                if isinstance(entry, (list, tuple)):
                    lines.append(f"  {entry[0]}: {entry[1] if len(entry) > 1 else ''}")
                else:
                    lines.append(f"  {entry}")
            return "\n".join(lines)

        # --- Try whisper_buffer ---
        whispers = getattr(room, "whisper_buffer", None)
        if whispers:
            if callable(whispers):
                whispers = whispers()
            if whispers:
                lines = [f"|wListening at {room_key}:|n"]
                lines.append("|yRecent speech:|n")
                for entry in whispers[-min(len(whispers), 10)]:
                    if isinstance(entry, (list, tuple)):
                        lines.append(f"  {entry[0]}: {entry[1] if len(entry) > 1 else ''}")
                    else:
                        lines.append(f"  {entry}")
                return "\n".join(lines)

        return f"|wListening at {room_key}:|n\n|n...silence. The room is quiet.|n"

    def _resolve_target(self, arg):
        """Resolve a dbref argument to a room object. Returns (room, error)."""
        if not arg or not arg.startswith("#"):
            return None, None
        if not arg[1:].isdigit():
            return None, None
        matches = search_object(arg)
        if not matches:
            return None, f"No room found for {arg}."
        target = matches[0]
        if getattr(target, "location", None) is not None:
            return None, f"{arg} seems to be an object, not a room."
        return target, None

    def func(self):
        """Execute the listen command."""
        caller = self.caller
        room = caller.location

        if not room:
            caller.msg("You are nowhere to listen from.")
            return

        args = (self.args or "").strip()

        if not args:
            # No argument: listen at current room
            caller.msg(self._get_room_speech_summary(room))
            return

        # Try to resolve as dbref
        target_room, err = self._resolve_target(args)
        if target_room:
            caller.msg(self._get_room_speech_summary(target_room))
            return
        if err:
            caller.msg(err)
            return

        # Try to find an exit by name
        exit_obj = self._find_exit(room, args)
        if not exit_obj:
            caller.msg(f"No exit named '{args}' from here.")
            return

        dest = getattr(exit_obj, "destination", None)
        if not dest:
            caller.msg(f"The exit '{args}' leads to... nothing? Spooky.")
            return

        caller.msg(f"|wEavesdropping through '{args}':|n\n" + self._get_room_speech_summary(dest))
