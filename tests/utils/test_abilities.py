# tests/utils/test_abilities.py
# Tests for ability framework

import pytest
from unittest.mock import MagicMock

from utils.abilities import (
    _ABILITIES,
    register_ability,
    get_abilities,
    find_ability_by_verb,
    _check_property_match,
    find_abilities_for_object,
    execute_ability,
    get_verb_map,
)


class TestCheckPropertyMatch:
    def test_bool_match_true(self):
        props = {"is_drinkable": True}
        assert _check_property_match(props, "is_drinkable", "True") is True

    def test_bool_match_false(self):
        props = {"is_drinkable": False}
        assert _check_property_match(props, "is_drinkable", "False") is True

    def test_gte_match(self):
        props = {"current_volume_ml": 200}
        assert _check_property_match(props, "current_volume_ml", ">=1") is True

    def test_gte_match_edge(self):
        props = {"current_volume_ml": 1}
        assert _check_property_match(props, "current_volume_ml", ">=1") is True

    def test_gte_match_zero(self):
        props = {"current_volume_ml": 0}
        assert _check_property_match(props, "current_volume_ml", ">=1") is False

    def test_lte_match(self):
        props = {"current_volume_ml": 50}
        assert _check_property_match(props, "current_volume_ml", "<=100") is True

    def test_lte_match_edge(self):
        props = {"current_volume_ml": 100}
        assert _check_property_match(props, "current_volume_ml", "<=100") is True

    def test_gt_match(self):
        props = {"current_volume_ml": 100}
        assert _check_property_match(props, "current_volume_ml", ">1") is True

    def test_lt_match(self):
        props = {"current_volume_ml": 50}
        assert _check_property_match(props, "current_volume_ml", "<100") is True

    def test_exact_int_match(self):
        props = {"current_volume_ml": 120}
        assert _check_property_match(props, "current_volume_ml", 120) is True

    def test_exact_int_mismatch(self):
        props = {"current_volume_ml": 120}
        assert _check_property_match(props, "current_volume_ml", 60) is False

    def test_string_exact_match(self):
        props = {"liquid_name": "soda"}
        assert _check_property_match(props, "liquid_name", "soda") is True

    def test_missing_property(self):
        props = {"is_drinkable": True}
        assert _check_property_match(props, "current_volume_ml", ">=1") is False

    def test_bool_false_string_mismatch(self):
        props = {"is_drinkable": False}
        assert _check_property_match(props, "is_drinkable", "True") is False


class TestRegisterAbility:
    def setup_method(self):
        # Clear registry before each test
        _ABILITIES.clear()

    def test_register_with_decorator(self):
        @register_ability(name="wear", verbs=["wear", "don"], requires_property={"is_wearable": "True"})
        def test_wear_func(caller, target):
            pass

        assert "wear" in _ABILITIES
        assert _ABILITIES["wear"]["name"] == "wear"
        assert _ABILITIES["wear"]["verbs"] == ["wear", "don"]

    def test_register_default_verbs(self):
        @register_ability(name="eat")
        def test_eat_func(caller, target):
            pass

        assert _ABILITIES["eat"]["verbs"] == ["eat"]

    def test_register_default_requires_property(self):
        @register_ability(name="read")
        def test_read_func(caller, target):
            pass

        assert _ABILITIES["read"]["requires_property"] == {}


class TestFindAbilityByVerb:
    def setup_method(self):
        _ABILITIES.clear()

    def test_find_by_verb(self):
        @register_ability(name="drink", verbs=["drink", "sip"])
        def test_drink_func(caller, target):
            pass

        assert find_ability_by_verb("drink") == "drink"
        assert find_ability_by_verb("sip") == "drink"

    def test_find_by_verb_case_insensitive(self):
        @register_ability(name="drink", verbs=["drink"])
        def test_drink_func(caller, target):
            pass

        assert find_ability_by_verb("DRINK") == "drink"
        assert find_ability_by_verb("Drink") == "drink"

    def test_find_by_verb_not_found(self):
        assert find_ability_by_verb("fly") is None


class TestFindAbilitiesForObject:
    def setup_method(self):
        _ABILITIES.clear()

    def _mock_obj(self, properties=None):
        obj = MagicMock()
        obj.db = MagicMock()
        obj.db.properties = properties
        return obj

    def test_find_abilities_match(self):
        @register_ability(name="drink", requires_property={"is_drinkable": "True", "current_volume_ml": ">=1"})
        def test_drink(caller, target):
            pass

        obj = self._mock_obj(properties={
            "is_drinkable": True,
            "current_volume_ml": 200,
        })
        matches = find_abilities_for_object(obj)
        assert len(matches) == 1
        assert matches[0]["name"] == "drink"

    def test_find_abilities_no_match_zero_volume(self):
        @register_ability(name="drink", requires_property={"is_drinkable": "True", "current_volume_ml": ">=1"})
        def test_drink(caller, target):
            pass

        obj = self._mock_obj(properties={
            "is_drinkable": True,
            "current_volume_ml": 0,
        })
        matches = find_abilities_for_object(obj)
        assert len(matches) == 0

    def test_find_abilities_multiple(self):
        @register_ability(name="drink", requires_property={"is_drinkable": "True"})
        def test_drink(caller, target):
            pass

        @register_ability(name="wear", requires_property={"is_wearable": "True"})
        def test_wear(caller, target):
            pass

        obj = self._mock_obj(properties={
            "is_drinkable": True,
            "is_wearable": True,
        })
        matches = find_abilities_for_object(obj)
        assert len(matches) == 2

    def test_find_abilities_empty_props(self):
        @register_ability(name="default_abil")
        def test_default(caller, target):
            pass

        obj = self._mock_obj(properties=None)
        matches = find_abilities_for_object(obj)
        assert len(matches) == 1
        assert matches[0]["name"] == "default_abil"


class TestExecuteAbility:
    def setup_method(self):
        _ABILITIES.clear()

    def test_execute_ability_success(self):
        @register_ability(name="test_abil")
        def test_func(caller, target):
            caller.msg("Test message")

        caller = MagicMock()
        target = MagicMock()
        result = execute_ability(caller, "test_abil", target)
        assert result is True
        caller.msg.assert_called()

    def test_execute_ability_not_found(self):
        caller = MagicMock()
        target = MagicMock()
        result = execute_ability(caller, "nonexistent", target)
        assert result is False
        caller.msg.assert_called_with("Unknown ability: nonexistent")

    def test_execute_ability_handler_exception(self):
        @register_ability(name="error_abil")
        def error_func(caller, target):
            raise ValueError("Test error")

        caller = MagicMock()
        target = MagicMock()
        result = execute_ability(caller, "error_abil", target)
        assert result is False


class TestVerbMap:
    def setup_method(self):
        _ABILITIES.clear()

    def test_get_verb_map(self):
        @register_ability(name="drink", verbs=["drink", "sip"])
        def test_drink(caller, target):
            pass

        @register_ability(name="wear", verbs=["wear", "don"])
        def test_wear(caller, target):
            pass

        vm = get_verb_map()
        assert vm["drink"] == "drink"
        assert vm["sip"] == "drink"
        assert vm["wear"] == "wear"
        assert vm["don"] == "wear"


class TestGetAbilities:
    def setup_method(self):
        _ABILITIES.clear()

    def test_get_abilities_empty(self):
        assert get_abilities() == {}

    def test_get_abilities_has_entries(self):
        @register_ability(name="blink")
        def test_blink(caller, target):
            pass

        abilities = get_abilities()
        assert "blink" in abilities
