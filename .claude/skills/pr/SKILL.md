---
name: pr
description: Create a GitHub pull request with conventional commit title and structured description
---

# GitHub Pull Request Assistant

Generate a conventional commit style PR title and structured description, ask for approval, and create the PR.

## Workflow

1. **Check branch status**: Verify current branch and compare to main
2. **Analyze changes**: Review commits that will be in the PR
3. **Generate PR title**: Create conventional commit format title
4. **Generate PR description**: Create structured description
5. **Ask for approval**: Present title and description for review
6. **Create PR**: Run `gh pr create` with approved content

## Instructions

### Step 1: Check Branch Status

Run these commands in parallel:
- `git branch --show-current` - Get current branch name
- `git status --short` - Check for uncommitted changes
- `git rev-parse --abbrev-ref main@{upstream} 2>/dev/null || echo "origin/main"` - Get remote main branch
- `git log main..HEAD --oneline` - See commits that will be in PR

**If not on a feature branch:**
- Show error: "You're on main branch. Create a feature branch first."
- Stop

**If there are uncommitted changes:**
- Warn: "You have uncommitted changes. Commit or stash them before creating PR."
- Ask: "Would you like to see /commit to commit them first?"
- Stop (let user commit first)

**If no commits ahead of main:**
- Show error: "No commits to create PR from. Make some commits first."
- Stop

**If branch is behind main:**
- Warn: "Your branch is behind main. Consider rebasing first."
- Ask: "Continue anyway or cancel to rebase?"
- If cancel: Stop

**If branch not pushed to remote:**
- Note: "Branch not yet pushed. Will push before creating PR."

### Step 2: Review Changes

Run these commands in parallel:
- `git log main..HEAD --pretty=format:"%h %s"` - List commits in PR
- `git diff main...HEAD --stat` - Show files changed
- `git diff main...HEAD --shortstat` - Summary stats
- `gh pr list --head $(git branch --show-current) --json number,title,state` - Check if PR exists

**If PR already exists:**
- Parse PR number from JSON output: `echo "$pr_json" | jq -r '.[0].number'`
- Parse PR title: `echo "$pr_json" | jq -r '.[0].title'`
- Get PR URL: `gh pr view <number> --json url -q .url`
- Store these for later use
- Show: "PR #123 already exists: [title]"
- Show: "URL: [pr-url]"
- Ask: "Would you like to: (1) update title and description, (2) update description only, (3) view PR, or (4) cancel?"
- If option 1: Continue to title and description generation (will use `gh pr edit` with both)
- If option 2: Skip title generation, continue to description generation only (will preserve existing title)
- If option 3: Run `gh pr view` and stop
- If option 4: Stop

### Step 3: Analyze and Generate PR Title

Analyze the commits and determine:

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

**Scope (optional but recommended):**
- `api` - API endpoints (app/api/)
- `db` - Database models, migrations (app/db/)
- `service` - Business logic (app/services/)
- `repo` - Data access layer (app/repositories/)
- `test` - Test infrastructure (tests/)
- `ci` - CI/CD workflows (.github/)
- `deps` - Dependencies (pyproject.toml)
- `config` - Configuration

**Title rules:**
- Format: `<type>(<scope>): <description>`
- 50-72 characters max
- Imperative mood ("add" not "adds" or "added")
- No period at end
- Summarize the overall change, not individual commits

**If multiple commits:**
- Look for the dominant theme
- Summarize the overall feature/fix
- Don't just use the first commit message

**Examples:**
- Single commit: `feat(api): add job endpoint` → Use as-is (if good)
- Multiple commits:
  - `feat(api): add endpoint`
  - `test(api): add tests`
  - `docs: update README`
  → Generate: `feat(api): add job endpoint with tests and docs`

### Step 4: Generate PR Description

Use this structured format:

```markdown
## Summary
[1-2 sentence overview of what this PR does and why]

## Changes
[Bulleted list of key changes, organized logically]
-
-

## Testing
[How was this tested? Be specific]
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing performed
- [ ] [Other relevant testing]

## Related
[Link to issues, other PRs, or note if none]
Closes #[issue-number]
```

**Guidelines for each section:**

**Summary:**
- What: Briefly describe the change
- Why: Why is this needed?
- 1-2 sentences max

**Changes:**
- Bullet list of key changes
- Organize by layer (API → Service → Repository → DB) if applicable
- Focus on *what* changed, not implementation details
- 3-8 bullets typically

**Testing:**
- Be specific about test coverage
- Check boxes for what was done
- Include manual testing details
- Mention any edge cases tested

**Related:**
- `Closes #123` if fixes an issue
- `Related to #456` if connected
- Links to relevant PRs or docs
- If none: "No related issues"

### Step 5: Present PR Title and Description

Format clearly:

