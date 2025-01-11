import os
import requests
import time

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("REPO")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds

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

def assign_pr_author(pr_number, pr_author):
    """Assign the PR author to the pull request."""
    assign_url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/assignees"
    assign_payload = {"assignees": [pr_author]}
    response = requests.post(assign_url, json=assign_payload, headers=HEADERS)
    if response.ok:
        print(f"Successfully assigned {pr_author} to PR #{pr_number}.")
    else:
        print(f"Failed to assign {pr_author} to PR #{pr_number}. Response: {response.text}")

def notify_pr_author(pr_number, pr_author):
    """Notify the PR author about the merge conflict."""
    comment_url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/comments"
    comment_payload = {
        "body": (
            f"Hi @{pr_author}, due to recent changes in the `develop` branch, this PR now has a merge conflict. "
            f"Please resolve the conflict following [this guide](https://help.github.com/articles/resolving-a-merge-conflict-using-the-command-line/). "
            f"Thank you!"
        )
    }
    response = requests.post(comment_url, json=comment_payload, headers=HEADERS)
    if response.ok:
        print(f"Successfully notified {pr_author} about the merge conflict in PR #{pr_number}.")
    else:
        print(f"Failed to notify {pr_author} about the merge conflict in PR #{pr_number}. Response: {response.text}")

def check_and_notify(prs):
    """Check for merge conflicts or dirty state, assign the PR author, and notify if conflicts exist."""
    for pr in prs:
        pr_number = pr["number"]
        pr_author = pr["user"]["login"]

        print(f"Checking PR #{pr_number} by {pr_author}.")

        # Fetch PR details with retries
        pr_details = fetch_pr_details(pr_number)
        if not pr_details:
            print(f"Skipping PR #{pr_number} due to undetermined mergeable state.")
            continue

        mergeable_state = pr_details.get("mergeable_state")

        if mergeable_state == "conflict":
            print(f"PR #{pr_number} has conflicts.")

            # Assign the author to the PR
            assign_pr_author(pr_number, pr_author)

            # Notify the PR author about the conflict
            notify_pr_author(pr_number, pr_author)
        elif mergeable_state == "dirty":
            print(f"PR #{pr_number} has a dirty state.")

            # Assign the author to the PR for a dirty state
            assign_pr_author(pr_number, pr_author)
        else:
            print(f"PR #{pr_number} does not have conflicts or dirty state. Mergeable state: {mergeable_state}")

if __name__ == "__main__":
    try:
        prs = list_open_prs()
        check_and_notify(prs)
    except Exception as e:
        print(f"An error occurred: {e}")
