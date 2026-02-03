# Rune CLI Specification

This document describes the behavior and architecture of the Rune Terminal User Interface (TUI). It serves as a language-agnostic specification that can be used to reimplement the CLI in any language (Rust, Go, etc.).

## Overview

The Rune CLI is a persistent, interactive terminal interface for conversing with AI agents. It provides a split-pane layout with scrollable output, real-time status updates, and keyboard-driven navigation.

## Architecture

### Layout Structure

The TUI consists of the following vertical sections (top to bottom):

1. **Header** (1 line, fixed)
   - Displays: Application name, current agent, model name
   - Format: `Rune  Agent: {agent_name}  Model: {model}`

2. **Main Content Area** (flexible height)
   - Either **Output Pane** or **Details Pane** (mutually exclusive)
   - See sections below for details

3. **Spinner Status Line** (0-2 lines, conditional)
   - Only visible when agent is actively working
   - Line 1: Spinner animation + status message
   - Line 2: Blank line (spacing)

4. **Separator** (1 line, fixed)
   - Horizontal rule character: `─`

5. **Prompt Title** (1 line, fixed)
   - Displays agent-specific prompt character
   - Format: `{agent_name} {prompt_char}`
   - Examples: `build #`, `plan ?`

6. **Input Area** (1 line, expandable)
   - User input field with left margin prompt glyph
   - Prompt glyph varies by agent (e.g., `> `, `# `, `? `)

7. **Bottom Separator** (1 line, fixed)
   - Horizontal rule character: `─`

### Output Pane

**Purpose**: Displays the conversation history between user and agent.

**Content Formatting**:
- User messages: Prefixed with `> `, styled with inverted colors (bg:white, fg:black)
- Agent responses: Prefixed with `⏺ `, normal styling
- Tool execution summaries: Prefixed with `⏺ `, format `ToolName(key_argument)`
  - Tool results indented with `⎿ ` and brief status/preview
  - Long outputs show `(Content available in details - Ctrl+O)`
