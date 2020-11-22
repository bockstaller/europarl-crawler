import pytest
from europarl.db.interface import get_all_subclasses


def test_get_all_subclasses():
    class BaseClass:
        pass

    class SubClass1(BaseClass):
        pass

    class SubClass2(BaseClass):
        pass

    class SubSubClass1(SubClass1):
        pass

    class NormalClass:
        pass

    actual = get_all_subclasses(BaseClass)
    expected = [
        SubClass1,
        SubSubClass1,
        SubClass2,
    ]
    print(actual)

    assert set(actual) == set(expected)
