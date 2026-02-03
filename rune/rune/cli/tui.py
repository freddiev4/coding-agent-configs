"""Persistent prompt_toolkit TUI for Rune.

This provides a two-pane interface:
- Scrollable output log (top)
- Fixed multiline input box (bottom)

It is optional and enabled via a CLI flag.
"""

from __future__ import annotations

import asyncio
import json
import random
from dataclasses import dataclass
from typing import Optional

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.key_binding.bindings.basic import load_basic_bindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.containers import ConditionalContainer, ScrollOffsets
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.margins import Margin
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea
from rune.agents import list_agents


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Runescape-themed action verbs for spinner status
_RUNE_VERBS = [
    "Smithing",
    "Mining",
    "Fishing",
    "Cooking",
    "Woodcutting",
    "Crafting",
    "Runecrafting",
    "Firemaking",
    "Fletching",
    "Brewing",      # Herblore
    "Slaying",
    "Training",
    "Grinding",
    "Questing",
    "Enchanting",
    "Alching",
    "Thieving",
    "Climbing",     # Agility
    "Forging",
    "Smelting",
    "Casting",
    "Conjuring",
]


class _OutputPTKLexer(Lexer):
    """prompt_toolkit-native lexer for the output buffer.

    We can't persist styled fragments in a Buffer, so we style at render time.
    Any line that starts with "> " is treated as echoed user input.
    Text wrapped in backticks is styled as inline code.
    """

    def lex_document(self, document):  # type: ignore[override]
        def get_line(lineno: int):
            try:
                line = document.lines[lineno]
            except Exception:
                return []

            if line.startswith("> "):
                return [("class:user_input", line)]

            # Parse backtick-wrapped code (remove backticks, style the content)
            fragments = []
            pos = 0
            while pos < len(line):
                # Find next backtick
                tick_start = line.find("`", pos)
                if tick_start == -1:
                    # No more backticks, add rest of line
                    if pos < len(line):
                        fragments.append(("", line[pos:]))
                    break

                # Add text before backtick
                if tick_start > pos:
                    fragments.append(("", line[pos:tick_start]))

                # Find closing backtick
                tick_end = line.find("`", tick_start + 1)
                if tick_end == -1:
                    # No closing backtick, treat as normal text
                    fragments.append(("", line[tick_start:]))
                    break

                # Add backtick-wrapped text as code (without the backticks)
                code_content = line[tick_start + 1:tick_end]
                fragments.append(("class:code", code_content))
                pos = tick_end + 1

            return fragments if fragments else [("", line)]

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
            "code": "#5b9bd5",  # Rune blue for backtick-wrapped code
            "spinner": "#b0b0b0",  # Spinner status line
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
    show_details: dict[str, bool] = {"enabled": False}  # Toggle with Ctrl+O
    details_readonly: dict[str, bool] = {"enabled": True}  # Control read-only state

    # Details pane for tool calls/results (scrollable, shows everything)
    # When visible, it overlays the output pane
    details_buffer = Buffer(read_only=Condition(lambda: details_readonly["enabled"]))
    details_control = BufferControl(
        buffer=details_buffer,
        focusable=True,
        focus_on_click=True,
    )
    details_window = Window(
        content=details_control,
        wrap_lines=True,
        # No height constraint - let it fill available space
        scroll_offsets=ScrollOffsets(top=1, bottom=1),
    )

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

    # Spinner status line (fixed at bottom, just above input)
    def _spinner_text():
        if not spinner.get("active"):
            return []
        status = str(spinner.get("status") or "Working…")
        if not show_details["enabled"] and details_buffer.text.strip():
            status += " (Ctrl+O for details)"
        frame = _SPINNER_FRAMES[int(spinner.get("i", 0)) % len(_SPINNER_FRAMES)]
        return [("class:spinner", f"{frame} {status}")]

    spinner_status = FormattedTextControl(text=_spinner_text)

    # Conditionally show details pane when toggled (fills most of the screen)
    details_pane = ConditionalContainer(
        HSplit([
            Window(
                FormattedTextControl(lambda: [("class:title", "Tool Details (Ctrl+O to hide, ↑↓/PgUp/PgDn to scroll, Home/End to jump)")]),
                height=1,
            ),
            Window(height=1, char="─", style="class:frame.border"),
            details_window,
            Window(height=1, char="─", style="class:frame.border"),
        ]),
        filter=Condition(lambda: show_details["enabled"]),
    )

    # When details are shown, minimize output window; otherwise show it normally
    output_container = ConditionalContainer(
        output_window,
        filter=Condition(lambda: not show_details["enabled"]),
    )

    # Spinner status line with spacing (only visible when active)
    spinner_container = ConditionalContainer(
        HSplit([
            Window(spinner_status, height=1),
            Window(height=1),  # Blank line for spacing
        ]),
        filter=Condition(lambda: spinner.get("active", False)),
    )

    root = HSplit(
        [
            Window(header, height=1),
            output_container,  # Hidden when details shown
            details_pane,      # Visible when toggled, takes up output space
            spinner_container,  # Fixed spinner status line with spacing (only when active)
            Window(height=1, char="─", style="class:frame.border"),
            Window(FormattedTextControl(lambda: [("class:prompt", _prompt_title())]), height=1),
            input_window,
            Window(height=1, char="─", style="class:frame.border"),
        ]
    )

    layout = Layout(root, focused_element=input_window)

    app: Application

    printer_holder: dict[str, Optional[TuiPrinter]] = {"p": None}

    # Spinner state (rendered in the output pane).
    # We also use the spinner line as a lightweight "status" line that can show
    # the most recent tool call / work item while the agent is running.
    spinner: dict[str, object] = {
        "active": False,
        "i": 0,
        "task": None,
        "line": "",
        "status": random.choice(_RUNE_VERBS) + "…",
        "verb": random.choice(_RUNE_VERBS),  # Current Runescape-themed verb
    }

    def _set_spinner_status(status: str) -> None:
        """Update the spinner status text.

        The animation loop will pick this up and rewrite the spinner line.
        """
        spinner["status"] = status or (spinner.get("verb", "Working") + "…")

    def _start_spinner() -> None:
        """Start the spinner animation in the fixed status line."""
        if spinner.get("active"):
            return
        spinner["active"] = True
        spinner["i"] = int(spinner.get("i", 0))
        # Pick a new random Runescape verb each time
        spinner["verb"] = random.choice(_RUNE_VERBS)
        spinner["status"] = spinner["verb"] + "…"
        try:
            app.invalidate()
        except Exception:
            pass

    def _stop_spinner() -> None:
        """Stop the spinner animation and hide the status line."""
        if not spinner.get("active"):
            return
        spinner["active"] = False
        spinner["i"] = 0
        try:
            app.invalidate()
        except Exception:
            pass

    def _append_agent_turn(turn) -> None:
        # While the agent is working, update spinner status and write details to details pane.
        # Also write a summary to the main output pane.
        # Spinner stays active until the final response is ready.
        p = printer_holder["p"]
        if p is None:
            return

        # Make details buffer writable for updates
        details_readonly["enabled"] = False

        for i, tool_call in enumerate(turn.tool_calls):
            try:
                args = json.loads(tool_call["function"]["arguments"])
            except Exception:
                args = {"arguments": tool_call["function"].get("arguments")}
            tool_name = tool_call["function"]["name"]
            _set_spinner_status(f"Tool: {tool_name}")

            # Get the most relevant argument for the summary
            summary_arg = None
            if "command" in args:
                summary_arg = args["command"]
            elif "file_path" in args:
                summary_arg = args["file_path"]
            elif "pattern" in args:
                summary_arg = args["pattern"]
            elif "prompt" in args:
                summary_arg = args["prompt"][:50] + "..." if len(str(args.get("prompt", ""))) > 50 else args.get("prompt")

            # Write summary to main output (always visible)
            if summary_arg:
                p.print(f"⏺ {tool_name}({summary_arg})")
            else:
                p.print(f"⏺ {tool_name}")

            # Write full details to details buffer
            details_buffer.insert_text(f"[{turn.agent_name}] Tool: {tool_name}\n")
            for k, v in (args or {}).items():
                details_buffer.insert_text(f"  {k}: {v}\n")

            if i < len(turn.tool_results):
                tr = turn.tool_results[i]
                if tr.success:
                    _set_spinner_status(f"Tool: {tool_name} ✓")

                    # Summary in main output
                    if tr.output:
                        output_preview = str(tr.output).strip()
                        if len(output_preview) > 100:
                            output_preview = "(Content available in details - Ctrl+O)"
                        elif not output_preview:
                            output_preview = "(No content)"
                        p.print(f"  ⎿ {output_preview}")
                    else:
                        p.print(f"  ⎿ (No content)")

                    # Full details in details buffer
                    details_buffer.insert_text(f"  ✓ {tool_name} completed\n")
                    if tr.output:
                        details_buffer.insert_text(f"{tr.output}\n")
                else:
                    _set_spinner_status(f"Tool: {tool_name} ✗")

                    # Summary in main output
                    p.print(f"  ⎿ Error: {tr.error}")

                    # Full details in details buffer
                    details_buffer.insert_text(f"  ✗ {tool_name} failed: {tr.error}\n")

            p.print("")  # Blank line after each tool
            details_buffer.insert_text("\n")

        # Make details buffer read-only again
        details_readonly["enabled"] = True

        if turn.finished and turn.response:
            # Final response: stop spinner and print the agent message with ⏺ prefix.
            _stop_spinner()
            _set_spinner_status("Working…")
            p.print(f"⏺ {turn.response}")

    def _submit() -> None:
        text = input_buffer.text.strip()
        if not text:
            return

        # Echo the user's input immediately so it's clear the message was sent,
        # then force a UI refresh before doing any potentially long-running work.
        p = printer_holder["p"]
        if p is not None:
            p.print(f"> {text}")
            # Ensure exactly one blank line between the user message and the
            # agent/tool output that follows.
            p.print("")

        # Clear input immediately.
        input_buffer.text = ""
        try:
            app.invalidate()
        except Exception:
            pass

        # Slash commands are handled by the UI (not sent to the agent).
        if text.startswith("/"):
            _stop_spinner()
            cmdline = text[1:].strip()
            cmd, *rest = cmdline.split(None, 1)
            arg = rest[0] if rest else ""


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
            _stop_spinner()
            p = printer_holder["p"]
            if p is not None:
                p.print("Commands must start with '/'.")
            return

        # Schedule the agent work to run asynchronously so UI can update first
        async def _run_agent():
            # Clear previous turn details (temporarily make buffer writable)
            details_readonly["enabled"] = False
            details_buffer.text = ""
            details_readonly["enabled"] = True

            # Start spinner while the agent is working.
            _start_spinner()

            # Small delay to let UI render the echoed input and spinner
            await asyncio.sleep(0.05)

            try:
                # Run agent.stream() in a thread pool to avoid blocking the event loop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _process_agent_stream, text)
            except Exception as e:
                _stop_spinner()
                if p is not None:
                    p.print(f"Error: {e}")
            finally:
                _stop_spinner()

        def _process_agent_stream(prompt: str):
            """Process agent stream in a background thread."""
            try:
                for turn in agent.stream(prompt):
                    _append_agent_turn(turn)
            except Exception as e:
                raise

        # Schedule the async work
        try:
            loop = asyncio.get_running_loop()
            asyncio.ensure_future(_run_agent())
        except Exception:
            # Fallback to synchronous if we can't get the loop
            _start_spinner()
            try:
                for turn in agent.stream(text):
                    _append_agent_turn(turn)
            except Exception as e:
                _stop_spinner()
                if p is not None:
                    p.print(f"Error: {e}")
            finally:
                _stop_spinner()

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

    @kb.add("c-o")
    def _(event) -> None:
        """Toggle details pane visibility."""
        show_details["enabled"] = not show_details["enabled"]
        # If showing details, focus the details window for scrolling
        if show_details["enabled"]:
            try:
                event.app.layout.focus(details_window)
            except Exception:
                pass
        else:
            # When hiding, return focus to input
            try:
                event.app.layout.focus(input_window)
            except Exception:
                pass
        try:
            event.app.invalidate()
        except Exception:
            pass

    @kb.add("c-c")
    @kb.add("c-d")
    def _(event) -> None:
        event.app.exit(result=None)

    # Smart scrolling - scroll details pane if visible, otherwise scroll output
    @kb.add("pageup")
    def _(event) -> None:
        """Scroll up - details pane if visible, otherwise output."""
        if show_details["enabled"]:
            try:
                # Scroll by moving cursor up multiple lines
                for _ in range(10):
                    cursor_up = details_buffer.document.get_cursor_up_position()
                    if cursor_up:
                        details_buffer.cursor_position = max(0, details_buffer.cursor_position + cursor_up)
                    else:
                        break
                event.app.invalidate()
            except Exception as e:
                pass
        else:
            follow_mode["enabled"] = False
            try:
                # Scroll output by moving cursor up multiple lines
                for _ in range(10):
                    cursor_up = output_buffer.document.get_cursor_up_position()
                    if cursor_up:
                        output_buffer.cursor_position = max(0, output_buffer.cursor_position + cursor_up)
                    else:
                        break
                event.app.invalidate()
            except Exception:
                pass

    @kb.add("pagedown")
    def _(event) -> None:
        """Scroll down - details pane if visible, otherwise output."""
        if show_details["enabled"]:
            try:
                # Scroll by moving cursor down multiple lines
                for _ in range(10):
                    cursor_down = details_buffer.document.get_cursor_down_position()
                    if cursor_down:
                        details_buffer.cursor_position = min(
                            len(details_buffer.text),
                            details_buffer.cursor_position + cursor_down
                        )
                    else:
                        break
                event.app.invalidate()
            except Exception as e:
                pass
        else:
            try:
                # Scroll output by moving cursor down multiple lines
                for _ in range(10):
                    cursor_down = output_buffer.document.get_cursor_down_position()
                    if cursor_down:
                        output_buffer.cursor_position = min(
                            len(output_buffer.text),
                            output_buffer.cursor_position + cursor_down
                        )
                    else:
                        break
                event.app.invalidate()
            except Exception:
                pass

    # Navigation - Home/End work for both details pane and output pane
    @kb.add("home")
    def _(event) -> None:
        """Jump to top of details pane or output pane."""
        if show_details["enabled"]:
            try:
                details_buffer.cursor_position = 0
                event.app.invalidate()
            except Exception:
                pass
        else:
            follow_mode["enabled"] = False
            try:
                output_buffer.cursor_position = 0
                event.app.invalidate()
            except Exception:
                pass

    @kb.add("end", filter=Condition(lambda: show_details["enabled"]))
    def _(event) -> None:
        """Jump to bottom of details pane."""
        if show_details["enabled"]:
            try:
                details_buffer.cursor_position = len(details_buffer.text)
                event.app.invalidate()
            except Exception:
                pass

    @kb.add("up", filter=Condition(lambda: show_details["enabled"]))
    def _(event) -> None:
        """Scroll up one line in details pane."""
        if show_details["enabled"]:
            try:
                cursor_up = details_buffer.document.get_cursor_up_position()
                if cursor_up:
                    details_buffer.cursor_position = max(0, details_buffer.cursor_position + cursor_up)
                event.app.invalidate()
            except Exception:
                pass

    @kb.add("down", filter=Condition(lambda: show_details["enabled"]))
    def _(event) -> None:
        """Scroll down one line in details pane."""
        if show_details["enabled"]:
            try:
                cursor_down = details_buffer.document.get_cursor_down_position()
                if cursor_down:
                    details_buffer.cursor_position = min(
                        len(details_buffer.text),
                        details_buffer.cursor_position + cursor_down
                    )
                event.app.invalidate()
            except Exception:
                pass

    @kb.add("end", filter=Condition(lambda: not show_details["enabled"]))
    def _(event) -> None:
        """Resume follow mode and jump to bottom (when details not shown)."""
        follow_mode["enabled"] = True
        event.app.layout.focus(input_window)
        try:
            output.control.move_cursor_to_end()
        except Exception:
            pass
        event.app.invalidate()

    # Merge our custom key bindings with the default basic bindings (for text input)
    all_bindings = merge_key_bindings([
        load_basic_bindings(),
        kb,
    ])

    app = Application(
        layout=layout,
        key_bindings=all_bindings,
        style=style,
        full_screen=False,
        mouse_support=True,  # Enable mouse/trackpad scrolling
    )
    printer_holder["p"] = TuiPrinter(output=output, app=app, follow_mode=follow_mode)

    # Initial header/help. (Defer until the app is running; Buffer.insert_text
    # calls get_app() internally and requires an active prompt_toolkit app.)
    initial_help = "Commands: /exit, /reset, /history, /switch <agent>, /agents, /status\nCtrl+O: Toggle details | ↑↓: Scroll line | PgUp/PgDn: Scroll page | Home/End: Jump | Ctrl+C: Exit"

    async def _run() -> None:
        """Run the prompt_toolkit app.

        On some Python/prompt_toolkit combinations (notably Python 3.13), PTK can
        surface `RuntimeError: no running event loop` from internal callbacks.
        Running the app in a dedicated task keeps the loop active for the full
        lifetime of the UI.
        """

        async def _spinner_loop() -> None:
            # Animate the spinner by incrementing the frame counter.
            while True:
                await asyncio.sleep(0.1)
                if spinner.get("active"):
                    spinner["i"] = int(spinner.get("i", 0)) + 1
                    try:
                        app.invalidate()
                    except Exception:
                        pass

        app_task = asyncio.create_task(app.run_async())
        spinner_task = asyncio.create_task(_spinner_loop())
        spinner["task"] = spinner_task

        # Now that the app is running, it's safe to write into buffers.
        printer_holder["p"].print(initial_help)
        try:
            await app_task
        finally:
            spinner_task.cancel()
            try:
                await spinner_task
            except Exception:
                pass
            if not app_task.done():
                app.exit(result=None)
                await app_task

    try:
        asyncio.run(_run())
    finally:
        agent.shutdown()
