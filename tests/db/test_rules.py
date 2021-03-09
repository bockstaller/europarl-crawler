import uuid
from datetime import datetime, timedelta, timezone

import pytest
from psycopg2 import sql

from europarl.db import Rules
from europarl.rules.rule import rule_registry


def test_table_exists(db_interface):
    rules = Rules(db_interface)
    assert rules.table_exists()


def test_table_not_exists(db_interface):
    with db_interface.cursor() as db:
        db.cur.execute(
            sql.SQL("drop table {table} cascade").format(
                table=sql.Identifier(Rules.table_name)
            )
        )

    rules = Rules(db_interface)
    assert rules.table_exists() is False


@pytest.mark.parametrize("rulenames", [rule_registry.all])
def test_register_rule_and_get_by_name_id(db_interface, rulenames):
    rules = Rules(db_interface)
    registered_rules = []

    registered_rules = rules.register_rules(rulenames)

    for original, stored_id in zip(rulenames, registered_rules):
        id_by_name, name_by_name, active_by_name = rules.get_rule(rulename=original)
        assert id_by_name == stored_id
        assert type(name_by_name) == str

        assert name_by_name == str(original)
        assert not active_by_name

        id_by_id, name_by_id, active_by_id = rules.get_rule(id=stored_id)
        assert id_by_id == stored_id
        assert type(name_by_id) == str
        assert name_by_id == str(original)
        assert not active_by_id


def test_get_rule_by_nothing(db_interface):
    rules = Rules(db_interface)

    with pytest.raises(AttributeError):
        rules.get_rule()


def test_get_non_existent_rule(db_interface):
    rules = Rules(db_interface)
    assert rules.get_rule(id=10) is None


def test_register_rule_multiple_times(db_interface):
    r = Rules(db_interface)
    id_0 = r.register_rules(rule_registry.all)
    id_1 = r.register_rules(rule_registry.all)
    assert id_0 == id_1