```
Proposed pull request:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title:
<type>(<scope>): <description>

Description:
<description content>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Commits that will be included:
• abc1234 feat(api): add endpoint
• def5678 test: add tests
• ghi9012 docs: update README

Files changed: 15 files (+234, -12)
```

Ask: "Would you like to: (1) approve and create PR, (2) edit the content, or (3) cancel?"

Use AskUserQuestion tool.

### Step 6: Handle User Response

**Determine operation mode:**
- If PR already exists (from Step 2): Update mode
- If PR doesn't exist: Create mode

#### Create Mode (New PR)

**Option 1: Approve and create PR**

If branch not pushed:
- Run: `git push -u origin $(git branch --show-current)`
- If push fails: Show error and stop

Create PR:
- Save description to temp file (use mktemp or .pr-description.tmp)
- Run: `gh pr create --title "<title>" --body-file <temp-file>`
- If successful: Show PR URL and number
- If fails: Show error and suggest manual creation
- Clean up temp file

**Option 2: Edit**

Ask: "Please provide edited title and description (multiline supported):"

Format:
```
Title: <your title>

Description:
<your description>
```

Wait for user input, parse title and description, then create PR with edited content.

**Option 3: Cancel**

Confirm: "❌ Cancelled. No PR created. Run /pr again when ready."

#### Update Mode (Existing PR)

Store the PR number from Step 2's `gh pr list` output.

**If user selected "update title and description" in Step 2:**

Present both title and description for approval (same format as create mode).

**Option 1: Approve and update PR**

Push commits if needed:
- Check if branch has unpushed commits: `git log origin/$(git branch --show-current)..HEAD`
- If yes: Run `git push`
- If push fails: Show error and stop

Update PR:
- Save description to temp file
- Run: `gh pr edit <pr-number> --title "<title>" --body-file <temp-file>`
- If successful: Show "✅ Updated PR #<number>: <title>" and URL
- If fails: Show error with suggestion
- Clean up temp file

**Option 2: Edit**

Same as create mode - ask for edited title and description, then update.

**Option 3: Cancel**

Confirm: "❌ Cancelled. PR not updated."

**If user selected "update description only" in Step 2:**

Skip title generation. Only generate and present description.

Present description for approval:
```
Proposed PR description update:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<description content>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current title will be preserved: <existing-title>
```

**Option 1: Approve and update description**

Push commits if needed (same as above).

Update PR:
- Save description to temp file
- Run: `gh pr edit <pr-number> --body-file <temp-file>` (no --title flag)
- If successful: Show "✅ Updated PR #<number> description"
- If fails: Show error
- Clean up temp file

**Option 2: Edit description**

Ask for edited description only, then update.

**Option 3: Cancel**

Confirm: "❌ Cancelled. PR description not updated."

## Important Rules

- **Branch check first**: Never run on main branch
- **Clean working tree**: Require all changes committed
- **Conventional title**: Must follow conventional commits format
- **Structured description**: Use the template format
- **Push before PR**: Always push branch before creating PR
- **Error handling**: Clear messages for all failure cases

## Examples

### Single Commit PR

**Commits:**
```
abc1234 feat(api): add job creation endpoint with validation
```

**Generated Title:**
```
feat(api): add job creation endpoint with validation
```

**Generated Description:**
```markdown
## Summary
Adds POST /api/v1/jobs endpoint for creating dataset validation jobs with schema validation.

## Changes
- Add JobCreate Pydantic schema with validation rules
- Implement POST /api/v1/jobs endpoint
- Add validation for required fields and business rules
- Return 201 with job ID on success

## Testing
- [x] Unit tests for schema validation
- [x] Integration tests for API endpoint
- [x] Manual testing with Postman
- [x] Edge cases: invalid schemas, missing fields

## Related
Closes #45
```

### Multi-Commit PR

**Commits:**
```
abc1234 feat(api): add job endpoint skeleton
def5678 feat(service): implement job creation logic
ghi9012 feat(repo): add database persistence
jkl3456 test: add comprehensive test suite
mno7890 docs: update API documentation
```

**Generated Title:**
```
feat(api): add job creation endpoint with full implementation
```

**Generated Description:**
```markdown
## Summary
Implements complete job creation flow including API endpoint, business logic, database persistence, and comprehensive testing.

## Changes
- Add POST /api/v1/jobs endpoint with request validation
- Implement JobService.create_job() with business logic
- Add JobRepository for database operations
- Create comprehensive test coverage (unit, integration, e2e)
- Update API documentation with new endpoint

## Testing
- [x] Unit tests for service and repository layers
- [x] Integration tests with real database
- [x] E2E tests via TestClient
- [x] Manual testing with various payload sizes
- [x] Edge cases: duplicate jobs, invalid schemas

## Related
Closes #45
```

### Bug Fix PR

**Commits:**
```
abc1234 fix(db): handle null values in job status migration
def5678 test: add regression test for null handling
```

