import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("REPO")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
MERGE_CONFLICT_LABEL = "PR: don't merge - HAS MERGE CONFLICTS"

def list_open_prs():
    url = f"https://api.github.com/repos/{REPO}/pulls?state=open"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def check_and_assign(prs):
    for pr in prs:
        pr_number = pr["number"]
        pr_author = pr["user"]["login"]

        # Fetch PR details
        pr_details_url = f"https://api.github.com/repos/{REPO}/pulls/{pr_number}"
        pr_details = requests.get(pr_details_url, headers=HEADERS).json()
        mergeable_state = pr_details.get("mergeable_state")

        if mergeable_state == "conflict":
            print(f"PR #{pr_number} has conflicts. Assigning to {pr_author}.")

            # Assign the author to the PR
            assign_url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/assignees"
            assign_payload = {"assignees": [pr_author]}
            assign_response = requests.post(assign_url, json=assign_payload, headers=HEADERS)

            if assign_response.ok:
                print(f"Successfully assigned {pr_author} to PR #{pr_number}.")
            else:
                print(f"Failed to assign {pr_author} to PR #{pr_number}. Response: {assign_response.text}")
        else:
            print(f"PR #{pr_number} does not have conflicts.")

if __name__ == "__main__":
    try:
        prs = list_open_prs()
        check_and_assign(prs)
    except Exception as e:
        print(f"An error occurred: {e}")
