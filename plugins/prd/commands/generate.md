---
description: "Generate structured PRD from brain dump"
argument-hint: "BRAIN_DUMP"
---

# Generate PRD Command

You will transform the user's brain dump into a structured Product Requirements Document (PRD).

## User's Brain Dump

$ARGUMENTS

## Your Task

Create a comprehensive PRD file named `prd.md` in the project root with the following structure:

### Required Sections

1. **PRD Title**: `# PRD: [Extract project name from brain dump]`

2. **Problem Statement**: Clear description of what problem this solves (not just features)

3. **Requirements**:
   - Functional Requirements (checkboxes)
   - Non-Functional Requirements (checkboxes for performance, security, testing, etc.)

4. **Success Criteria**: Specific, measurable, verifiable checkboxes

5. **Completion Promise**:
   ```
   ## Completion Promise
   Output: <promise>PRD_COMPLETE</promise> when all success criteria met
   ```

6. **Task Breakdown**: Break down into individual tasks with:
   - Task number and tag (e.g., `### Task 1: [AUTH] Implement JWT authentication`)
   - **Description**: What needs to be done
   - **Dependencies**: Which tasks must complete first (use "None" or "Task X")
   - **Parallelizable**: Yes/No or "After Task X"

### Task Breakdown Guidelines

- Identify logical dependencies between tasks
- Group independent tasks that can run in parallel
- Be specific about what each task accomplishes
- Use clear tags like [AUTH], [API], [UI], [TEST], [DOCS]

### Success Criteria Guidelines

- Make criteria specific and verifiable (e.g., "tests passing with >80% coverage" not "code is good")
- Include testing requirements
- Include documentation if needed
- Use checkboxes for easy tracking

## Example Format

```markdown
# PRD: [Project Name]

## Problem Statement
[Clear description of the problem being solved]

## Requirements

### Functional Requirements
- [ ] Requirement 1
- [ ] Requirement 2

### Non-Functional Requirements
- [ ] Performance: [specific metric]
- [ ] Security: [specific requirement]
- [ ] Testing: [coverage target]

## Success Criteria
- [ ] Specific criterion 1
- [ ] Specific criterion 2
- [ ] All tests passing

## Completion Promise
Output: <promise>PRD_COMPLETE</promise> when all success criteria met

## Task Breakdown

### Task 1: [TAG] Task name
**Description**: What this task does
**Dependencies**: None
**Parallelizable**: Yes

### Task 2: [TAG] Task name
**Description**: What this task does
**Dependencies**: Task 1
**Parallelizable**: After Task 1
```

## Important Notes

- Ask clarifying questions if the brain dump is too vague
- Extract the core problem, not just features
- Be realistic about task dependencies
- Make success criteria measurable
- The PRD should be Ralph-friendly for iterative execution

After creating the PRD, inform the user they can:
1. Review and edit `prd.md`
2. Execute with Ralph: `/ralph-loop "$(cat prd.md)" --max-iterations 50 --completion-promise "PRD_COMPLETE"`