- Inline code: Text wrapped in backticks rendered in rune blue (#5b9bd5) without the backticks

**Scrolling Behavior**:
- **Unlimited scrollback**: Can scroll to the very beginning of the session
- **Follow mode**: By default, auto-scrolls to show new messages
- **Manual scroll**: Disables follow mode until user returns to bottom
- **Cursor-based**: Uses buffer cursor position for precise scrolling control

**Navigation**:
- `PageUp`: Scroll up ~10 lines
- `PageDown`: Scroll down ~10 lines
- `Home`: Jump to very top of session
- `End`: Jump to bottom and re-enable follow mode
- `Mouse wheel`: Scroll up/down

### Details Pane

**Purpose**: Displays full tool execution logs without cluttering the main conversation.

**Visibility**: Hidden by default, toggled with `Ctrl+O`

**When Visible**:
- Replaces the Output Pane entirely (overlay behavior)
- Shows complete tool call arguments and full output
- Format:
  ```
  [agent_name] Tool: ToolName
    argument_1: value
    argument_2: value
    ✓ ToolName completed
    [full output content...]
  ```

**Scrolling**:
- Same navigation as Output Pane
- `PageUp/PageDown`: Scroll by ~10 lines
- `↑/↓ arrows`: Scroll by single lines
- `Home/End`: Jump to top/bottom
- `Mouse wheel`: Scroll

**Buffer Management**:
- Read-only buffer (users cannot edit)
- Cleared at the start of each new agent turn
- Temporarily made writable during updates, then locked again

### Input Area

**Behavior**:
- Multiline support (but defaults to single line)
- `Enter`: Submit when cursor at end of input
- `Shift+Tab`: Insert newline (for multiline input)
- Characters appear immediately as typed (non-blocking)
- Input cleared immediately upon submission

**Echo Behavior**:
- User input is echoed to Output Pane with `> ` prefix immediately on submit
- Blank line inserted after echoed input for spacing
- Input area clears before agent starts processing

### Spinner Status Line

**Purpose**: Provides real-time feedback on agent activity without polluting the conversation.

**Position**: Fixed location above the prompt title section (doesn't scroll away)

**Visibility**:
- Appears when agent starts processing
- Remains visible throughout all tool executions
- Disappears only when final agent response is ready

**Animation**:
- Uses spinning frames: `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`
- Updates at ~10 FPS (100ms interval)
- Frame counter increments while active

**Status Messages**:
- Default: Random action verb from thematic list + `…`
  - Runescape theme: "Smithing…", "Mining…", "Runecrafting…", etc.
  - Verbs randomly selected at spinner start
- During tool execution: `Tool: {tool_name}`
- With hidden details: Appends `(Ctrl+O for details)`

**Action Verbs** (Runescape theme):
```
Smithing, Mining, Fishing, Cooking, Woodcutting, Crafting,
Runecrafting, Firemaking, Fletching, Brewing, Slaying,
Training, Grinding, Questing, Enchanting, Alching, Thieving,
Climbing, Forging, Smelting, Casting, Conjuring
```

## Keyboard Bindings

### Global
- `Ctrl+C`, `Ctrl+D`: Exit application
- `Ctrl+O`: Toggle details pane visibility
- `Mouse wheel`: Scroll current pane

### Output Pane (when details hidden)
- `PageUp`: Scroll up 10 lines, disable follow mode
- `PageDown`: Scroll down 10 lines
- `Home`: Jump to top of session, disable follow mode
- `End`: Jump to bottom, enable follow mode, focus input

### Details Pane (when details visible)
- `PageUp`: Scroll up 10 lines
- `PageDown`: Scroll down 10 lines
- `↑`: Scroll up 1 line
- `↓`: Scroll down 1 line
- `Home`: Jump to top
- `End`: Jump to bottom
- `Ctrl+O`: Close details, return to output view

### Input Area
- `Enter`: Submit input (when cursor at end)
- `Shift+Tab`: Insert newline
- `Backspace`, `Ctrl+H`: Delete character before cursor
- Default text editing keys (arrows, home, end, delete, etc.)

## Slash Commands

Commands typed in input that start with `/` are handled locally (not sent to agent):

- `/exit`, `/quit`: Exit application
- `/reset`: Clear session history
- `/history`: Show all messages in current session
- `/status`: Display session stats (turns, tokens, working directory)
- `/agents`: List available agents
- `/switch <agent>`: Switch to different agent
- Unknown commands show error: `Unknown command: /{cmd}`

**Safety**: Bare commands without `/` prefix are rejected with reminder message.

## Agent Communication Flow

### User Submits Message

1. User types message and presses `Enter`
2. Input echoed to output pane with `> ` prefix
3. Blank line inserted for spacing
4. Input field cleared
5. Spinner starts with random verb (e.g., "Crafting…")
6. Details buffer cleared for new turn
7. Agent processing begins asynchronously

### Agent Processes (Streaming)

For each turn in the agent's streaming response:

1. **Tool Calls**:
   - Spinner updates: `Tool: {tool_name}`
   - Summary printed to output pane: `⏺ ToolName(arg)`
   - Full details written to details buffer (hidden by default)

2. **Tool Results**:
   - Success: `⎿ (brief preview or "No content")`
   - Failure: `⎿ Error: {error_message}`
   - Full output in details buffer

3. **Final Response**:
   - Spinner stops and disappears
   - Agent message printed to output: `⏺ {response}`
   - Details buffer made read-only

### Async Execution

Agent work runs in background thread/executor to prevent blocking the UI:
- UI remains responsive during processing
- User can scroll, toggle details, etc. while agent works
- Input is disabled during processing (new message awaits completion)

## Styling

### Colors (example values)
- Frame borders: `#b0b0b0` (light gray)
- Title/headers: `bold #b0b0b0`
- Prompts: `#b0b0b0`
- User input: `bg:#ffffff fg:#000000` (inverted)
- Code (backticks): `#5b9bd5` (rune blue)
- Spinner: `#b0b0b0`

### Typography
- Monospace font required
- Line wrapping enabled for output and details
- No wrapping in input (horizontal scroll if needed)

## State Management

### Follow Mode
- **Type**: Boolean flag
- **Initial**: `true`
- **Behavior**:
  - When `true`: Auto-scroll output to show latest content
  - When `false`: Manual scrolling, cursor visible
  - Set to `false` on: PageUp, Home, manual scroll up
  - Set to `true` on: End key, reaching bottom

### Details Visibility
- **Type**: Boolean flag
- **Initial**: `false`
- **Behavior**:
  - When `true`: Details pane shown, output pane hidden
  - When `false`: Output pane shown, details pane hidden
  - Toggled by: `Ctrl+O`

### Details Read-Only State
- **Type**: Boolean flag
- **Initial**: `true`
- **Behavior**:
  - Prevents accidental editing of tool logs
  - Temporarily set to `false` during buffer updates
  - Set back to `true` after updates complete

### Spinner State
- **active** (boolean): Whether spinner is currently animating
- **i** (integer): Current frame index (0-9)
- **status** (string): Current status message
- **verb** (string): Current random action verb

## Buffer Management

### Output Buffer
- Stores all conversation history
- Append-only (never delete old content)
- Plain text only (styling applied via lexer at render time)
- Cursor position used for scrolling
- Always writable (new content added continuously)

### Details Buffer
- Stores tool execution details for current turn
- Cleared at start of each new agent turn
- Read-only by default (via conditional filter)
- Temporarily writable during tool execution
- Cursor position used for scrolling

### Input Buffer
- Multiline support enabled
- Completer disabled (prevents async warnings)
- Cleared immediately on submission
- Focus returns after slash command execution

## Implementation Notes

### Lexer (Syntax Highlighting)

The output buffer uses a custom lexer that applies styling at render time:

**Rules**:
1. Lines starting with `> `: Apply `user_input` style
2. Text between backticks: Extract content, apply `code` style
3. All other text: No special styling

**Backtick Parsing Algorithm**:
```
pos = 0
while pos < line.length:
    tick_start = find("`", pos)
    if tick_start == -1:
        append remaining text
        break

    append text before tick_start

    tick_end = find("`", tick_start + 1)
    if tick_end == -1:
        append remaining text (no closing backtick)
        break

    code_content = line[tick_start + 1 : tick_end]
    append code_content with "code" style
    pos = tick_end + 1
```

### Scrolling Implementation

**Cursor-Based (Recommended)**:
- Manipulate buffer's cursor position
- Window automatically scrolls to keep cursor visible
- Allows unlimited scrollback without constraints
- Works for both output and details panes

**Vertical Scroll (Alternative)**:
- Directly modify window's `vertical_scroll` attribute
- May have platform-specific limitations
- Less precise than cursor-based approach

### Async Agent Execution

To prevent UI blocking during agent processing:

1. Define async function that:
   - Clears details buffer
   - Starts spinner
   - Yields control (small delay for UI render)
   - Runs agent.stream() in thread pool executor
   - Handles errors
   - Stops spinner

2. Schedule async function on event loop with `ensure_future()`

3. Return immediately from submit handler so UI can update

4. Agent results stream back and update UI incrementally

## Testing Checklist

### Basic Interaction
- [ ] User can type and submit messages
- [ ] User input echoes immediately with `> ` prefix
- [ ] Agent responses appear with `⏺ ` prefix
- [ ] Spinner shows while processing

### Scrolling
- [ ] Can scroll to very beginning of session (Home key)
- [ ] Can scroll to bottom (End key)
- [ ] PageUp/PageDown scroll by multiple lines
- [ ] Mouse wheel scrolling works
- [ ] Follow mode disables on scroll up
- [ ] Follow mode re-enables on End key

### Details Pane
- [ ] Ctrl+O shows details pane
- [ ] Details pane replaces output view
- [ ] Full tool arguments visible
- [ ] Full tool outputs visible
- [ ] Can scroll through all details
- [ ] Ctrl+O hides details and restores output

### Spinner
- [ ] Appears when agent starts working
- [ ] Shows random verb on start
- [ ] Updates to "Tool: X" during execution
- [ ] Stays visible through all tools
- [ ] Disappears only when final response ready
- [ ] Positioned above input area (doesn't scroll)

### Syntax Highlighting
- [ ] Backtick text renders in blue
- [ ] Backticks themselves are hidden
- [ ] User input has inverted background
- [ ] Nested backticks handled gracefully

### Slash Commands
- [ ] /exit quits application
- [ ] /reset clears session
- [ ] /history shows message log
- [ ] /status shows session stats
- [ ] Bare commands (without /) rejected

### Edge Cases
- [ ] Empty input submission ignored
- [ ] Long tool outputs truncated in summary
- [ ] Multi-line input works with Shift+Tab
- [ ] Rapid scrolling doesn't crash
- [ ] Details buffer clears between turns

## Performance Considerations

- **Scrollback Limit**: Consider limiting buffer size for very long sessions (e.g., keep last 10K lines)
- **Render Optimization**: Only re-render visible lines, not entire buffer
- **Lexer Caching**: Cache styled fragments per line if parsing is expensive
- **Async Updates**: Batch multiple tool results before invalidating UI
- **Mouse Events**: Debounce scroll events to reduce render frequency

## Accessibility

- All features keyboard-accessible (no mouse required)
- Status updates announced via spinner line (visible feedback)
- Clear visual hierarchy with borders and spacing
- High contrast text (light on dark background)
- Monospace font ensures consistent character alignment

## Future Enhancements

- **Search**: `/search <term>` to find text in history
- **Copy Mode**: Vim-style visual selection for copying
- **Themes**: Configurable color schemes
- **Split Details**: Show output and details side-by-side
- **Session Persistence**: Save/restore session state
- **Agent Streaming**: Stream partial responses as they generate
- **Multi-agent**: Multiple concurrent conversations in tabs/panes
