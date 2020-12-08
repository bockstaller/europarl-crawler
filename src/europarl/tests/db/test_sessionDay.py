import pytest
from europarl.db.tables import SessionDay


def test_db(db_interface):
    sessionDay = SessionDay(db_interface)
    assert sessionDay.table_exists()
