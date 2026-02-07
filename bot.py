import os
import logging
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- CONFIGURATION ---
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SETUP ---
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
routes = web.RouteTableDef()
file_map = {} 

# --- TELEGRAM HANDLERS ---
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    logger.info(f"Start command from {message.chat.id}")
    await message.reply_text(
        "**Hello my Princess!** 👑✨\n\n"
        "I am awake and ready to serve you! 🙇\n"
        "Forward me any video, and I will make a magic link for you! 🪄"
    )

@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def msg_handler(client, message):
    unique_id = f"{message.chat.id}_{message.id}"
    file_map[unique_id] = message
    
    # "Princess" Feature 1: Fake Quality Selector
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ 360p (Data Saver)", callback_data=f"q|360|{unique_id}"),
         InlineKeyboardButton("💎 720p (HD)", callback_data=f"q|720|{unique_id}")],
        [InlineKeyboardButton("👑 1080p (Royal)", callback_data=f"q|1080|{unique_id}")]
    ])
    
    await message.reply_text(
        "**Ooh! A video for me?** 🎀\n\n"
        "How would Your Highness like to watch this today?",
        reply_markup=buttons
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    
    if data.startswith("q|"):
        _, quality, unique_id = data.split("|")
        
        # "Princess" Feature 2: Cheeky Verification
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("YES! He is! 💪❤️", callback_data=f"a|yes|{unique_id}"),
             InlineKeyboardButton("No... 🙈", callback_data=f"a|no|{unique_id}")]
        ])
        
        await callback_query.edit_message_text(
            f"Preparing {quality}p version... 🪄\n\n"
            "**Wait! Just one tiny security check...** 🛡️\n\n"
            "**Do you agree Batu is the strongest?** 🦁",
            reply_markup=buttons
        )
    
    elif data.startswith("a|"):
        _, answer, unique_id = data.split("|")
        
        if unique_id not in file_map:
            await callback_query.answer("Oh no! This link expired 🥺 Send it again?", show_alert=True)
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

        host_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
        download_link = f"{host_url}/stream/{unique_id}"
        
        if answer == "yes":
            text = (
                f"**Correct Answer!** 👑✨\n\n"
                f"Here is your Royal Link, my Princess:\n"
                f"🔗 `{download_link}`\n\n"
                f"📂 `{file_name}`\n"
                f"Enjoy your movie! 🍿🎬"
            )
        else:
            text = (
                f"**Wrong answer...** 🥺\n"
                f"But I love you anyway, so here is your link:\n"
                f"🔗 `{download_link}`\n\n"
                f"Next time say Yes! 😤❤️"
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
    mime_type = getattr(media, 'mime_type', 'application/octet-stream') or 'application/octet-stream'

    # --- RESUMABLE DOWNLOADS (Range Header Support) ---
    range_header = request.headers.get("Range")
    offset = 0
    length = file_size
    status_code = 200

    if range_header:
        try:
            # Parse Range: bytes=1000-
            parts = range_header.replace("bytes=", "").split("-")
            start_byte = int(parts[0]) if parts[0] else 0
            end_byte = int(parts[1]) if parts[1] else file_size - 1
            
            # Adjust offset and length
            offset = start_byte
            length = (end_byte - start_byte) + 1
            status_code = 206 # Partial Content
        except ValueError:
            pass # Fallback to full file if parsing fails

    headers = {
        'Content-Type': mime_type,
        'Content-Disposition': f'attachment; filename="{file_name}"',
        'Accept-Ranges': 'bytes',
        'Content-Length': str(length),
    }

    if status_code == 206:
        headers['Content-Range'] = f'bytes {offset}-{offset + length - 1}/{file_size}'

    response = web.StreamResponse(status=status_code, reason='Partial Content' if status_code == 206 else 'OK', headers=headers)
    await response.prepare(request)

    # --- STREAMING LOGIC ---
    # FUTURE UPGRADE: Insert FFmpeg piping here if we switch to VPS
    # For now, we stream directly from Telegram (Original Quality)
    
    chunk_size = 1024 * 1024 # 1MB chunks
    start_chunk_index = offset // chunk_size
    skip_bytes = offset % chunk_size
    
    try:
        first_chunk = True
        async for chunk in app.stream_media(message, limit=0, offset=start_chunk_index):
            if first_chunk:
                if skip_bytes:
                    await response.write(chunk[skip_bytes:]) # Write partial chunk
                else:
                    await response.write(chunk)
                first_chunk = False
            else:
                await response.write(chunk)
                
    except Exception as e:
        # Client disconnected (Normal behavior)
        pass 
    
    return response

# --- MAIN RUNNER ---
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

    # Keep program alive
    await idle()
    
    # Cleanup
    await app.stop()

if __name__ == "__main__":
    app.run(start_services())
