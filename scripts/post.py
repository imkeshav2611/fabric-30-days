#!/usr/bin/env python3
"""Posts today's carousel to LinkedIn. Standard library only.

Day number = days since series.json start_date (India time) + 1. Runs are safe to repeat:
a day that is already in posted.json is skipped.

Env: LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN, optional LINKEDIN_VERSION, DAY, DRY_RUN, LINKEDIN_TOKEN_EXPIRES
"""
import datetime, json, os, pathlib, re, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.linkedin.com"
RESERVED = set('\\|{}@[]()<>#*_~')


def little(text):
    """Escape LinkedIn 'little text format' reserved characters and mark up hashtags."""
    out, pos = [], 0
    for m in re.finditer(r"(?<![\w#])#(\w+)", text):
        out.append("".join("\\" + c if c in RESERVED else c for c in text[pos:m.start()]))
        out.append("{hashtag|\\#|" + m.group(1) + "}")
        pos = m.end()
    out.append("".join("\\" + c if c in RESERVED else c for c in text[pos:]))
    return "".join(out)


def call(method, url, token, body=None, raw=None, version=None):
    headers = {"Authorization": f"Bearer {token}"}
    if version:
        headers.update({"LinkedIn-Version": version, "X-Restli-Protocol-Version": "2.0.0"})
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        headers["Content-Type"] = "application/octet-stream"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            txt = r.read().decode() or "{}"
            return r.status, dict(r.headers), (json.loads(txt) if txt.lstrip().startswith("{") else {})
    except urllib.error.HTTPError as e:
        sys.exit(f"LinkedIn API error {e.code} on {method} {url.split('?')[0]}: {e.read().decode()[:600]}")


def main():
    cfg = json.loads((ROOT / "series.json").read_text())
    log_path = ROOT / "posted.json"
    log = json.loads(log_path.read_text())
    dry = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

    exp = os.environ.get("LINKEDIN_TOKEN_EXPIRES")
    if exp:
        left = (datetime.date.fromisoformat(exp) - datetime.date.today()).days
        if left <= 7:
            print(f"::warning::LinkedIn token expires in {left} days. Run scripts/get_token.py again.")

    if os.environ.get("DAY"):
        day = int(os.environ["DAY"])
    else:
        if not cfg.get("start_date"):
            print("Series not started: start_date is not set in series.json. Nothing posted.")
            return
        off = datetime.timedelta(hours=cfg["timezone_offset_hours"])
        local_now = datetime.datetime.now(datetime.timezone.utc) + off
        today = local_now.date()
        if local_now.time() < datetime.time(7, 30):
            print(f"Too early ({local_now:%H:%M} India time). Scheduled posts go out from 07:30. Nothing posted.")
            return
        due =(today - datetime.date.fromisoformat(cfg["start_date"])).days + 1
        posted_today = [k for k, v in log.items() if (datetime.datetime.fromisoformat(v["at"]) + off).date() == today]
        if posted_today:
            print(f"Already posted today (day {posted_today[0]}). Nothing posted.")
            return
        # Post the next day in order. If GitHub skipped a run, the series shifts by a day instead of leaving a gap.
        day = max([int(k) for k in log] or [0]) + 1
        if day > due:
            print(f"Day {day} is not due until later. Nothing posted.")
            return
    if day < 1 or day > cfg["total_days"]:
        print(f"Day {day} is outside the series (1 to {cfg['total_days']}). Nothing posted.")
        return
    if str(day) in log:
        print(f"Day {day} was already posted ({log[str(day)]['post']}). Nothing posted.")
        return

    folder = ROOT / "posts" / f"day-{day:02d}"
    pdf, caption, title = folder / "carousel.pdf", (folder / "caption.txt").read_text().strip(), (folder / "title.txt").read_text().strip()
    commentary = little(caption)
    print(f"Day {day}: {title} | pdf {pdf.stat().st_size // 1024} KB | caption {len(caption)} chars")
    if dry:
        print("DRY RUN. Commentary that would be sent:\n" + commentary)
        return

    token, author = os.environ["LINKEDIN_ACCESS_TOKEN"], os.environ["LINKEDIN_PERSON_URN"]
    version = os.environ.get("LINKEDIN_VERSION") or "202609"

    _, _, init = call("POST", f"{API}/rest/documents?action=initializeUpload", token, {"initializeUploadRequest": {"owner": author}}, version=version)
    doc, upload_url = init["value"]["document"], init["value"]["uploadUrl"]
    call("PUT", upload_url, token, raw=pdf.read_bytes())
    for _ in range(30):  # wait until LinkedIn has processed the PDF
        _, _, info = call("GET", f"{API}/rest/documents/{urllib.parse.quote(doc, safe='')}", token, version=version)
        if info.get("status") == "AVAILABLE":
            break
        if info.get("status") == "PROCESSING_FAILED":
            sys.exit("LinkedIn could not process the PDF.")
        time.sleep(4)
    else:
        sys.exit("Timed out waiting for LinkedIn to process the PDF.")

    post = {
        "author": author, "commentary": commentary, "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "content": {"media": {"title": title, "id": doc}},
        "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False,
    }
    _, headers, _ = call("POST", f"{API}/rest/posts", token, post, version=version)
    urn = headers.get("x-restli-id") or headers.get("X-RestLi-Id") or "unknown"
    log[str(day)] = {"post": urn, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    log_path.write_text(json.dumps(log, indent=2) + "\n")
    print(f"Posted day {day}: https://www.linkedin.com/feed/update/{urn}")


if __name__ == "__main__":
    main()
