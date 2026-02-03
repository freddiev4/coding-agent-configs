"""Interactive multiline input widget for the Rune CLI.

This module is optional: it requires `prompt_toolkit`.

Features (when prompt_toolkit is installed):
- Full-width input area
- Multiline editing
- Newline insertion via Shift+Tab
- Backspace support (including Ctrl+H fallback)

UI tweaks:
- Leading ❯ prompt glyph inside the input area.
- Agent label (e.g. "build #") rendered flush-left above the input.
- Only top and bottom rules (no vertical box sides).

If prompt_toolkit is not installed, importing this module will raise.
"""

from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.application.current import get_app
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.margins import Margin
from prompt_toolkit.styles import Style


class _PromptGlyphMargin(Margin):
    """Left margin that renders a leading prompt glyph (❯) for each line.

    prompt_toolkit 3.0 expects Margin instances (not callables) in `left_margins`.
    """

    def get_width(self, get_ui_content) -> int:  # type: ignore[override]
        return 2

    def create_margin(self, window_render_info, width: int, height: int):  # type: ignore[override]
        # Must return a flat list of (style, text) fragments. Newlines split lines.
        # (Returning a list-of-lists will crash in prompt_toolkit's split_lines.)
        return [("class:prompt", "❯ \n") for _ in range(height)]


def prompt_boxed(prompt_title: str) -> str:
    """Prompt for user input in a full-width, multiline area.

    - Shift+Tab inserts a newline.
    - Enter accepts the input.
    """

    kb = KeyBindings()

    @kb.add("s-tab")
    def _(event) -> None:
        event.current_buffer.insert_text("\n")

    @kb.add("c-h")
    def _(event) -> None:
        event.current_buffer.delete_before_cursor(count=1)

    def _width() -> int:
        """Return the terminal width in columns.

        Note: prompt_toolkit width is in *columns* (not terminal rows/height).
        """

        try:
            return get_app().output.get_size().columns
        except Exception:
            return 80

    # Light gray styling.
    style = Style.from_dict(
        {
            "rule": "#b0b0b0",
            "label": "bold #b0b0b0",
            "prompt": "#b0b0b0",
        }
    )

    session: PromptSession[str] = PromptSession(key_bindings=kb, style=style)

    # Input control.
    buffer_control = BufferControl(buffer=session.default_buffer)

    # Only top and bottom lines (no vertical sides): implement as
    # label + horizontal rule + input + horizontal rule.
    top = Window(
        height=1,
        content=BufferControl(buffer=session.default_buffer),
    )

    label_line = Window(
        height=1,
        content=BufferControl(buffer=session.default_buffer),
    )

    # We can't easily draw a rule with BufferControl; use Window(char=...).
    top_rule = Window(height=1, char="─", style="class:rule")
    bottom_rule = Window(height=1, char="─", style="class:rule")

    title_window = Window(
        height=1,
        content=BufferControl(buffer=session.default_buffer),
    )

    # Use a dedicated Window for the title so it's flush-left.
    title_window = Window(
        height=1,
        content=None,
        style="class:label",
        always_hide_cursor=True,
    )

    # prompt_toolkit Window can take `content` only; easiest is to use `char` for
    # rules and `FormattedTextControl` for title.
    from prompt_toolkit.layout.controls import FormattedTextControl

    title_window = Window(
        height=1,
        content=FormattedTextControl(
            FormattedText([("class:label", str(prompt_title))])
        ),
        always_hide_cursor=True,
    )

    root_container = HSplit(
        [
            title_window,
            top_rule,
            Window(
                content=buffer_control,
                wrap_lines=True,
                left_margins=[_PromptGlyphMargin()],
            ),
            bottom_rule,
        ],
        width=_width,
    )

    session.app.layout = Layout(root_container)
    return session.prompt("")
