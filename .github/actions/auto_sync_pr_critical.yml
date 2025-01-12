import os
import requests
import time

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("REPO")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
CRITICAL_LABEL = "PR: require post-merge sync to HEAD"
DEVELOP_BRANCH = "develop"
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds


def list_merged_prs():
    """Fetch the list of recently merged pull requests."""
    url = f"https://api.github.com/repos/{REPO}/pulls?state=closed"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    prs = response.json()
    return [pr for pr in prs if pr.get("merged_at")]  # Filter to include only merged PRs


def fetch_pr_details(pr_number):
    """Fetch the details of a specific PR."""
    pr_details_url = f"https://api.github.com/repos/{REPO}/pulls/{pr_number}"
    for attempt in range(RETRY_COUNT):
        response = requests.get(pr_details_url, headers=HEADERS)
        response.raise_for_status()
        pr_details = response.json()
        if pr_details:
            return pr_details
        time.sleep(RETRY_DELAY)
    return None


def list_open_prs():
    """Fetch the list of open pull requests."""
    url = f"https://api.github.com/repos/{REPO}/pulls?state=open"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def sync_branch(branch_name, base_branch):
    """Sync a branch with the base branch."""
    merge_url = f"https://api.github.com/repos/{REPO}/merges"
    payload = {
        "base": branch_name,
        "head": base_branch,
        "commit_message": f"Auto-merging {branch_name} with {base_branch} due to critical PR merge.",
    }
    response = requests.post(merge_url, json=payload, headers=HEADERS)
    if response.ok:
        print(f"Auto-synced branch '{branch_name}' with '{base_branch}'.")
    else:
        print(f"Failed to auto-sync branch '{branch_name}' with '{base_branch}'. Response: {response.text}")


def notify_pr_author_to_sync(pr_number, pr_author, branch_name, base_branch):
    """Notify the PR author to sync their branch with the base branch."""
    comment_url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/comments"
    message = (
        f"Hi @{pr_author}, the latest merged PR has triggered a critical sync with the `{base_branch}` branch. "
        f"Your branch `{branch_name}` needs to be updated to avoid conflicts.\n\n"
        "To sync your branch, run the following commands:\n\n"
        "```bash\n"
        f"git checkout {branch_name}\n"
        f"git fetch origin {base_branch}\n"
        f"git rebase origin/{base_branch}\n"
        "```\n\n"
        "Let us know if you need any assistance!"
    )
    response = requests.post(comment_url, json={"body": message}, headers=HEADERS)
    if response.ok:
        print(f"Notified @{pr_author} about syncing branch '{branch_name}'.")
    else:
        print(f"Failed to notify @{pr_author} about syncing branch '{branch_name}'. Response: {response.text}")


def auto_sync_open_prs_if_needed():
    """Check the latest merged PR and sync open PR branches if required."""
    merged_prs = list_merged_prs()
    if not merged_prs:
        print("No recently merged PRs found.")
        return

    # Check the latest merged PR
    latest_pr = merged_prs[0]
    pr_number = latest_pr["number"]
    pr_details = fetch_pr_details(pr_number)
    labels = [label["name"] for label in pr_details.get("labels", [])]

    if CRITICAL_LABEL in labels:
        print(f"Latest merged PR #{pr_number} is marked critical. Syncing open PR branches.")
        open_prs = list_open_prs()

        for pr in open_prs:
            pr_number = pr["number"]
            pr_author = pr["user"]["login"]
            pr_branch = pr["head"]["ref"]

            print(f"Processing PR #{pr_number} by @{pr_author} (branch: {pr_branch}).")

            try:
                # Attempt to sync the branch
                sync_branch(pr_branch, DEVELOP_BRANCH)
            except Exception as e:
                print(f"Auto-sync failed for PR #{pr_number}. Notifying the author.")
                notify_pr_author_to_sync(pr_number, pr_author, pr_branch, DEVELOP_BRANCH)
    else:
        print(f"Latest merged PR #{pr_number} is not marked as critical. No action required.")


if __name__ == "__main__":
    try:
        auto_sync_open_prs_if_needed()
    except Exception as e:
        print(f"An error occurred: {e}")
