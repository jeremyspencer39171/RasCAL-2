"""Tests for the terminal widget."""

from ratapi.events import ProgressEventData

from rascal2.widgets.terminal import TerminalWidget


def test_write():
    """Test that text can be successfully written to the terminal."""
    wg = TerminalWidget()
    wg.write("test text")
    assert "test text" in wg.text_area.toPlainText()


def test_append_html():
    """Test that HTML can be written to the terminal as formatted text."""
    wg = TerminalWidget()
    wg.write_html("<b>HTML bold text!</b>")
    assert "HTML bold text!" in wg.text_area.toPlainText()
    assert "<b>" not in wg.text_area.toPlainText()


def test_clear():
    """Test that the terminal clearing works."""
    wg = TerminalWidget()
    wg.write("test text")
    wg.clear()
    assert wg.text_area.toPlainText() == ""


def test_progress_bar():
    """Test that the progress bar is shown when a progress event is given."""
    wg = TerminalWidget()
    assert not wg.progress_bar.isVisibleTo(wg)

    event = ProgressEventData()
    event.percent = 0.2
    wg.update_progress(event)
    assert wg.progress_bar.isVisibleTo(wg)
    assert wg.progress_bar.value() == 20

    event.percent = 0.65
    wg.update_progress(event)
    assert wg.progress_bar.isVisibleTo(wg)
    assert wg.progress_bar.value() == 65
