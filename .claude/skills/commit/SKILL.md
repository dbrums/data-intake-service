---
name: commit
description: Generate and create conventional commits interactively
---

# Conventional Commit Assistant

Generate a conventional commit message based on staged changes, ask for approval, and create the commit.

## Workflow

1. **Check staged changes**: See what files are staged for commit
2. **Analyze changes**: Review the actual code changes
3. **Generate commit message**: Create a conventional commit message following the format:
   - `<type>(<scope>): <description>`
   - Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
   - Scopes: api, db, service, repo, test, ci, deps, config
4. **Ask for approval**: Present the message and ask user to approve or edit
5. **Create commit**: Run git commit with the approved message

## Instructions

### Step 1: Check Status

Run `git status --short` to see what files are staged and unstaged.

**If nothing is staged:**
- Show unstaged files
- Ask the user: "No files are staged. Would you like to (1) stage all changes (git add -A), (2) stage specific files, or (3) cancel?"
- If option 1: Run `git add -A` and continue
- If option 2: Ask which files to stage, run `git add <files>`, and continue
- If option 3: Stop

**If files are staged:**
- Show the staged files list
- Continue to Step 2

### Step 2: Review Changes

Run these commands in parallel:
- `git diff --staged --stat` - Show files changed with line counts
- `git diff --staged` - See the actual code changes
- `git log -1 --pretty=format:"%s"` - See the last commit message for style reference

### Step 3: Analyze and Generate Message

Analyze the changes and determine:

**Type (required):**
- `feat` - New features or functionality
- `fix` - Bug fixes
- `refactor` - Code changes that neither fix bugs nor add features
- `test` - Adding or updating tests
- `docs` - Documentation only
- `style` - Formatting, whitespace
- `perf` - Performance improvements
- `ci` - CI/CD changes
- `build` - Build system, dependencies
- `chore` - Maintenance, configuration

**Scope (optional but recommended for this project):**
- `api` - API endpoints, routing (app/api/)
- `db` - Database models, migrations (app/db/)
- `service` - Business logic (app/services/)
- `repo` - Data access layer (app/repositories/)
- `test` - Test infrastructure (tests/)
- `ci` - CI/CD workflows (.github/)
- `deps` - Dependencies (pyproject.toml)
- `config` - Configuration (app/core/config.py)

**Description:**
- Short (50-72 chars), imperative mood
- No period at the end
- Describe what the change does, not what was done
- Examples: "add retry logic" not "added retry logic"

**Body (optional, for complex changes):**
- Explain the "why" not the "what"
- Include context, motivation
- Describe breaking changes in detail

**Footer (optional):**
- Reference issues: `Closes #123` or `Fixes #456`
- Note breaking changes: `BREAKING CHANGE: <description>`

**Breaking changes:**
- Add `!` after type/scope if breaking: `feat!:` or `feat(api)!:`
- Must include `BREAKING CHANGE:` in the body or footer

### Step 4: Present Message

Format the message clearly with a box:

```
Proposed commit message:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<type>(<scope>): <description>

<body (if any)>

<footer (if any)>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files to be committed:
• file1.py (+10, -2)
• file2.py (+5, -1)
```

Ask: "Would you like to: (1) approve and commit, (2) edit the message, or (3) cancel?"

Use AskUserQuestion tool if available, or wait for text response.

### Step 5: Handle User Response

**Option 1: Approve and commit**
- Run `git commit -m "$(cat <<'EOF'\n<message>\nEOF\n)"` for proper multi-line handling
- If commit succeeds: Show "✅ Committed: <short version of message>"
- If commit fails (pre-commit hooks): Go to Error Handling

**Option 2: Edit**
- Ask: "Please provide your edited commit message (supports multi-line):"
- Wait for user input
- Validate the edited message follows conventional commits format
- If invalid: Warn and ask if they want to proceed anyway or re-edit
- Run `git commit -m "$(cat <<'EOF'\n<message>\nEOF\n)"`
- Confirm success or handle errors

**Option 3: Cancel**
- Confirm: "❌ Cancelled. Changes remain staged. Run `git reset` to unstage."

## Important Rules

- **Never skip hooks**: Never use `git commit --no-verify` or `--no-gpg-sign`
- **Multi-line messages**: Always use heredoc format for commits with body/footer
- **Imperative mood**: "add" not "added" or "adds"
- **Length limits**: Description ≤72 chars, preferably ≤50 chars
- **Breaking changes**: Must have `!` AND `BREAKING CHANGE:` footer
- **Pre-commit integration**: Let pre-commit hooks run and fix issues

## Examples

**Simple feature:**
```
feat(api): add job retry endpoint
```

**Bug fix with scope:**
```
fix(db): handle null values in job status migration
```

**Breaking change:**
```
refactor(api)!: change job response structure

BREAKING CHANGE: Job responses now return `jobId` instead of `id`.
Clients must update their integrations to use the new field name.
```

**Documentation:**
```
docs: update README with pre-commit setup instructions
```

**Complex change with body:**
```
feat(service): implement exponential backoff for job retries

Adds configurable retry logic with exponential backoff and jitter
to prevent thundering herd issues when many jobs fail simultaneously.

Maximum retry count is configurable via MAX_JOB_RETRIES environment
variable. Default is 3 retries with 2^n second delays.

Closes #45
```

**Multiple related changes:**
```
chore(deps): update security dependencies

Updates pytest to 9.0.3 (CVE-2025-71176) and black to 26.3.1
(CVE-2026-32274). No breaking changes.
```

## Error Handling

### Pre-commit Hook Failures

If pre-commit hooks fail, analyze the error and provide specific guidance:

**Black formatting failure:**
```
Pre-commit hook failed: black

The following files need formatting:
• app/services/job_service.py

Fix: Run 'pre-commit run black --all-files' to auto-format,
then stage the changes and try committing again.
```

**mypy type checking failure:**
```
Pre-commit hook failed: mypy

Type errors found:
app/api/endpoints/jobs.py:15: error: Missing return statement

Fix: Add the missing return statement, stage the fix, and retry.
```

**Conventional commit failure:**
```
Pre-commit hook failed: conventional-pre-commit

Commit message doesn't follow conventional commits format.

This shouldn't happen if I generated the message. Please report this issue.
```

After showing the error:
- Ask: "Would you like me to help fix the issues?"
- If yes: Provide specific commands or code fixes
- Don't automatically retry - let the user fix and run `/commit` again

### Git Commit Failures

If `git commit` fails for other reasons (e.g., nothing to commit, merge conflicts):
- Show the git error message
- Explain what it means
- Suggest resolution steps

## Usage Examples

**Basic usage:**
```
User: /commit
Claude: [Reviews staged changes, generates message, asks for approval]
```

**With arguments (optional future enhancement):**
```
User: /commit --type feat --scope api
Claude: [Uses provided type/scope, generates rest]
```

**Quick commit (if all files should be staged):**
```
User: /commit --all
Claude: [Stages all changes, generates message, asks for approval]
```

## Notes for Implementation

- This skill should be **interactive** - use AskUserQuestion when possible
- **Read git config** to get user name/email for co-authoring if desired
- **Respect .gitignore** - don't suggest staging ignored files
- **Check for merge commits** - don't run during merge/rebase
- **Detect WIP commits** - warn if generating message for partial work
