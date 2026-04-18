# Claude Code Project Configuration

This directory contains project-specific Claude Code settings and skills.

## Skills

### `/commit` - Conventional Commit Assistant

Interactive tool for creating conventional commits.

**Usage:**
```
/commit
```

**What it does:**
1. Shows your staged changes (or prompts to stage files)
2. Analyzes the changes and generates a conventional commit message
3. Asks you to approve, edit, or cancel
4. Creates the commit with the approved message

**Features:**
- ✅ Automatically determines appropriate type (feat, fix, docs, etc.)
- ✅ Suggests relevant scope (api, db, service, etc.) based on files changed
- ✅ Generates clear, imperative descriptions
- ✅ Handles multi-line messages with body and footer
- ✅ Detects breaking changes
- ✅ Validates against conventional commits format
- ✅ Respects pre-commit hooks

**Project-specific scopes:**
- `api` - API endpoints, routing (app/api/)
- `db` - Database models, migrations (app/db/)
- `service` - Business logic (app/services/)
- `repo` - Data access layer (app/repositories/)
- `test` - Test infrastructure (tests/)
- `ci` - CI/CD workflows (.github/)
- `deps` - Dependencies (pyproject.toml)
- `config` - Configuration (app/core/config.py)

**Examples:**

Simple feature:
```
/commit
→ feat(api): add job retry endpoint
```

Bug fix:
```
/commit
→ fix(db): handle null values in job status migration
```

Breaking change:
```
/commit
→ refactor(api)!: change job response structure

BREAKING CHANGE: Job responses now return `jobId` instead of `id`.
```

**Tips:**
- Stage your changes first with `git add <files>` for best results
- Or let the skill prompt you to stage all changes
- You can always edit the generated message before committing
- Pre-commit hooks will still run and may reformat your code
