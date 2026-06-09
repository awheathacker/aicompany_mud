# commands/drink.py
# Drink command — uses the ability system to find and execute abilities

from evennia import Command
from evennia.utils.search import search_object

# Import abilities_drink so the decorator registers the "drink" ability at startup
import utils.abilities_drink
from utils.abilities import find_abilities_for_object, execute_ability


class CmdDrink(Command):
    """
    Drink from a liquid container using the ability framework.

    Usage:
      drink [target]

    Examples:
      drink glass of soda
      drink tea
      drink #123
    """
    key = "drink"
    aliases = ["sip", "gulp", "swallow"]
    locks = "cmd:all()"
    help_category = "Abilities"

    def func(self):
        caller = self.caller
        room = caller.location

        if not room:
            caller.msg("You are nowhere to drink in.")
            return

        target_key = (self.args or "").strip()

        if not target_key:
            # No target specified — list drinkable things
            drinkable = [
                obj for obj in room.contents
                if hasattr(obj, 'db') and
                obj.db.properties and
                obj.db.properties.get("is_drinkable") and
                obj.db.properties.get("current_volume_ml", 0) > 0
            ]

            if drinkable:
                lines = ["|yYou can drink from:|n"]
                for obj in drinkable:
                    props = obj.db.properties
                    name = props.get("liquid_name", "liquid")
                    vol = props.get("current_volume_ml", 0)
                    lines.append(f"  {obj.key} ({vol}ml of {name})")
                caller.msg("\n".join(lines))
            else:
                caller.msg("There's nothing drinkable here.")
            return

        # Find the target object
        if target_key.startswith("#"):
            matches = search_object(target_key)
            if matches:
                target = matches[0]
                if target.location != room:
                    caller.msg(f"You don't see '{target_key}' to drink from.")
                    return
            else:
                caller.msg(f"You don't see '{target_key}' to drink from.")
                return
        else:
            # Search room contents by name
            matches = [obj for obj in room.contents
                       if target_key.lower() in obj.key.lower()]
            if matches:
                target = matches[0]
            else:
                caller.msg(f"You don't see '{target_key}' to drink from.")
                return

        # Use the ability framework
        abilities = find_abilities_for_object(target)

        if not abilities:
            if not target.db.properties:
                caller.msg(f"The {target.key} doesn't seem to have any special properties.")
                return
            if not target.db.properties.get("is_drinkable"):
                caller.msg(f"The {target.key} isn't drinkable.")
                return
            current_vol = target.db.properties.get("current_volume_ml", 0)
            if current_vol <= 0:
                caller.msg(f"The {target.key} is empty.")
                return
            caller.msg(f"Nothing to drink from the {target.key}.")
            return

        # Execute the ability
        execute_ability(caller, "drink", target)


class CmdCheckAbilities(Command):
    """
    Check what abilities are available for an object.

    Usage:
      check [target]
      abilities [target]
    """
    key = "check"
    aliases = ["abilities", "inspect", "probe"]
    locks = "cmd:all()"
    help_category = "Abilities"

    def func(self):
        caller = self.caller
        room = caller.location

        if not room:
            caller.msg("You are nowhere.")
            return

        target_key = (self.args or "").strip()

        if not target_key:
            # List objects with special abilities
            objects_with_abilities = []
            for obj in room.contents:
                if hasattr(obj, 'db') and obj.db.properties:
                    abilities = find_abilities_for_object(obj)
                    if abilities:
                        objects_with_abilities.append((obj, abilities))

            if objects_with_abilities:
                lines = ["|yObjects with special abilities:|n"]
                for obj, abilities in objects_with_abilities:
                    ability_names = [a.get("name", "unknown") for a in abilities]
                    lines.append(f"  {obj.key}: {', '.join(ability_names)}")
                caller.msg("\n".join(lines))
            else:
                caller.msg("No special abilities detected on objects here.")
            return

        # Find the target
        if target_key.startswith("#"):
            matches = search_object(target_key)
            if matches:
                target = matches[0]
            else:
                caller.msg(f"You don't see '{target_key}'.")
                return
        else:
            # Simple search
            matches = [obj for obj in room.contents
                       if target_key.lower() in obj.key.lower()]
            if matches:
                target = matches[0]
            else:
                caller.msg(f"You don't see '{target_key}'.")
                return

        if not hasattr(target, 'db'):
            caller.msg(f"The {target.key} seems like a normal object.")
            return

        # Show object properties
        props = target.db.properties
        if props:
            lines = [f"|y{target.key} properties:|n"]

            if props.get("object_type"):
                lines.append(f"  Type: {props['object_type']}")

            if props.get("is_container"):
                lines.append(f"  Container (capacity: {props.get('capacity_ml', 240)}ml)")

            if props.get("is_liquid"):
                lines.append(f"  Liquid: {props.get('liquid_name', 'liquid')} ({props.get('current_volume_ml', 0)}ml)")

            if props.get("is_drinkable"):
                lines.append("  ✓ Drinkable")

            if props.get("is_lit"):
                lines.append(f"  Light (radius: {props.get('light_radius', 3)} rooms)")

            caller.msg("\n".join(lines) + "\n\n")

        # Show available abilities
        abilities = find_abilities_for_object(target)
        if abilities:
            lines = ["|wAvailable abilities:|n"]
            for ability in abilities:
                name = ability.get("name", "unknown")
                description = ability.get("description", "")
                lines.append(f"  {name}: {description}")
            caller.msg("\n".join(lines))
        else:
            caller.msg(f"No special abilities available for the {target.key}.")
