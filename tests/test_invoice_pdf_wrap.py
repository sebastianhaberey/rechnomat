from reportlab.pdfbase.pdfmetrics import stringWidth

from rechnomat.invoice_pdf import wrap_text

FONT = "Helvetica"
SIZE = 10


def test_wrap_text_returns_single_line_when_short_enough():
    text = "Sehr geehrte Damen und Herren,"
    assert wrap_text(text, font=FONT, size=SIZE, max_width=1000) == [text]


def test_wrap_text_splits_into_multiple_lines_that_fit_max_width():
    text = "Bitte überweisen Sie den Rechnungsbetrag bis zum 29.08.2026 unter Angabe der Rechnungsnummer 00000001"
    max_width = 200

    lines = wrap_text(text, font=FONT, size=SIZE, max_width=max_width)

    assert len(lines) > 1
    for line in lines:
        assert stringWidth(line, FONT, SIZE) <= max_width
    assert " ".join(lines) == text


def test_wrap_text_keeps_overlong_single_word_on_its_own_line():
    text = "Supercalifragilisticexpialidocious"
    assert wrap_text(text, font=FONT, size=SIZE, max_width=10) == [text]


def test_wrap_text_handles_empty_string():
    assert wrap_text("", font=FONT, size=SIZE, max_width=1000) == [""]


def test_wrap_text_preserves_explicit_line_breaks():
    text = "Vielen Dank für Ihren Auftrag.\nMit freundlichen Grüßen"
    assert wrap_text(text, font=FONT, size=SIZE, max_width=1000) == [
        "Vielen Dank für Ihren Auftrag.",
        "Mit freundlichen Grüßen",
    ]


def test_wrap_text_preserves_blank_lines_between_paragraphs():
    text = "Erster Absatz.\n\nZweiter Absatz."
    assert wrap_text(text, font=FONT, size=SIZE, max_width=1000) == [
        "Erster Absatz.",
        "",
        "Zweiter Absatz.",
    ]


def test_wrap_text_word_wraps_each_explicit_line_independently():
    long_paragraph = "Bitte überweisen Sie den Rechnungsbetrag bis zum 29.08.2026 unter Angabe der Rechnungsnummer"
    text = f"{long_paragraph}\nVielen Dank"
    max_width = 200

    lines = wrap_text(text, font=FONT, size=SIZE, max_width=max_width)

    assert lines[-1] == "Vielen Dank"
    assert len(lines) > 2
    for line in lines:
        assert stringWidth(line, FONT, SIZE) <= max_width
    assert " ".join(lines[:-1]) == long_paragraph
