# MyFeed — personal chronological reader

A free self-hosted reader for RSS/Atom websites, blogs and YouTube channel feeds. Built for GitHub Pages and GitHub Actions, without subscriptions or API keys. Responsive layout for Windows and phones.

## Features
- Unified chronological stream, keyword search, source category filters and read/unread labels.
- RSS/Atom feeds and public YouTube feeds (`https://www.youtube.com/feeds/videos.xml?channel_id=UC...`).
- Source editor with JSON export. Replace `config.json` in the repository to save additions.
- Automatic refresh every 3 hours by GitHub Actions (may be delayed). Installable as a mobile PWA.

## Current limitations
- Facebook and Instagram: only if an independently working, permitted RSS bridge URL is available. Ordinary page/profile links cannot be read directly.
- Reddit: requires an authorized external feed service; official RSS ceased in November 2026.
- The repository is public; configured feeds, post titles, and snapshots are public. Never enter credentials or private feeds.
- Read/unread is stored per browser, not synced across devices. RSS updates are not instantaneous.
- The source editor exports a config; it does not automatically modify the repository, avoiding storing GitHub credentials in a browser.

## Deployment
1. Open **Actions**, choose **Update unified feed**, click **Run workflow**. It generates `data/feed.json`. If it fails with a permissions error, go to Settings → Actions → General → Workflow permissions, allow Read and write permissions.
2. Open **Settings → Pages**, select **Deploy from a branch**, `main`, `/(root)`, then Save.
3. Go to `https://radusirbu92-byte.github.io/myfeed/` after the Pages deployment succeeds.
4. To add feeds: open **Surse**, add them, export `config.json` and replace the same file on GitHub. Pushing the config triggers the update workflow.

## Development
Run `python collect.py` and `python -m http.server 8000`, then open localhost:8000.
