# utils/object_properties.py
# Object Properties Framework — Schema and helpers for MUD objects


# Schema for known property groups
PROPERTY_SCHEMAS = {
    "liquid": {
        "is_liquid": True,
        "liquid_name": "water",
        "current_volume_ml": 240,
        "capacity_ml": 240,
        "is_drinkable": True,
    },
    "container": {
        "is_container": True,
        "capacity_ml": 240,
    },
    "food": {
        "is_food": True,
        "nutrition": 1,
        "is_eaten": False,
    },
    "wearable": {
        "is_wearable": True,
        "wear_slot": "body",
        "is_worn": False,
    },
    "light_source": {
        "is_lit": True,
        "light_radius": 3,
        "fuel": 100,
    },
}


def get_default_properties(schema_name):
    """Return the default property dict for a given schema name."""
    schema = PROPERTY_SCHEMAS.get(schema_name)
    return dict(schema) if schema else {}


def ensure_properties(obj, schema_name):
    """
    Merge default properties from the given schema into the object's db.properties.

    Args:
        obj: Evennia object with db.properties (or db.properties = None)
        schema_name: Key into PROPERTY_SCHEMAS

    Returns:
        The updated properties dict
    """
    props = dict(obj.db.properties or {})
    defaults = get_default_properties(schema_name)
    for k, v in defaults.items():
        if k not in props:
            props[k] = v
    obj.db.properties = props
    return props


def apply_properties_from_json(obj, json_string):
    """
    Parse a JSON string and merge the properties into the object.

    Args:
        obj: Evennia object
        json_string: JSON-encoded property dict (e.g. '{"is_drinkable": true, "liquid_name": "soda"}')

    Returns:
        The updated properties dict
    """
    import json

    new_props = json.loads(json_string)
    props = dict(obj.db.properties or {})
    props.update(new_props)
    obj.db.properties = props
    return props


def object_is_drinkable(obj):
    """Check if an Evennia object is drinkable and has volume > 0."""
    props = obj.db.properties or {}
    return bool(
        props.get("is_drinkable")
        and props.get("current_volume_ml", 0) > 0
    )


def object_is_empty(obj):
    """Check if a drinkable object is empty."""
    props = obj.db.properties or {}
    return props.get("is_drinkable") and props.get("current_volume_ml", 0) <= 0
