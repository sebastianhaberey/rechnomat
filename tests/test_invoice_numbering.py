import pytest

from rechnomat.invoice_numbering import (
    find_highest_invoice_number,
    find_highest_matching_invoice_number,
    increment_invoice_number,
)


def test_find_highest_invoice_number_with_missing_directory(tmp_path):
    assert find_highest_invoice_number(tmp_path / "invoices") is None


def test_find_highest_invoice_number_with_empty_directory(tmp_path):
    assert find_highest_invoice_number(tmp_path) is None


def test_find_highest_invoice_number_returns_original_zero_padding(tmp_path):
    (tmp_path / "00000005.yml").touch()
    (tmp_path / "00000012.yml").touch()
    assert find_highest_invoice_number(tmp_path) == "00000012"


def test_find_highest_invoice_number_ignores_non_numeric_filenames(tmp_path):
    (tmp_path / "notes.txt").touch()
    (tmp_path / "abc.yml").touch()
    (tmp_path / "00000003.yml").touch()
    assert find_highest_invoice_number(tmp_path) == "00000003"


def test_find_highest_invoice_number_preserves_prefix_and_padding(tmp_path):
    (tmp_path / "DE-0005.yml").touch()
    (tmp_path / "DE-0012.yml").touch()
    assert find_highest_invoice_number(tmp_path) == "DE-0012"


def test_find_highest_invoice_number_ignores_filenames_with_digits_in_prefix(tmp_path):
    (tmp_path / "2024-DE-1000.yml").touch()
    (tmp_path / "DE-0003.yml").touch()
    assert find_highest_invoice_number(tmp_path) == "DE-0003"


def test_find_highest_matching_invoice_number_applies_predicate(tmp_path):
    (tmp_path / "00000005.yml").touch()
    (tmp_path / "00000012.yml").touch()
    assert find_highest_matching_invoice_number(tmp_path, lambda p: p.name == "00000005.yml") == "00000005"


def test_find_highest_matching_invoice_number_returns_none_when_nothing_matches(tmp_path):
    (tmp_path / "00000005.yml").touch()
    assert find_highest_matching_invoice_number(tmp_path, lambda _p: False) is None


def test_increment_invoice_number_preserves_padding():
    assert increment_invoice_number("DE000001") == "DE000002"


def test_increment_invoice_number_grows_beyond_original_padding():
    assert increment_invoice_number("DE9") == "DE10"


def test_increment_invoice_number_raises_without_trailing_digits():
    with pytest.raises(ValueError, match="no trailing digits"):
        increment_invoice_number("DE")
