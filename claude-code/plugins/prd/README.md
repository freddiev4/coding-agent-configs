# PRD Plugin

A Claude Code plugin for transforming brain dumps into structured Product Requirements Documents (PRDs) that work seamlessly with Ralph Wiggum for iterative execution.

## Overview

This plugin helps you:
1. **Brain Dump → PRD Generation**: Convert messy ideas into structured PRDs
2. **Task Breakdown**: Decompose PRDs into individual, actionable tasks with clear dependencies
3. **Ralph Integration**: Generate PRDs optimized for Ralph Wiggum's iterative execution model

## Architecture

### Design Philosophy: Loose Coupling

The PRD plugin is designed to be **Ralph-friendly** but standalone. It excels at **structure and planning** while Ralph Wiggum excels at **iterative refinement**.

### Ralph's Strength
Ralph excels at **iterative refinement** - running tests, fixing failures, retrying until done. It's best for execution loops.

### PRD Plugin's Strength
The PRD plugin excels at **structure and planning** - taking messy ideas and creating clear requirements.

## Workflow

```bash
# Step 1: Brain dump → Structured PRD
/generate-prd "I want to build a todo app with real-time sync, auth, and mobile support"

# Claude creates prd.md with:
# - Clear requirements
# - Task breakdown with dependencies
# - Success criteria
# - A completion promise section

# Step 2: Review & edit prd.md (you're in control)

# Step 3: Execute with Ralph for iterative implementation
/ralph-loop "$(cat prd.md)" --max-iterations 50 --completion-promise "PRD_COMPLETE"
```

## Why This Approach?

- **Modularity**: PRD plugin handles planning, Ralph handles execution
- **Control**: You can edit the PRD before execution starts
- **Reusability**: PRD becomes living documentation throughout the project
- **Ralph-Optimized**: Task dependencies enable Ralph to work methodically through implementation

## Commands

### /generate-prd

Generate a structured PRD from a brain dump.

**Usage:**
```bash
/generate-prd "Your idea description here..."
```

**Output**: Creates `prd.md` in project root with:
- Problem statement
- Requirements (functional & non-functional)
- Success criteria (checkboxes)
- Task breakdown with dependencies
- Completion promise for Ralph integration

**Next Steps**: After generation, review `prd.md` and execute with Ralph:
```bash
/ralph-loop "$(cat prd.md)" --max-iterations 50 --completion-promise "PRD_COMPLETE"
```

## PRD Format

The plugin generates PRDs in this format:

```markdown
# PRD: [Project Name]

## Problem Statement
[Clear description of what problem this solves]

## Requirements

### Functional Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

### Non-Functional Requirements
- [ ] Performance requirement
- [ ] Security requirement
- [ ] Testing requirement

## Success Criteria
- [ ] User authentication working
- [ ] CRUD operations for todos
- [ ] Real-time sync implemented
- [ ] Tests passing (>80% coverage)

## Completion Promise
Output: <promise>PRD_COMPLETE</promise> when all success criteria met

## Task Breakdown

### Task 1: [AUTH] Implement JWT authentication
**Description**: Implement user authentication with JWT tokens
**Dependencies**: None
**Parallelizable**: Yes

### Task 2: [API] Create todo CRUD endpoints
**Description**: Build REST API endpoints for todo operations
**Dependencies**: Task 1 (auth)
**Parallelizable**: After Task 1

### Task 3: [SYNC] Add WebSocket real-time sync
**Description**: Implement WebSocket server for real-time updates
**Dependencies**: Task 2 (API)
**Parallelizable**: After Task 2

### Task 4: [TEST] Write integration tests
**Description**: Create test suite with >80% coverage
**Dependencies**: Tasks 1, 2, 3
**Parallelizable**: After all tasks complete
```

This format works with Ralph AND standalone execution.

## Integration with Ralph Wiggum

The PRD format includes a completion promise that Ralph can detect:

```bash
# After generating and reviewing prd.md
/ralph-loop "$(cat prd.md)" --max-iterations 50 --completion-promise "PRD_COMPLETE"
```

Ralph will:
- Execute the PRD iteratively
- Run tests and fix failures
- Iterate until all success criteria are met
- Output the completion promise when done

## Best Practices

### 1. Clear Problem Statements
Start with a clear problem you're solving, not just features.

### 2. Measurable Success Criteria
Use specific, verifiable criteria (e.g., "tests passing" not "code is good").

### 3. Task Dependencies
Clearly mark which tasks depend on others for proper parallelization.

### 4. Review Before Execution
Always review the generated PRD before executing - edit as needed.

### 5. Use Ralph for Execution
Ralph's iterative loop is perfect for working through the PRD's task list, handling failures, and refining implementation.

## Examples

### Example 1: Simple Feature
```bash
/generate-prd "Add dark mode toggle to settings page"
# Review prd.md
/ralph-loop "$(cat prd.md)" --max-iterations 20 --completion-promise "PRD_COMPLETE"
```

### Example 2: Complex System
```bash
/generate-prd "Build real-time chat system with authentication, message history, file uploads, and end-to-end encryption"
# Review prd.md, adjust requirements if needed
/ralph-loop "$(cat prd.md)" --max-iterations 100 --completion-promise "PRD_COMPLETE"
# Let Ralph iterate until all requirements met
```

## How Ralph Uses the PRD

When you execute `/ralph-loop "$(cat prd.md)"`, Ralph will:

1. **Read the Task Breakdown**: Understand what needs to be built and in what order
2. **Follow Dependencies**: Work through tasks respecting the dependency chain
3. **Check Success Criteria**: Use the checkboxes to track progress
4. **Iterate Until Done**: Keep working until the completion promise is valid
5. **Self-Correct**: Fix failing tests, adjust implementation based on errors

The task dependencies help Ralph work methodically - it knows what to tackle first and what needs to wait.

## For Help

Run `/help` in Claude Code for detailed command reference and examples.
