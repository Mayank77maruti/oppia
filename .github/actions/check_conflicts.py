import os
import requests
import time

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("REPO")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds

LABEL_CRITICAL = "PR: require post-merge sync to HEAD"

def list_open_prs():
    """Fetch the list of open pull requests."""
    url = f"https://api.github.com/repos/{REPO}/pulls?state=open"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def fetch_pr_details(pr_number):
    """Fetch the details of a specific PR."""
    pr_details_url = f"https://api.github.com/repos/{REPO}/pulls/{pr_number}"
    for attempt in range(RETRY_COUNT):
        response = requests.get(pr_details_url, headers=HEADERS)
        response.raise_for_status()
        pr_details = response.json()
        mergeable_state = pr_details.get("mergeable_state")
        if mergeable_state and mergeable_state != "unknown":
            return pr_details
        print(f"Retry {attempt + 1}/{RETRY_COUNT}: Mergeable state is 'unknown' for PR #{pr_number}. Retrying...")
        time.sleep(RETRY_DELAY)
    print(f"Mergeable state could not be determined for PR #{pr_number} after retries.")
    return None

def fetch_pr_comments(pr_number):
    """Fetch all comments for a PR."""
    comments_url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/comments"
    response = requests.get(comments_url, headers=HEADERS)
    if response.ok:
        return response.json()
    else:
        print(f"Failed to fetch comments for PR #{pr_number}. Response: {response.text}")
        return []

def notify_pr_author(pr_number, pr_author, message):
    """Notify the PR author with a comment, avoiding duplicates."""
    existing_comments = fetch_pr_comments(pr_number)
    for comment in existing_comments:
        if message in comment.get("body", ""):
            print(f"Message already exists for PR #{pr_number}. Skipping notification.")
            return  # Skip posting if the message already exists

    comment_url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/comments"
    comment_payload = {"body": message}
    response = requests.post(comment_url, json=comment_payload, headers=HEADERS)
    if response.ok:
        print(f"Successfully notified {pr_author} for PR #{pr_number}.")
    else:
        print(f"Failed to notify {pr_author} for PR #{pr_number}. Response: {response.text}")

def auto_merge_branch(base_branch, head_branch):
    """Attempt to auto-merge a branch."""
    merge_url = f"https://api.github.com/repos/{REPO}/merges"
    merge_payload = {
        "base": base_branch,
        "head": head_branch
    }
    response = requests.post(merge_url, json=merge_payload, headers=HEADERS)
    if response.ok:
        print(f"Successfully merged {head_branch} into {base_branch}.")
    else:
        print(f"Failed to merge {head_branch} into {base_branch}. Response: {response.text}")

def handle_critical_pr(pr):
    """Handle a critical PR with the specific label."""
    pr_number = pr["number"]
    pr_author = pr["user"]["login"]
    base_branch = "develop"  # Replace with your main branch if different
    head_branch = pr["head"]["ref"]

    # Notify the PR author to sync their branch
    message = (
        f"Hi @{pr_author}, your PR #{pr_number} is critical and requires syncing to the HEAD of the `{base_branch}` branch. "
        "Please follow [this guide](https://help.github.com/articles/syncing-a-fork/) to update your branch. "
        "Alternatively, you can request auto-syncing from the maintainers."
    )
    notify_pr_author(pr_number, pr_author, message)

    # Optional: Auto-merge the branch
    auto_merge_branch(base_branch, head_branch)

def check_and_notify(prs):
    """Check for merge conflicts, dirty state, or critical PRs and notify appropriately."""
    for pr in prs:
        pr_number = pr["number"]
        pr_author = pr["user"]["login"]
        labels = [label["name"] for label in pr.get("labels", [])]

        print(f"Checking PR #{pr_number} by {pr_author}.")

        if LABEL_CRITICAL in labels:
            print(f"PR #{pr_number} is marked as critical.")
            handle_critical_pr(pr)
            continue

        # Fetch PR details with retries
        pr_details = fetch_pr_details(pr_number)
        if not pr_details:
            print(f"Skipping PR #{pr_number} due to undetermined mergeable state.")
            continue

        mergeable_state = pr_details.get("mergeable_state")

        if mergeable_state == "conflict":
            print(f"PR #{pr_number} has conflicts.")

            # Notify the PR author about the conflict
            message = (
                f"Hi @{pr_author}, your PR #{pr_number} has a **merge conflict**. "
                "Please resolve it by following [this guide](https://help.github.com/articles/resolving-a-merge-conflict-using-the-command-line/)."
            )
            notify_pr_author(pr_number, pr_author, message)
        elif mergeable_state == "dirty":
            print(f"PR #{pr_number} has a dirty state.")

            # Notify the PR author about the dirty state
            message = (
                f"Hi @{pr_author}, your PR #{pr_number} has a **dirty state**. "
                "Please resolve it by syncing your branch with the target branch."
            )
            notify_pr_author(pr_number, pr_author, message)
        else:
            print(f"PR #{pr_number} is clean. Mergeable state: {mergeable_state}")

if __name__ == "__main__":
    try:
        prs = list_open_prs()
        check_and_notify(prs)
    except Exception as e:
        print(f"An error occurred: {e}")
