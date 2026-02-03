"""Persistent prompt_toolkit TUI for Rune.

This provides a two-pane interface:
- Scrollable output log (top)
- Fixed multiline input box (bottom)

It is optional and enabled via a CLI flag.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Optional

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.layout.containers import ScrollOffsets
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.margins import Margin
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea
from rune.agents import list_agents


class _OutputPTKLexer(Lexer):
    """prompt_toolkit-native lexer for the output buffer.

    We can't persist styled fragments in a Buffer, so we style at render time.
    Any line that starts with "> " is treated as echoed user input.
    """

    def lex_document(self, document):  # type: ignore[override]
        def get_line(lineno: int):
            try:
                line = document.lines[lineno]
            except Exception:
                return []

            if line.startswith("> "):
                return [("class:user_input", line)]
            return [("", line)]

        return get_line


class _PromptGlyphMargin(Margin):
    """Left margin that shows a prompt glyph only on the first visible line."""

    def __init__(self, prompt="❯ ") -> None:
        # `prompt` can be a string or a callable returning a string.
        self._prompt = prompt

    @property
    def prompt(self) -> str:
        p = self._prompt
        return p() if callable(p) else p

    def get_width(self, get_ui_content) -> int:  # type: ignore[override]
        return len(self.prompt)

    def create_margin(self, window_render_info, width: int, height: int):  # type: ignore[override]
        # Return a flat list of fragments; newlines split into margin lines.
        # Only show the prompt on the first line; indent subsequent wrapped lines.
        fragments = [("class:prompt", self.prompt + "\n")]
        pad = " " * len(self.prompt)
        fragments.extend([("class:prompt", pad + "\n") for _ in range(max(0, height - 1))])
        return fragments


@dataclass
class TuiPrinter:
    """A minimal 'printer' that appends text into a TextArea."""

    output: TextArea
    app: Application
    follow_mode: dict[str, bool]

    def print(self, text: str = "") -> None:
        buf = self.output.buffer
        buf.insert_text(text + "\n", move_cursor=True)
        # Keep cursor at end so the output window can follow.
        self.output.buffer.cursor_position = len(self.output.text)
        # Anchor view to bottom by default.
        try:
            self.output.window.vertical_scroll = 10**9  # type: ignore[attr-defined]
        except Exception:
            pass
        if self.follow_mode.get("enabled", True):
            try:
                self.output.control.move_cursor_to_end()
            except Exception:
                pass
        self.app.invalidate()

    def print_fragments(self, fragments) -> None:
        """Append formatted-text fragments to the output buffer.

        NOTE: prompt_toolkit Buffers store plain text only, so styles in fragments
        cannot be persisted. This method therefore de-styles fragments.
        Prefer `print()` and rely on the output lexer for styling.
        """
        from prompt_toolkit.formatted_text import fragment_list_to_text

        self.print(fragment_list_to_text(fragments))


def run_tui(agent) -> None:
    """Run Rune in a persistent TUI.

    The `agent` is expected to be rune.harness.agent.Agent.
    """

    style = Style.from_dict(
        {
            "frame.border": "#b0b0b0",
            "title": "bold #b0b0b0",
            "prompt": "#b0b0b0",
            "status": "#b0b0b0",
            "user_input": "bg:#ffffff fg:#000000",
            # Used when we print formatted fragments directly.
            "user_input": "bg:#ffffff fg:#000000",
        }
    )

    kb = KeyBindings()

    # Output area.
    # Use an explicit BufferControl with a Pygments lexer so styling is applied to
    # the control that is actually rendered in the Window.
    output_buffer = Buffer()
    output_control = BufferControl(
        buffer=output_buffer,
        lexer=_OutputPTKLexer(),
        focusable=True,
    )
    output_window = Window(
        content=output_control,
        wrap_lines=True,
        always_hide_cursor=True,
        scroll_offsets=ScrollOffsets(top=1, bottom=1),
    )

    # Keep a lightweight TextArea wrapper for existing code paths that expect
    # `.buffer`, `.text`, and `.control`.
    output = TextArea(text="", focusable=True)
    output.buffer = output_buffer  # type: ignore[attr-defined]
    output.control = output_control  # type: ignore[attr-defined]

    follow_mode: dict[str, bool] = {"enabled": True}

    # Multiline input buffer.
    # Disable completer to avoid coroutine warnings in some prompt_toolkit versions.
    input_buffer = Buffer(multiline=True, completer=None)

    def _prompt_char() -> str:
        return {"build": "#", "plan": "?"}.get(agent.agent_def.name, ">")

    def _prompt_title() -> str:
        return f"{agent.agent_def.name} {_prompt_char()}"

    input_control = BufferControl(buffer=input_buffer)
    input_window = Window(
        content=input_control,
        height=1,
        wrap_lines=False,
        left_margins=[_PromptGlyphMargin(lambda: f"{_prompt_char()} ")],
    )

    header = FormattedTextControl(
        text=lambda: [
            ("class:title", "Rune"),
            ("", "  "),
            ("class:status", f"Agent: {agent.agent_def.name}  Model: {agent.config.model}"),
        ]
    )

    root = HSplit(
        [
            Window(header, height=1),
            output_window,
            Window(height=1, char="─", style="class:frame.border"),
            Window(FormattedTextControl(lambda: [("class:prompt", _prompt_title())]), height=1),
            input_window,
            Window(height=1, char="─", style="class:frame.border"),
        ]
    )

    layout = Layout(root, focused_element=input_window)

    app: Application

    printer_holder: dict[str, Optional[TuiPrinter]] = {"p": None}

    def _append_agent_turn(turn) -> None:
        p = printer_holder["p"]
        if p is None:
            return

        for i, tool_call in enumerate(turn.tool_calls):
            try:
                args = json.loads(tool_call["function"]["arguments"])
            except Exception:
                args = {"arguments": tool_call["function"].get("arguments")}
            p.print(f"[{turn.agent_name}] Tool: {tool_call['function']['name']}")
            for k, v in (args or {}).items():
                p.print(f"  {k}: {v}")
            if i < len(turn.tool_results):
                tr = turn.tool_results[i]
                if tr.success:
                    p.print(f"  ✓ {tool_call['function']['name']} completed")
                    if tr.output:
                        p.print(str(tr.output))
                else:
                    p.print(f"  ✗ {tool_call['function']['name']} failed: {tr.error}")

        if turn.finished and turn.response:
            p.print(str(turn.response))

    def _submit() -> None:
        text = input_buffer.text.strip()
        if not text:
            return

        # Slash commands are handled by the UI (not sent to the agent).
        if text.startswith("/"):
            cmdline = text[1:].strip()
            cmd, *rest = cmdline.split(None, 1)
            arg = rest[0] if rest else ""

            # Clear input immediately for commands.
            input_buffer.text = ""

            p = printer_holder["p"]
            if p is not None:
                p.print(f"> {text}")
                p.print("")

            if cmd in {"exit", "quit"}:
                app.exit(result=None)
                return
            if cmd == "reset":
                agent.reset()
                if p is not None:
                    p.print("Session reset.")
                return
            if cmd == "history":
                if p is not None:
                    for msg in agent.session.messages:
                        content = (msg.content or "").replace("\n", " ")
                        if len(content) > 200:
                            content = content[:200] + "..."
                        p.print(f"{msg.role}: {content}")
                return
            if cmd == "status":
                s = agent.session
                if p is not None:
                    p.print(f"Session: {s.session_id}")
                    p.print(f"Turns: {s.turn_count}")
                    p.print(f"Messages: {len(s.messages)}")
                    p.print(
                        f"Tokens: {s.usage.total_tokens} (prompt: {s.usage.prompt_tokens}, completion: {s.usage.completion_tokens})"
                    )
                    p.print(f"Working Dir: {s.working_dir}")
                return
            if cmd == "agents":
                if p is not None:
                    p.print("Available agents:")
                    for ag in list_agents():
                        marker = " *" if ag.name == agent.agent_def.name else ""
                        p.print(f"  - {ag.name}{marker}: {ag.description}")
                return
            if cmd == "switch":
                new_name = arg.strip()
                if not new_name:
                    if p is not None:
                        p.print("Usage: /switch <agent>")
                    return
                try:
                    agent.switch_agent(new_name)
                    if p is not None:
                        p.print(f"Switched to {new_name} agent.")
                except ValueError as e:
                    if p is not None:
                        p.print(str(e))
                return

            if p is not None:
                p.print(f"Unknown command: /{cmd}")
            return

        # Non-slash commands must not look like bare commands.
        if text in {"exit", "reset", "history", "agents", "status"} or text.startswith("switch "):
            p = printer_holder["p"]
            if p is not None:
                p.print(f"> {text}")
                p.print("")
                p.print("Commands must start with '/'.")
            input_buffer.text = ""
            return

        # Echo user input into output pane.
        p = printer_holder["p"]
        if p is not None:
            p.print(f"> {text}")
            # Ensure exactly one blank line between the user message and the
            # agent/tool output that follows.
            p.print("")

        input_buffer.text = ""

        try:
            for turn in agent.stream(text):
                _append_agent_turn(turn)
        except Exception as e:
            if p is not None:
                p.print(f"Error: {e}")

    @kb.add("enter", filter=Condition(lambda: True))
    def _(event) -> None:
        # Enter submits when cursor is on last line and not preceded by a backslash.
        # Otherwise insert newline.
        buf = event.app.current_buffer
        doc = buf.document
        if doc.is_cursor_at_the_end:
            _submit()
        else:
            buf.insert_text("\n")

    @kb.add("s-tab")
    def _(event) -> None:
        # Shift+Tab inserts newline (always).
        event.app.current_buffer.insert_text("\n")

    @kb.add("c-c")
    @kb.add("c-d")
    def _(event) -> None:
        event.app.exit(result=None)

    # Output scrolling + follow mode.
    @kb.add("pageup")
    def _(event) -> None:
        follow_mode["enabled"] = False
        event.app.layout.focus(output_window)
        output_window.vertical_scroll -= 1

    @kb.add("pagedown")
    def _(event) -> None:
        event.app.layout.focus(output_window)
        output_window.vertical_scroll += 1

    @kb.add("end")
    def _(event) -> None:
        # Resume follow mode and jump to bottom.
        follow_mode["enabled"] = True
        event.app.layout.focus(input_window)
        try:
            output.control.move_cursor_to_end()
        except Exception:
            pass
        event.app.invalidate()

    app = Application(layout=layout, key_bindings=kb, style=style, full_screen=False)
    printer_holder["p"] = TuiPrinter(output=output, app=app, follow_mode=follow_mode)

    # Initial header/help. (Defer until the app is running; Buffer.insert_text
    # calls get_app() internally and requires an active prompt_toolkit app.)
    initial_help = "Commands: /exit, /reset, /history, /switch <agent>, /agents, /status"

    async def _run() -> None:
        """Run the prompt_toolkit app.

        On some Python/prompt_toolkit combinations (notably Python 3.13), PTK can
        surface `RuntimeError: no running event loop` from internal callbacks.
        Running the app in a dedicated task keeps the loop active for the full
        lifetime of the UI.
        """

        app_task = asyncio.create_task(app.run_async())
        # Now that the app is running, it's safe to write into buffers.
        printer_holder["p"].print(initial_help)
        try:
            await app_task
        finally:
            if not app_task.done():
                app.exit(result=None)
                await app_task

    try:
        asyncio.run(_run())
    finally:
        agent.shutdown()
