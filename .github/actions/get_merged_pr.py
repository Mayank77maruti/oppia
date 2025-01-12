import os
import sys
import requests

# Fetch the PR details using GitHub API to get the latest merged PR for the develop branch
repo = os.environ['GITHUB_REPOSITORY']
token = os.environ['GITHUB_TOKEN']
url = f"https://api.github.com/repos/{repo}/pulls?state=closed&sort=updated&direction=desc"

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}"
}

response = requests.get(url, headers=headers)
if response.status_code != 200:
    print(f"Error fetching PRs: {response.status_code}")
    sys.exit(1)

prs = response.json()
if not prs:
    print("No PRs found.")
    sys.exit(1)

# Get the most recent PR number
pr_number = prs[0]['number']
print(f"PR_NUMBER={pr_number}", end='')
