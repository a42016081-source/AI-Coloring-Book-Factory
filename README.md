# AI Coloring Book Factory

Automated AI-powered coloring book creator with Telegram Bot, Flask Dashboard,
MongoDB, and GitHub Actions.

## What It Does

1. Generates unique coloring page images from a topic using AI.
2. Creates an interior PDF, front cover, back cover, full-wrap cover, preview PDF.
3. Generates KDP-style metadata (title, description, keywords, categories).
4. Packages everything into a downloadable ZIP.
5. Stores everything in MongoDB (settings + file metadata + history).
6. Files stored in GridFS or S3 — never in GitHub Actions scratch.
7. Controllable via Telegram bot and Web Dashboard sharing one MongoDB.

## 1. Create GitHub Account & Repo

1. Go to https://github.com → Sign Up.
2. Click **New repository** → name it `ai-coloring-book-factory` → Private → Create.
3. Upload this project (or push via git):
   ```bash
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/YOURNAME/ai-coloring-book-factory.git
   git push -u origin main