# Comms Ops Tracker

A real-time comms operations tracker for LE-5, LE-3, LEAC, and JG — built with Streamlit, synced via GitHub.

---

## Deploy in 10 minutes

### Step 1 — Create a GitHub repo

1. Go to [github.com/new](https://github.com/new)
2. Name it `comms-ops-tracker`
3. Set it to **Private**
4. Click **Create repository**
5. Upload all files from this folder into the repo (drag and drop on GitHub works)

Make sure the folder structure looks like this:
```
comms-ops-tracker/
├── app.py
├── requirements.txt
├── .gitignore
├── data/
│   └── events.json
└── .streamlit/
    └── secrets.toml   ← DO NOT upload this (it's in .gitignore)
```

### Step 2 — Create a GitHub Personal Access Token

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Name it: `comms-ops-tracker`
4. Expiration: 1 year
5. Check the **repo** scope (full repo access)
6. Click **Generate token**
7. **Copy the token** — you won't see it again

### Step 3 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your `comms-ops-tracker` repo
5. Main file path: `app.py`
6. Click **Advanced settings → Secrets**
7. Paste this (fill in your values):

```toml
GITHUB_TOKEN  = "ghp_your_token_here"
GITHUB_REPO   = "your-github-username/comms-ops-tracker"
GITHUB_BRANCH = "main"
```

8. Click **Deploy**

Streamlit will give you a URL like `https://your-app.streamlit.app`

### Step 4 — Share with your team

Send the URL. That's it. Everyone who opens it sees the same live data.

---

## How syncing works

- Every status change, owner assignment, or flag **immediately writes to `data/events.json`** in your GitHub repo
- The next person who loads the page (or clicks Refresh) sees the updated data
- You can also see all changes in GitHub's commit history — full audit trail

## Adding next month's events

Either use the **＋ Add event** button in the app, or directly edit `data/events.json` in GitHub.

---

## Local development (optional)

```bash
pip install -r requirements.txt
# Create .streamlit/secrets.toml with your values
streamlit run app.py
```
