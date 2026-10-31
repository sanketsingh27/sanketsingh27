"""Refresh public commits; API failures leave the existing README untouched."""
import html
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
START, END = "<!-- COMMITS:START -->", "<!-- COMMITS:END -->"


def render(items):
    rows = ["| Date | Repository | Commit |", "| :--- | :--- | :--- |"]
    for item in items:
        repo = item["repository"]
        if repo.get("private", True):
            continue
        message = item["commit"]["message"].splitlines()[0][:85]
        # Encode punctuation so commit messages cannot inject HTML or Markdown.
        message = "".join(c if c.isalnum() or c == " " else f"&#{ord(c)};" for c in message)
        date = item["commit"]["committer"]["date"][:10]
        rows.append(f'| {date} | [{html.escape(repo["name"])}]({repo["html_url"]}) | [{message}]({item["html_url"]}) |')
    return "\n".join(rows) if len(rows) > 2 else "No public commits found yet."


def main():
    query = urlencode({"q": "author:sanketsingh27 is:public -repo:sanketsingh27/sanketsingh27", "sort": "committer-date", "order": "desc", "per_page": 5})
    command = ["curl", "--fail", "--silent", "--show-error", "--retry", "2", "--max-time", "30", "-H", "Accept: application/vnd.github+json"]
    if os.environ.get("GH_TOKEN"):
        command += ["-H", "Authorization: Bearer " + os.environ["GH_TOKEN"]]
    result = subprocess.run(command + ["https://api.github.com/search/commits?" + query], check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    if data.get("incomplete_results"):
        raise RuntimeError("Incomplete search; keeping previous commits")
    content = render(data["items"])
    path = ROOT / "README.md"
    original = path.read_text()
    before, remainder = original.split(START)
    _, after = remainder.split(END)
    path.write_text(before + START + "\n" + content + "\n" + END + after)


if __name__ == "__main__":
    main()
