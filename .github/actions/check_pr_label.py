import os
import sys
import requests

# Check if the PR has the required label
repo = os.environ['GITHUB_REPOSITORY']
token = os.environ['GITHUB_TOKEN']
pr_number = os.environ['PR_NUMBER']
label_name = "PR: require post-merge sync to HEAD"
url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}"
}

response = requests.get(url, headers=headers)
if response.status_code != 200:
    print(f"Error fetching labels: {response.status_code}")
    sys.exit(1)

labels = response.json()
label_found = any(label['name'] == label_name for label in labels)

if label_found:
    print("::set-output name=sync::true")
    print("Label found")
else:
    print("::set-output name=sync::false")
    print("Label not found")
