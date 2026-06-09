# tests/utils/test_object_properties.py
# Tests for object properties framework

import pytest
from unittest.mock import MagicMock

from utils.object_properties import (
    PROPERTY_SCHEMAS,
    get_default_properties,
    ensure_properties,
    apply_properties_from_json,
    object_is_drinkable,
    object_is_empty,
)


class TestPropertySchemas:
    def test_liquid_schema_exists(self):
        assert "liquid" in PROPERTY_SCHEMAS

    def test_liquid_schema_has_drinkable(self):
        assert PROPERTY_SCHEMAS["liquid"]["is_drinkable"] is True

    def test_container_schema_exists(self):
        assert "container" in PROPERTY_SCHEMAS

    def test_food_schema_exists(self):
        assert "food" in PROPERTY_SCHEMAS

    def test_wearable_schema_exists(self):
        assert "wearable" in PROPERTY_SCHEMAS

    def test_light_source_schema_exists(self):
        assert "light_source" in PROPERTY_SCHEMAS

    def test_unknown_schema_returns_empty(self):
        assert get_default_properties("nonexistent") == {}

    def test_get_default_properties_returns_copy(self):
        props = get_default_properties("liquid")
        props["is_drinkable"] = False
        assert PROPERTY_SCHEMAS["liquid"]["is_drinkable"] is True


class TestEnsureProperties:
    def _mock_obj(self, properties=None):
        obj = MagicMock()
        obj.db = MagicMock()
        obj.db.properties = properties
        return obj

    def test_ensure_properties_starts_empty(self):
        obj = self._mock_obj(properties=None)
        result = ensure_properties(obj, "liquid")
        assert result["is_drinkable"] is True
        assert result["current_volume_ml"] == 240

    def test_ensure_properties_preserves_existing(self):
        obj = self._mock_obj(properties={"liquid_name": "soda"})
        result = ensure_properties(obj, "liquid")
        assert result["liquid_name"] == "soda"
        assert result["is_drinkable"] is True
        assert result["current_volume_ml"] == 240

    def test_ensure_properties_overwrites_with_default(self):
        obj = self._mock_obj(properties={"is_drinkable": True})
        result = ensure_properties(obj, "food")
        assert result["is_food"] is True
        assert result["is_eaten"] is False


class TestApplyPropertiesFromJson:
    def _mock_obj(self, properties=None):
        obj = MagicMock()
        obj.db = MagicMock()
        obj.db.properties = properties
        return obj

    def test_apply_json_to_empty_object(self):
        obj = self._mock_obj(properties=None)
        result = apply_properties_from_json(obj, '{"is_drinkable": true}')
        assert result["is_drinkable"] is True

    def test_apply_json_merges_with_existing(self):
        obj = self._mock_obj(properties={"is_drinkable": True})
        apply_properties_from_json(obj, '{"liquid_name": "soda"}')
        props = obj.db.properties
        assert props["is_drinkable"] is True
        assert props["liquid_name"] == "soda"

    def test_apply_json_overwrites_values(self):
        obj = self._mock_obj(properties={"current_volume_ml": 240})
        apply_properties_from_json(obj, '{"current_volume_ml": 100}')
        assert obj.db.properties["current_volume_ml"] == 100


class TestObjectIsDrinkable:
    def _mock_obj(self, properties=None):
        obj = MagicMock()
        obj.db = MagicMock()
        obj.db.properties = properties
        return obj

    def test_drinkable_with_volume(self):
        obj = self._mock_obj(properties={
            "is_drinkable": True,
            "current_volume_ml": 120,
        })
        assert object_is_drinkable(obj) is True

    def test_drinkable_zero_volume(self):
        obj = self._mock_obj(properties={
            "is_drinkable": True,
            "current_volume_ml": 0,
        })
        assert object_is_drinkable(obj) is False

    def test_non_drinkable(self):
        obj = self._mock_obj(properties={
            "is_drinkable": False,
            "current_volume_ml": 120,
        })
        assert object_is_drinkable(obj) is False

    def test_no_properties(self):
        obj = self._mock_obj(properties=None)
        assert object_is_drinkable(obj) is False

    def test_missing_volume_key(self):
        obj = self._mock_obj(properties={"is_drinkable": True})
        assert object_is_drinkable(obj) is False


class TestObjectIsEmpty:
    def _mock_obj(self, properties=None):
        obj = MagicMock()
        obj.db = MagicMock()
        obj.db.properties = properties
        return obj

    def test_empty_drinkable(self):
        obj = self._mock_obj(properties={
            "is_drinkable": True,
            "current_volume_ml": 0,
        })
        assert object_is_empty(obj) is True

    def test_not_empty(self):
        obj = self._mock_obj(properties={
            "is_drinkable": True,
            "current_volume_ml": 60,
        })
        assert object_is_empty(obj) is False

    def test_empty_non_drinkable(self):
        obj = self._mock_obj(properties={
            "is_drinkable": False,
            "current_volume_ml": 0,
        })
        assert object_is_empty(obj) is False