**Generated Title:**
```
fix(db): handle null values in job status migration
```

**Generated Description:**
```markdown
## Summary
Fixes bug where null job status values caused migration failures during database upgrade.

## Changes
- Add null handling in job status migration script
- Set default status for null values
- Add data validation before migration
- Include rollback handling

## Testing
- [x] Unit tests for migration logic
- [x] Integration tests with null data
- [x] Tested upgrade from previous schema version
- [x] Tested rollback scenario
- [x] Manual testing on staging database

## Related
Fixes #67
```

### Refactoring PR

**Commits:**
```
abc1234 refactor(service): extract validation into separate class
def5678 refactor(service): simplify error handling
ghi9012 test: update tests for refactored code
jkl3456 docs: update architecture documentation
```

**Generated Title:**
```
refactor(service): improve validation and error handling architecture
```

**Generated Description:**
```markdown
## Summary
Refactors service layer validation and error handling to improve maintainability and testability without changing external behavior.

## Changes
- Extract validation logic into ValidationService
- Simplify error handling with custom exception hierarchy
- Improve separation of concerns
- Update tests to reflect new architecture
- Document new patterns in architecture guide

## Testing
- [x] All existing tests still pass
- [x] No changes to API contracts
- [x] Manual regression testing
- [x] Performance testing (no degradation)

## Related
Part of technical debt cleanup, no related issues
```

### Updating an Existing PR

**Scenario:** PR #123 exists, you've added new commits addressing review feedback.

**User runs:** `/pr`

**Skill detects existing PR:**
```
PR #123 already exists: feat(api): add job endpoint with validation
URL: https://github.com/user/repo/pull/123

Found 2 new commits since PR was created:
• def5678 fix(api): add input validation per review
• ghi9012 test: add edge case tests

Would you like to:
(1) Update title and description
(2) Update description only (preserve title)
(3) View PR
(4) Cancel
```

**User selects option 2 (update description only).**

**Skill generates updated description:**
```
Proposed PR description update:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## Summary
Adds POST /api/v1/jobs endpoint for creating dataset validation jobs with schema validation.

## Changes
- Add JobCreate Pydantic schema with validation rules
- Implement POST /api/v1/jobs endpoint
- Add validation for required fields and business rules
- Return 201 with job ID on success
- Add input validation for all fields (per review feedback)
- Add comprehensive edge case testing

## Testing
- [x] Unit tests for schema validation
- [x] Integration tests for API endpoint
- [x] Manual testing with Postman
- [x] Edge cases: invalid schemas, missing fields, boundary values
- [x] Negative test cases for validation errors

## Related
Closes #45
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current title will be preserved: feat(api): add job endpoint with validation

Would you like to: (1) approve and update, (2) edit description, or (3) cancel?
```

**User approves.**

**Skill executes:**
```bash
# Push new commits
git push

# Update PR description only
gh pr edit 123 --body-file /tmp/pr-description.tmp

✅ Updated PR #123 description
URL: https://github.com/user/repo/pull/123
```

**Result:** PR description now reflects new testing and changes, title unchanged.

## Error Handling

### Uncommitted Changes
```
Error: You have uncommitted changes:
 M app/api/endpoints/jobs.py
 M tests/test_jobs.py

Commit or stash changes before creating a PR.
Run /commit to create a commit interactively.
```

### On Main Branch
```
Error: You're currently on the 'main' branch.

Create a feature branch first:
  git checkout -b feat/your-feature-name
```

### No Commits
```
Error: No commits ahead of main.

Your branch is up to date with main. Make some commits first:
  git commit -m "feat: add something"
```

### PR Already Exists
```
PR #123 already exists: feat(api): add job endpoint
Status: open
URL: https://github.com/user/repo/pull/123

Would you like to:
(1) Update title and description
(2) Update description only (preserve title)
(3) View PR
(4) Cancel
```

**Note:** Options 1 and 2 will push any new commits automatically before updating the PR.

### GitHub CLI Not Available
```
Error: GitHub CLI (gh) is not installed or not authenticated.

Install: brew install gh
Authenticate: gh auth login
```

## Integration with /commit Skill

These skills work together:

**Workflow:**
```bash
# 1. Make changes during development
# 2. Use /commit skill to create conventional commits
/commit

# 3. When feature is complete, use /pr skill
/pr
```

**Benefits:**
- /commit handles individual commits
- /pr handles the overall PR
- Both enforce conventional commits
- Both provide interactive guidance
- Consistent quality at both levels

## Notes

- This skill requires `gh` CLI installed and authenticated
- Branch must be pushed to remote before PR creation
- PR title should summarize the overall change, not just the first commit
- PR description becomes your commit message when using "squash and merge"
- Template can be customized in .github/pull_request_template.md
- Works best when combined with branch protection rules and squash merge strategy
