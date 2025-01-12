import os
import requests
from github import Github

# Get environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
LABEL_NAME = "PR: require post-merge sync to HEAD"

def get_open_prs(repo):
    """Fetch all open PRs from the repository."""
    return repo.get_pulls(state='open', sort='created', direction='desc')

def sync_branch(repo, base_branch, head_branch):
    """Attempt to auto-sync the branch."""
    try:
        base = repo.get_git_ref(f"heads/{base_branch}")
        head = repo.get_git_ref(f"heads/{head_branch}")

        # Merge the base branch into the head branch
        repo.merge(head_branch, base.object.sha)
        print(f"Successfully synced branch {head_branch} with {base_branch}.")
        return True
    except Exception as e:
        print(f"Failed to auto-sync branch {head_branch}: {e}")
        return False

def notify_author(pr):
    """Notify the PR author via comment."""
    author = pr.user.login
    pr.create_issue_comment(f"Hi @{author}, your branch requires syncing with HEAD. Please update your branch.")
    print(f"Notification sent to author @{author}.")

def main():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    # Check if the merged PR has the label
    event = os.getenv("GITHUB_EVENT_PATH")
    with open(event, "r") as f:
        data = json.load(f)
    
    merged_pr_number = data["pull_request"]["number"]
    merged_pr = repo.get_pull(merged_pr_number)

    if LABEL_NAME not in [label.name for label in merged_pr.get_labels()]:
        print(f"No action required: Label '{LABEL_NAME}' not found.")
        return

    # Process open PRs
    open_prs = get_open_prs(repo)
    for pr in open_prs:
        if not sync_branch(repo, merged_pr.base.ref, pr.head.ref):
            notify_author(pr)

if __name__ == "__main__":
    main()
