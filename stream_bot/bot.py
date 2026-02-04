import os
import math
import logging
from pyrogram import Client, filters
from aiohttp import web

# --- CONFIGURATION ---
# SECURE: Read from Environment Variables (set these in Render)
API_ID = int(os.environ.get("API_ID", 0)) 
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8080))

# --- SETUP ---
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
routes = web.RouteTableDef()
file_map = {} # Stores message locations in memory

# --- TELEGRAM HANDLER ---
@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def msg_handler(client, message):
    # We use a unique ID to map the file request to this specific message
    unique_id = f"{message.chat.id}_{message.id}"
    file_map[unique_id] = message
    
    # Generate the link (Replace 'localhost' with your server URL later)
    # If running locally, it's http://localhost:8080
    # If on Render/Heroku, it's https://your-app-name.onrender.com
    host_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
    
    download_link = f"{host_url}/stream/{unique_id}"
    
    await message.reply_text(
        f"� **Your Link is Ready, Princess!**\n\n"
        f"📂 **File:** `{message.document.file_name if message.document else 'Video.mp4'}`\n"
        f"🔗 **Link:** `{download_link}`\n\n"
        f"✨ *Wait, Princess! Link is ready to be forwarded!*"
    )

# --- WEB SERVER HANDLER (THE MAGIC) ---
@routes.get("/stream/{id}")
async def stream_handler(request):
    unique_id = request.match_info['id']
    if unique_id not in file_map:
        return web.Response(status=404, text="Link expired or bot restarted, Princess.")
    
    message = file_map[unique_id]
    media = message.document or message.video or message.audio
    file_size = media.file_size
    file_name = media.file_name if hasattr(media, 'file_name') else "video.mp4"

    # Set headers so the browser knows it's a file download
    headers = {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': f'attachment; filename="{file_name}"',
        'Content-Length': str(file_size)
    }

    response = web.StreamResponse(status=200, reason='OK', headers=headers)
    await response.prepare(request)

    # STREAMING LOGIC: Download from Telegram -> Send to User immediately
    # We download in 1MB chunks to keep memory usage low
    async for chunk in app.stream_media(message, limit=0, offset=0):
        await response.write(chunk)
    
    return response

# --- RUNNER ---
if __name__ == "__main__":
    # Start Telegram Client
    app.start()
    print("Bot Started! Ready to serve, Princess.")
    
    # Start Web Server
    web_app = web.Application()
    web_app.add_routes(routes)
    web.run_app(web_app, port=PORT)
