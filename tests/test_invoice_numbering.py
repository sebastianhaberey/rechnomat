from rechnomat.invoice_numbering import find_highest_invoice_number, next_invoice_number


def test_next_invoice_number_with_missing_directory(tmp_path):
    assert next_invoice_number(tmp_path / "invoices") == "00000001"


def test_next_invoice_number_with_empty_directory(tmp_path):
    assert next_invoice_number(tmp_path) == "00000001"


def test_next_invoice_number_increments_and_preserves_width(tmp_path):
    (tmp_path / "00000000.yml").touch()
    (tmp_path / "00000001.yml").touch()
    assert next_invoice_number(tmp_path) == "00000002"


def test_next_invoice_number_uses_width_of_highest_file(tmp_path):
    (tmp_path / "00001.yml").touch()
    assert next_invoice_number(tmp_path) == "00002"


def test_next_invoice_number_ignores_non_numeric_filenames(tmp_path):
    (tmp_path / "notes.txt").touch()
    (tmp_path / "abc.yml").touch()
    (tmp_path / "00003.yml").touch()
    assert next_invoice_number(tmp_path) == "00004"


def test_next_invoice_number_grows_width_on_overflow(tmp_path):
    (tmp_path / "99999.yml").touch()
    assert next_invoice_number(tmp_path) == "100000"


def test_next_invoice_number_picks_highest_by_value_not_string_order(tmp_path):
    (tmp_path / "0000009.yml").touch()
    (tmp_path / "0000010.yml").touch()
    assert next_invoice_number(tmp_path) == "0000011"


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
