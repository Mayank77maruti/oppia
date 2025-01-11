import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("REPO")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
MERGE_CONFLICT_LABEL = "PR: don't merge - HAS MERGE CONFLICTS"

def list_open_prs():
    """Fetch the list of open pull requests."""
    url = f"https://api.github.com/repos/{REPO}/pulls?state=open"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def assign_pr_author(pr_number, pr_author):
    """Assign the PR author to the pull request."""
    assign_url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/assignees"
    assign_payload = {"assignees": [pr_author]}
    response = requests.post(assign_url, json=assign_payload, headers=HEADERS)
    if response.ok:
        print(f"Successfully assigned {pr_author} to PR #{pr_number}.")
    else:
        print(f"Failed to assign {pr_author} to PR #{pr_number}. Response: {response.text}")

def add_merge_conflict_label(pr_number):
    """Add the merge conflict label to the pull request."""
    label_url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/labels"
    label_payload = {"labels": [MERGE_CONFLICT_LABEL]}
    response = requests.post(label_url, json=label_payload, headers=HEADERS)
    if response.ok:
        print(f"Added merge conflict label to PR #{pr_number}.")
    else:
        print(f"Failed to add merge conflict label to PR #{pr_number}. Response: {response.text}")

def check_and_assign(prs):
    """Check for merge conflicts and assign the PR author if conflicts are present."""
    for pr in prs:
        pr_number = pr["number"]
        pr_author = pr["user"]["login"]

        # Fetch PR details
        pr_details_url = f"https://api.github.com/repos/{REPO}/pulls/{pr_number}"
        pr_details = requests.get(pr_details_url, headers=HEADERS).json()
        mergeable_state = pr_details.get("mergeable_state")
        labels = [label["name"] for label in pr_details.get("labels", [])]

        print(f"Checking PR #{pr_number} by {pr_author}. Mergeable state: {mergeable_state}")

        if mergeable_state == "conflict":
            print(f"PR #{pr_number} has conflicts.")

            # Assign the author to the PR
            assign_pr_author(pr_number, pr_author)

            # Add the merge conflict label if not already present
            if MERGE_CONFLICT_LABEL not in labels:
                add_merge_conflict_label(pr_number)
            else:
                print(f"PR #{pr_number} already has the merge conflict label.")
        else:
            print(f"PR #{pr_number} does not have conflicts.")

if __name__ == "__main__":
    try:
        prs = list_open_prs()
        check_and_assign(prs)
    except Exception as e:
        print(f"An error occurred: {e}")
