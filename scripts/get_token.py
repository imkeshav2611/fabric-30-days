#!/usr/bin/env python3
"""One-time LinkedIn sign-in. Run on your Mac every ~60 days:  python3 scripts/get_token.py

Opens LinkedIn in your browser. After you click Allow, the access token goes straight into the
GitHub repository's secrets. It is never printed and never written to disk.

Needs: .env with LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET, the GitHub CLI (gh) signed in,
and this redirect URL added on the LinkedIn app's Auth tab:  http://localhost:8765/callback
"""
import datetime, http.server, json, pathlib, secrets, subprocess, sys, urllib.parse, urllib.request, webbrowser

ROOT = pathlib.Path(__file__).resolve().parent.parent
REDIRECT = "http://localhost:8765/callback"
SCOPES = "openid profile w_member_social"

env = dict(l.strip().split("=", 1) for l in (ROOT / ".env").read_text().splitlines() if "=" in l and not l.startswith("#"))
cid, csec = env["LINKEDIN_CLIENT_ID"], env["LINKEDIN_CLIENT_SECRET"]
repo = json.loads((ROOT / "series.json").read_text())["repo"]
state, result = secrets.token_urlsafe(16), {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        result.update({k: v[0] for k, v in q.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Done. You can close this tab and go back to the terminal.</h2>")

    def log_message(self, *a):
        pass


url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(
    {"response_type": "code", "client_id": cid, "redirect_uri": REDIRECT, "state": state, "scope": SCOPES})
print("Opening LinkedIn in your browser. Sign in and click Allow.")
webbrowser.open(url)
srv = http.server.HTTPServer(("localhost", 8765), Handler)
while "code" not in result and "error" not in result:
    srv.handle_request()
if "error" in result or result.get("state") != state:
    sys.exit(f"Sign-in failed: {result.get('error_description') or result.get('error') or 'state mismatch'}")

form = urllib.parse.urlencode({"grant_type": "authorization_code", "code": result["code"], "redirect_uri": REDIRECT,
                               "client_id": cid, "client_secret": csec}).encode()
tok = json.load(urllib.request.urlopen(urllib.request.Request("https://www.linkedin.com/oauth/v2/accessToken", data=form)))
me = json.load(urllib.request.urlopen(urllib.request.Request("https://api.linkedin.com/v2/userinfo",
                                                             headers={"Authorization": "Bearer " + tok["access_token"]})))
expires = (datetime.date.today() + datetime.timedelta(seconds=tok["expires_in"])).isoformat()


def gh(*args, stdin=None):
    subprocess.run(["gh", *args, "--repo", repo], input=stdin, text=True, check=True, stdout=subprocess.DEVNULL)


gh("secret", "set", "LINKEDIN_ACCESS_TOKEN", stdin=tok["access_token"])
gh("secret", "set", "LINKEDIN_PERSON_URN", stdin="urn:li:person:" + me["sub"])
gh("variable", "set", "LINKEDIN_TOKEN_EXPIRES", "--body", expires)
print(f"Signed in as {me.get('name', 'you')}. Token saved to GitHub secrets for {repo}. It expires on {expires}.")
