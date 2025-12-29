## Git Workflow

### Git and GitHub Commands

- `gh pr create --draft`: Create draft pull request
- `gh pr ready <pr-number>`: Mark PR as ready for review
- `gh pr merge <pr-number> --squash`: Squash and merge PR
- `gh pr edit <pr-number> --add-reviewer <username>`: Add reviewer to PR

You must not use `git add -A` or `git add .`. Specify the files for the `git add` command.

### Branch Naming Conventions

Use descriptive prefixes followed by descriptive names with dashes:

- `feature/` - for adding new functionality or capabilities
- `bugfix/` - for fixing bugs or issues in the codebase
- `chore/` - for maintenance tasks, updates, or routine work
- `refactor/` - for code restructuring without changing functionality
- `experiment/` - for testing new ideas or proof-of-concept work
- `docs/` - for documentation updates or additions
- `aidev/` - for AI-assisted development or automation tasks

### Commit Messages

- Use imperative mood (e.g., "Add feature" not "Added feature")
- Keep subject line concise (50 chars or less)
- Start with capital letter and don't end with period
- Separate subject from body with a blank line for detailed explanations
- For security updates, prefix with "Security:" or document vulnerability fixes
- NEVER mention co-authored-by or tool used to create the commit

### Pull Requests

- Create detailed message focusing on high-level problem and solution
- You MUST squash and merge PRs, NEVER only merge
- Use `gh` command line tool for PR operations
