#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROMPT = """Read the guidelines in CLAUDE.md.
Review the code changes in github PR {pr_number} (this branch), use gh cli if needed.
Act as a critical and brutally honest senior software engineer.
Write the report to GEMINI_REVIEW_PR{pr_number}.md.
If you see an opportunity to improve, include code fragments in the report showing how to improve the code."""


def run_command(cmd, cwd=None, capture=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=capture, text=True)
    if result.returncode != 0:
        print(f"Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip() if capture else None


def main():
    parser = argparse.ArgumentParser(description="Gemini PR Review Script")
    parser.add_argument("pr_number", help="PR number to review")
    parser.add_argument(
        "--use-existing-worktree",
        action="store_true",
        help="Use existing worktree vs recreating worktree (clean one)",
    )
    parser.add_argument(
        "--work-dir",
        help="Directory within the worktree where gemini should run (default: auto-detect from changes)",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory where review file should be written (default: current directory)",
    )

    args = parser.parse_args()
    pr_number = args.pr_number

    print(f"Reviewing PR #{pr_number}...")

    # Step 1: Fetch PR Information
    print("Step 1: Fetching PR information...")

    # Get PR details including fork information
    pr_info_json = run_command(
        f"gh pr view {pr_number} --json headRefName,title,files,isCrossRepository,headRepositoryOwner"
    )
    pr_info = json.loads(pr_info_json)

    branch_name = pr_info["headRefName"]
    branch_dir_postfix = branch_name.replace("/", "-")
    pr_title = pr_info["title"]
    is_fork_pr = pr_info.get("isCrossRepository", False)

    git_top_dir = run_command("git rev-parse --show-toplevel")
    repo_name = Path(git_top_dir).name
    temp_dir_for_ws = Path(git_top_dir) / "temp"
    worktree_dir = temp_dir_for_ws / f"{repo_name}-{branch_dir_postfix}"

    print(f"PR Title: {pr_title}")
    print(f"Branch: {branch_name}")
    print(f"Is Fork PR: {is_fork_pr}")

    # Handle fork-based workflow
    # For fork PRs, we need to:
    # 1. Add the fork as a remote (if not already added)
    # 2. Fetch from the fork remote
    # 3. Create worktree using the remote branch reference (fork-owner/branch-name)
    if is_fork_pr:
        fork_owner = pr_info["headRepositoryOwner"]["login"]
        fork_remote_name = f"fork-{fork_owner}"
        fork_url = f"git@github.com:{fork_owner}/{repo_name}.git"

        print(f"Fork Owner: {fork_owner}")
        print(f"Fork Remote: {fork_remote_name}")

        # Check if remote already exists
        existing_remotes = run_command("git remote").split("\n")
        if fork_remote_name not in existing_remotes:
            print(f"Adding fork remote: {fork_url}")
            run_command(f"git remote add {fork_remote_name} {fork_url}")

        # Fetch from fork
        print(f"Fetching from fork remote: {fork_remote_name}")
        run_command(f"git fetch {fork_remote_name}")

        # Use the remote branch reference for worktree
        branch_ref = f"{fork_remote_name}/{branch_name}"
    else:
        # For non-fork PRs, fetch from origin
        run_command("git fetch")
        branch_ref = branch_name

    print(f"Branch reference: {branch_ref}")

    # Step 2: Create Worktree
    print("Step 2: Creating worktree...")
    temp_dir_for_ws.mkdir(exist_ok=True)

    # Remove existing worktree if it exists and not using existing
    if not args.use_existing_worktree and worktree_dir.exists():
        print("Removing existing worktree...")
        run_command(f"git worktree remove {worktree_dir} --force")

    if not worktree_dir.exists():
        print(f"Creating worktree from: {branch_ref}")
        run_command(f"git worktree add {worktree_dir} {branch_ref}")
    else:
        print("Using existing worktree...")

    # Step 3: Analyze Changes and Determine Review Directory
    print("Step 3: Analyzing changes...")

    # Determine review directory based on work_dir argument or auto-detection
    if args.work_dir:
        review_dir = args.work_dir
        print(f"Using specified work directory: {review_dir}")
    else:
        # Auto-detect based on file changes
        files = pr_info.get("files", [])
        cli_changes = 0
        webapp_changes = 0

        for file_info in files:
            file_path = file_info["path"]
            if file_path.startswith("cli/"):
                cli_changes += 1
            elif file_path.startswith("webapp/"):
                webapp_changes += 1

        print(f"CLI changes: {cli_changes}")
        print(f"Webapp changes: {webapp_changes}")

        # Determine review directory
        if cli_changes > webapp_changes:
            review_dir = "cli"
            print("Most changes in CLI directory")
        else:
            review_dir = "webapp"
            print("Most changes in Webapp directory")

    # Step 4: Execute Review in Separate Gemini Process
    print("Step 4: Executing review in separate gemini process...")
    review_path = worktree_dir / review_dir

    # Check if review path exists, fallback to worktree root if not
    if not review_path.exists():
        print(f"Warning: Review path {review_path} does not exist, using worktree root")
        review_path = worktree_dir

    print(f"Running gemini review in {review_path}...")

    # Format the prompt
    formatted_prompt = PROMPT.format(pr_number=pr_number)

    # Run gemini command
    gemini_cmd = ["gemini", "-y", "-p", formatted_prompt]

    subprocess.run(gemini_cmd, cwd=review_path)

    # Step 5: Copy Review Back
    print("Step 5: Copying review back to target directory...")
    review_file = review_path / f"GEMINI_REVIEW_PR{pr_number}.md"

    # Determine target directory: use --output-dir if provided, else current working directory
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    target_file = output_dir / f"GEMINI_REVIEW_PR{pr_number}.md"

    if review_file.exists():
        review_file.rename(target_file)
        print(f"Review completed and saved to {target_file}")
    else:
        print("Warning: Review file not found")
        sys.exit(1)

    print(f"PR #{pr_number} review completed successfully!")


if __name__ == "__main__":
    main()
