# StreamBot Setup Guide

## 1. Get API_ID and API_HASH
This connects your bot to Telegram's "User" API (allowing fast, large downloads).

1. Go to **[my.telegram.org](https://my.telegram.org)**.
2. Enter your phone number and click "Next". 
3. You will receive a code in your Telegram app (not SMS). Enter it.
4. Click on **"API development tools"**.
5. Fill in the form:
   - **App title:** `StreamBot`
   - **Shortname:** `streamer` (or anything you like)
   - **URL:** Leave empty or put `https://google.com`
   - **Platform:** Web or Desktop (doesn't fast matter)
6. Click **"Create application"**.
7. Copy the **`api_id`** and **`api_hash`**.

## 2. Get BOT_TOKEN
This creates the bot account people will chat with.

1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Click "Start" or type `/start`.
3. Send the command: `/newbot`
4. Answer the questions:
   - **Name:** Choose a display name (e.g., `My Fast Downloader`).
   - **Username:** Must end in `bot` (e.g., `FastStream_bot`).
5. BotFather will send you a long key called the **Token**. Copy it.

## 3. Deployment: Local vs. Cloud
You asked: *"Can I deploy locally and my friend in Iran use it?"*

**Short Answer:** No, not easily.

**Detailed Answer:**
- **Local (Your Laptop):** 
  - The link will look like `http://localhost:8080/...`.
  - "Localhost" means "this computer". Your friend cannot access "your computer" over the internet.
  - To make it work, you would need port forwarding or a tunnel (like ngrok), which is slow and unstable.
  - **Critical Issue:** If you close your laptop lid, the bot stops, and the download fails immediately.

- **Cloud (Render/Railway):**
  - The link will look like `https://my-bot.onrender.com/...`.
  - This is a public website available 24/7.
  - It runs on a server in a datacenter with high-speed internet.
  - It works even if your laptop is off.

**Verdict:** Use **Render** (as per the instructions). It's free and perfect for this "Pipe" architecture.

## 4. How to Deploy on Render (Free)
1. Upload the files (`bot.py`, `requirements.txt`) to a GitHub repository.
2. Go to **Render.com** -> New Web Service.
3. Connect your GitHub repo.
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `python bot.py`
6. Click **Deploy**.
7. Once active, go to **Environment Variables** in Render settings.
8. Add a variable: `RENDER_EXTERNAL_URL` -> Value: `https://your-app-name.onrender.com` (copy this from the top left of Render dashboard).
9. The bot will restart. Done!
