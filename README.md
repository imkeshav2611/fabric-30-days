# Microsoft Fabric · 30 Days

A 30-day LinkedIn carousel series, posted automatically to a personal profile.

## How it works

- `content/day-NN.txt` holds the words for each day. This is the only place to edit a post.
- `python3 build/build.py` turns every content file into `posts/day-NN/` with a PDF carousel, a caption and a title. It also checks that no slide overflows. Needs Google Chrome on a Mac.
- `.github/workflows/post.yml` runs every day and calls `scripts/post.py`, which uploads that day's PDF and caption to LinkedIn.
- `posted.json` records what has gone out, so a day is never posted twice.

## Switching it on

1. On the LinkedIn app's Auth tab, add the redirect URL `http://localhost:8765/callback`.
2. Run `python3 scripts/get_token.py`, sign in and click Allow. The token goes straight into this repository's secrets.
3. Set `start_date` in `series.json` to the date of Day 1, for example `"2026-10-19"`, then commit and push.

Posts go out from about 08:40 India time on weekdays and 10:10 on weekends. GitHub often starts scheduled jobs late, so the job retries every 30 minutes for a few hours and posts once per day. If a whole day is missed, the series shifts by one day rather than skipping a topic.

## Upkeep

- The LinkedIn token lasts about 60 days. Run `get_token.py` again before it expires. The daily job warns in its log when under a week is left.
- To test without posting, run the workflow by hand from the Actions tab with "dry_run" ticked.
- To change a post, edit its content file, run the build, commit and push.
- `LINKEDIN_VERSION` in the workflow is the LinkedIn API version. LinkedIn retires versions after about a year, so bump it if posting starts failing with a version error.

## Content rules

See `experience-bank.md`. No client or employer names, no certifications, and personal claims only from that file. Facts were checked against Microsoft Learn on 13 October 2026; see `sources.md`.
