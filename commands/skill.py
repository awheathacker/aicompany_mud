"""
skill command — view and manage character skills.

Usage:
  skill                (show all skills and levels)
  skill <skill>        (show detail for one skill)

Skills tracked: strength, agility, charisma, wisdom, endurance,
                perception, luck, crafting, stealth, combat

Each skill has levels: Novice → Adept → Veteran → Master → Legend

Examples:
  skill
  skill combat
"""
from commands.command import Command

SKILLS = {
    "strength": "Raw physical power",
    "agility": "Speed and reflexes",
    "charisma": "Social influence",
    "wisdom": "Knowledge and intuition",
    "endurance": "Stamina and resilience",
    "perception": "Awareness of surroundings",
    "luck": "Fortune in uncertain times",
    "crafting": "Artisan skill",
    "stealth": "Moving unseen",
    "combat": "Fighting prowess",
}

LEVEL_NAMES = {
    0: "Novice",
    1: "Adept",
    2: "Veteran",
    3: "Master",
    4: "Legend",
}

XP_PER_LEVEL = {
    0: 5,
    1: 12,
    2: 25,
    3: 50,
    4: 100,
}


def _get_skills_data(caller):
    """Return the caller's skills dict, initializing if needed."""
    return getattr(caller.db, "skills", {})


def _get_xp_data(caller):
    """Return the caller's XP dict, initializing if needed."""
    return getattr(caller.db, "xp", {})


def _get_level(xp: int) -> int:
    """Determine the level from total XP."""
    total = 0
    for lv, needed in XP_PER_LEVEL.items():
        total += needed
        if xp < total:
            return lv
    return 4


def _level_name(level: int) -> str:
    return LEVEL_NAMES.get(level, "God")


def _xp_to_next(xp: int, level: int) -> int:
    """How much XP needed to reach the next level."""
    total = 0
    for lv, needed in XP_PER_LEVEL.items():
        total += needed
        if lv == level:
            return needed
    return 0


class CmdSkill(Command):
    """
    View your character's skills and experience.

    Usage:
      skill                (show all skills)
      skill <skill>        (show detail for one skill)
    """
    key = "skill"
    aliases = ["skills", "stats"]
    help_category = "Character"

    def func(self):
        caller = self.caller
        args = (self.args or "").strip()

        if args:
            # Show detail for one skill
            skill_name = args.lower()
            if skill_name not in SKILLS:
                caller.msg(f"Unknown skill: '{skill_name}'. Available: {', '.join(SKILLS.keys())}")
                return
            xp = _get_xp_data(caller).get(skill_name, 0)
            level = _get_level(xp)
            caller.msg(f"{skill_name.title()}: {_level_name(level)} (level {level}) — {xp} XP")
            needed = _xp_to_next(xp, level)
            if level < 4:
                caller.msg(f"  Need {needed} more XP to reach Level {level + 1} ({_level_name(level + 1)}).")
            else:
                caller.msg("  Maximum level reached!")
            return

        # Show all skills
        xp_data = _get_xp_data(caller)
        lines = ["Your skills:"]
        for skill_name, desc in SKILLS.items():
            xp = xp_data.get(skill_name, 0)
            level = _get_level(xp)
            lines.append(f"  {skill_name:<14} {_level_name(level):<12} Level {level}  ({xp} XP)")
        caller.msg("\n".join(lines))


class CmdTrain(Command):
    """
    Train a character skill to gain experience points.

    Usage:
      train <skill>       (train a skill for 1 XP)
      train <skill> <n>   (train a skill for n XP)
    """
    key = "train"
    aliases = ["practice", "study"]
    help_category = "Character"

    def func(self):
        caller = self.caller
        args = (self.args or "").strip()

        if not args:
            caller.msg("Usage: train <skill> [amount]")
            return

        parts = args.split(maxsplit=1)
        skill_name = parts[0].lower()
        amount = 1
        if len(parts) > 1:
            try:
                amount = int(parts[1])
            except ValueError:
                caller.msg(f"Invalid amount: '{parts[1]}'. Use a number, e.g. 'train agility 5'.")
                return

        if amount < 1:
            caller.msg("Amount must be at least 1.")
            return

        if skill_name not in SKILLS:
            caller.msg(f"Unknown skill: '{skill_name}'. Available: {', '.join(SKILLS.keys())}")
            return

        xp_data = _get_xp_data(caller)
        old_xp = xp_data.get(skill_name, 0)
        old_level = _get_level(old_xp)
        xp_data[skill_name] = old_xp + amount
        new_level = _get_level(xp_data[skill_name])

        caller.db.xp = xp_data

        caller.msg(f"You practice your {skill_name}. {amount} XP earned ({old_xp} → {xp_data[skill_name]}).")

        if new_level > old_level:
            caller.msg(f"Level up! Your {skill_name} is now Level {new_level} ({_level_name(new_level)})!")

        # Initialize skills dict so they show up in 'skill' output
        if skill_name not in _get_skills_data(caller):
            skills_data = _get_skills_data(caller)
            skills_data[skill_name] = True
            caller.db.skills = skills_data
