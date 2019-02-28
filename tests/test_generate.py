import pytest

from pymongo_migrate.generate import slugify


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("My comment", "my_comment"),
        ("counting: 1, 2, 3", "counting_1_2_3"),
        ("wat?!", "wat"),
        ("mały żółwik", "may_wik"),
    ],
)
def test_slugify(test_input, expected):
    assert slugify(test_input) == expected
