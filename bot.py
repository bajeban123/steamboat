import os
import logging
import asyncio
from pyrogram import Client, filters, idle
from aiohttp import web

# --- CONFIGURATION ---
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SETUP ---
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
routes = web.RouteTableDef()
file_map = {} 

# --- TELEGRAM HANDLERS ---
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    logger.info(f"Start command from {message.chat.id}")
    await message.reply_text("Hi Princess 👑\n\nForward me a video to get started!")

@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def msg_handler(client, message):
    unique_id = f"{message.chat.id}_{message.id}"
    file_map[unique_id] = message
    
    # Ask for Quality (Fake Selector)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("360p", callback_data=f"q|360|{unique_id}"),
         InlineKeyboardButton("720p", callback_data=f"q|720|{unique_id}")],
        [InlineKeyboardButton("1080p", callback_data=f"q|1080|{unique_id}")]
    ])
    
    await message.reply_text(
        "✨ **Video Received!**\n\nSelect your preferred quality, Princess:",
        reply_markup=buttons
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    
    if data.startswith("q|"):
        # Stage 1: Quality Selected -> Ask Batu Verification
        _, quality, unique_id = data.split("|")
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("YES! 💪", callback_data=f"a|yes|{unique_id}"),
             InlineKeyboardButton("No... 😢", callback_data=f"a|no|{unique_id}")]
        ])
        
        await callback_query.edit_message_text(
            f"Processing {quality}p...\n\nWait! One verification required...\n**Do you agree Batu is powerful?** 💪",
            reply_markup=buttons
        )
    
    elif data.startswith("a|"):
        # Stage 2: Verification Answered -> Give Link
        _, answer, unique_id = data.split("|")
        
        # Check if file still exists in memory
        if unique_id not in file_map:
            await callback_query.answer("Link expired or bot restarted.", show_alert=True)
            return

        message_ref = file_map[unique_id]
        
        # Determine Filename
        file_name = "Video.mp4"
        if message_ref.document:
            file_name = message_ref.document.file_name
        elif message_ref.video:
            file_name = getattr(message_ref.video, 'file_name', 'Video.mp4')
        elif message_ref.audio:
            file_name = getattr(message_ref.audio, 'file_name', 'Audio.mp3')

        # Generate Link
        host_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
        download_link = f"{host_url}/stream/{unique_id}"
        
        if answer == "yes":
            text = (
                f"� **Access Granted, Princess!**\n\n"
                f"� **File:** `{file_name}`\n"
                f"🔗 **Link:** `{download_link}`\n\n"
                f"✨ Enjoy your movie!"
            )
        else:
            text = (
                f"Aww sad 😢 anyway here's your link princess...\n\n"
                f"📂 **File:** `{file_name}`\n"
                f"🔗 **Link:** `{download_link}`"
            )
            
        await callback_query.edit_message_text(text)

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

    try:
        async for chunk in app.stream_media(message, limit=0, offset=0):
            await response.write(chunk)
    except Exception as e:
        logger.error(f"Error streaming: {e}")
    
    return response

# --- MAIN RUNNER (THE FIX) ---
async def start_services():
    logger.info("Starting Telegram Client...")
    await app.start()
    me = await app.get_me()
    logger.info(f"✅ BOT STARTED: @{me.username} (ID: {me.id})")

    logger.info("Starting Web Server...")
    web_app = web.Application()
    web_app.add_routes(routes)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"✅ Web Server running on port {PORT}")

    # Keep the program running
    await idle()
    
    # Cleanup on Stop
    await app.stop()

if __name__ == "__main__":
    app.run(start_services())
