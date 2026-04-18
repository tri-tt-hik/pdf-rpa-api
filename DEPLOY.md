# Deployment Guide — PDF RPA API

How to get your API live on the internet in ~15 minutes using Railway.

---

## Final folder structure

```
pdf_rpa_bot/
│
├── api.py                        ← FastAPI app (the product)
├── Dockerfile                    ← Container definition
├── railway.toml                  ← Railway deployment config
├── requirements.txt
├── .dockerignore
├── .env.example
│
├── rpa/                          ← Your pipeline modules (unchanged)
│   ├── extractor.py
│   ├── structurer.py
│   ├── storage.py
│   ├── logger.py
│   └── notifier.py
│
└── .github/
    └── workflows/
        └── deploy.yml            ← Auto-deploy on every git push
```

---

## Step 1 — Push to GitHub

```bash
cd pdf_rpa_bot
git init
git add .
git commit -m "Initial commit"

# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/pdf-rpa-api.git
git push -u origin main
```

---

## Step 2 — Deploy on Railway

1. Go to https://railway.app and sign up (free)
2. Click **New Project → Deploy from GitHub repo**
3. Select your `pdf-rpa-api` repository
4. Railway auto-detects the Dockerfile and starts building

That's it. Railway will give you a live URL like:
```
https://pdf-rpa-api-production.up.railway.app
```

---

## Step 3 — Set environment variables on Railway

In Railway dashboard → your service → **Variables** tab, add:

| Variable | Value |
|---|---|
| `MONGO_URI` | your MongoDB Atlas connection string (optional) |
| `SLACK_WEBHOOK_URL` | your Slack webhook (optional) |
| `EMAIL_USER` | Gmail address (optional) |
| `EMAIL_PASSWORD` | Gmail app password (optional) |
| `EMAIL_TO` | notification recipient (optional) |

Leave blank if not using — the API works without any of these.

---

## Step 4 — Auto-deploy on every push (optional)

1. In Railway dashboard → your service → **Settings → Tokens**
   → Generate a **Deploy Token**, copy it

2. In GitHub repo → **Settings → Secrets → Actions**
   → New secret: `RAILWAY_TOKEN` → paste the token

Now every `git push` to `main` auto-deploys. The GitHub Actions workflow
in `.github/workflows/deploy.yml` handles this.

---

## Step 5 — Test your live API

Open your browser:
```
https://your-app.up.railway.app/docs
```

FastAPI auto-generates an interactive UI where you can:
- Upload a PDF directly
- See the job_id returned
- Poll the status
- Fetch the full result JSON

Or test with curl:
```bash
# Upload a PDF
curl -X POST https://your-app.up.railway.app/process \
  -F "file=@yourfile.pdf"

# Response: {"job_id": "abc-123", "status": "queued"}

# Check status
curl https://your-app.up.railway.app/status/abc-123

# Fetch result when done
curl https://your-app.up.railway.app/result/abc-123
```

---

## Step 6 — Connect Power Automate Cloud

1. Go to https://make.powerautomate.com
2. New flow → **Automated cloud flow**
3. Trigger: **When a file is created (OneDrive or SharePoint)**
4. Add action: **HTTP**
   - Method: `POST`
   - URI: `https://your-app.up.railway.app/process`
   - Body: multipart with the file
5. Add action: **Parse JSON** on the response to extract `job_id`
6. Add **Do Until** loop polling `/status/{job_id}` every 5 seconds
7. Add **Send an email** action with stats from `/result/{job_id}`

Now your customer just drops a PDF in their OneDrive — the entire
pipeline runs automatically, no machine required on their end.

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `POST` | `/process` | Upload PDF → returns `job_id` |
| `GET` | `/status/{job_id}` | Check job: queued / processing / done / failed |
| `GET` | `/result/{job_id}` | Fetch full structured JSON result |
| `GET` | `/docs` | Auto-generated interactive API docs |

---

## MongoDB Atlas (free, cloud database)

To persist results across restarts (Railway containers reset on redeploy):

1. Go to https://cloud.mongodb.com → free M0 cluster
2. Create database user + whitelist `0.0.0.0/0`
3. Copy connection string:
   `mongodb+srv://user:pass@cluster.mongodb.net/pdf_rpa`
4. Set as `MONGO_URI` in Railway variables

Without this, job results are stored in memory and lost on restart.

---

## What you can tell customers

> "Upload your PDFs to SharePoint or OneDrive.
>  Our API automatically extracts all text, tables, and structure,
>  and emails you a summary with the full structured output.
>  No software to install. Works with your existing Microsoft tools."
