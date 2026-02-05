import os
import logging
from pyrogram import Client, filters
from aiohttp import web

# --- CONFIGURATION ---
# CRITICAL: Ensure these are set in your Environment Variables!
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SETUP ---
# Do not call app.start() here yet!
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
routes = web.RouteTableDef()
file_map = {} 

# --- TELEGRAM HANDLERS ---
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    logger.info(f"Start command from {message.chat.id}")
    await message.reply_text("✨ **I am alive, Princess!**\n\nForward me a video to get a stream link.")

@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def msg_handler(client, message):
    unique_id = f"{message.chat.id}_{message.id}"
    file_map[unique_id] = message
    
    # Get the URL (Auto-detects Render URL or Localhost)
    host_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
    download_link = f"{host_url}/stream/{unique_id}"
    
    await message.reply_text(
        f"� **Your Link is Ready, Princess!**\n\n"
        f"� **File:** `{message.document.file_name if message.document else 'Video.mp4'}`\n"
        f"🔗 **Link:** `{download_link}`\n\n"
        f"⚡ *Paste this link into UploadBoy 'Remote Upload' for Iran access!*"
    )

# --- WEB HANDLERS ---
@routes.get("/stream/{id}")
async def stream_handler(request):
    unique_id = request.match_info['id']
    if unique_id not in file_map:
        return web.Response(status=404, text="Link expired.")
    
    message = file_map[unique_id]
    media = message.document or message.video or message.audio
    file_name = getattr(media, 'file_name', 'video.mp4') or 'video.mp4'
    file_size = media.file_size

    headers = {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': f'attachment; filename="{file_name}"',
        'Content-Length': str(file_size)
    }

    response = web.StreamResponse(status=200, reason='OK', headers=headers)
    await response.prepare(request)

    # Stream using Pyrogram's client
    try:
        async for chunk in app.stream_media(message, limit=0, offset=0):
            await response.write(chunk)
    except Exception as e:
        logger.error(f"Error streaming: {e}")
    
    return response

# --- THE FIX: INTEGRATE STARTUP/SHUTDOWN ---
async def start_telegram_client(web_app):
    """Starts Telegram when the Web Server starts"""
    logger.info("Starting Telegram Client...")
    await app.start()
    me = await app.get_me()
    logger.info(f"✅ BOT STARTED: @{me.username} (ID: {me.id})")
    logger.info("Ready to receive messages!")

async def stop_telegram_client(web_app):
    """Stops Telegram when the Web Server stops"""
    logger.info("Stopping Telegram Client...")
    await app.stop()

# --- MAIN RUNNER ---
if __name__ == "__main__":
    # Create the Web App
    web_app = web.Application()
    web_app.add_routes(routes)
    
    # Register the startup/cleanup tasks
    web_app.on_startup.append(start_telegram_client)
    web_app.on_cleanup.append(stop_telegram_client)
    
    # Run the Web App (This now controls the loop)
    web.run_app(web_app, port=PORT)
