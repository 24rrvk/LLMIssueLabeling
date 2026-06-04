from flask import Flask, request

from label_issue import label_issue

app = Flask(__name__)


@app.route("/github-webhook", methods=["POST"])
def github_webhook():
    payload = request.json

    if payload.get("action") == "opened":
        issue = payload["issue"]

        issue_number = issue["number"]
        title = issue["title"]
        body = issue["body"]

        print("\nNEW ISSUE REPORT SUBMITTED")
        print(f"Issue #: {issue_number}")
        print(f"Title: {title}")
        print(f"Body:\n{body}")

        label_issue(issue_number, title, body, True, 0)

    return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)