"""
Emote command — express yourself in the current room.

Lets players perform actions or expressions visible to everyone
in the same room. Supports free-text emotes, emote prefixes, and
targeted emotes using the standard MUD syntax.

Examples:
  emote sighs deeply
  emote laughs at the joke
  emote draws their sword
  emote waves to Alyssa
"""
from evennia import Command


class CmdEmote(Command):
    """
    Emote an action or expression to the current room.

    Usage:
      emote <expression>

    The emote is displayed to everyone in the room (including the
    emitter). Supports standard MUD emote syntax:
      - "emote sighs"        → *You* sighs
      - "emote waves to Alyssa" → *You* waves to Alyssa
      - "emote hands a letter to the guard" → *You* hands a letter to the guard

    The emote is also broadcast over the room's channel for NPCs
    and scripted listeners to react to.
    """
    key = "emote"
    aliases = ["emi", "say"]
    locks = "cmd:all()"
    help_category = "Social"

    def func(self):
        caller = self.caller
        room = caller.location

        if not room:
            caller.msg("You are floating in the void — no one to emote to.")
            return

        args = (self.args or "").strip()
        if not args:
            caller.msg("Emote what? (|wemote <expression>|n)")
            return

        # Sanitize: collapse whitespace, limit length
        args = " ".join(args.split())
        if len(args) > 200:
            args = args[:197] + "..."

        # Format the emote for the emitter
        my_name = caller.key or "You"
        my_msg = f"*{my_name}* {args}"

        # Format for everyone else in the room
        other_msg = f"*{my_name}* {args}"

        # Broadcast to caller
        caller.msg(my_msg)

        # Broadcast to others in the room
        for obj in room.contents:
            if obj == caller:
                continue
            if hasattr(obj, "msg"):
                obj.msg(other_msg)

        # Store the emote in the room's whispers/history for later
        # (compatibility with the whispers command if it exists)
        if hasattr(room.db, "emote_history"):
            room.db.emote_history.append({
                "from": my_name,
                "text": args,
                "timestamp": getattr(caller, "db", None) or ""
            })
            # Keep only the last 50 emotes
            if len(room.db.emote_history) > 50:
                room.db.emote_history = room.db.emote_history[-50:]
        else:
            room.db.emote_history = [{
                "from": my_name,
                "text": args,
                "timestamp": ""
            }]
