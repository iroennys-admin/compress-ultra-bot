import asyncio
import os
import re
import time
import psutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from datetime import datetime
from aiohttp import web
from config import *
from database import db
from youtube_handler import youtube_dl
from apk_handler import apk_dl
from compress_handler import compressor
from file_compress_handler import file_compressor

app = Client(
    "compress_ultra_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_states = {}

YOUTUBE_PATTERNS = [
    r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
    r'(https?://)?(www\.)?youtu\.be/[\w-]+',
    r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
]

def is_youtube_url(text):
    for pattern in YOUTUBE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def extract_youtube_url(text):
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
    return None

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📹 Comprimir Video", callback_data="menu_compress_video"),
         InlineKeyboardButton("📄 Comprimir Archivo", callback_data="menu_compress_file")],
        [InlineKeyboardButton("📥 Descomprimir", callback_data="menu_decompress"),
         InlineKeyboardButton("📊 Comparar Métodos", callback_data="menu_compare")],
        [InlineKeyboardButton("👤 Mi Perfil", callback_data="profile"),
         InlineKeyboardButton("📊 Mi Plan", callback_data="plan")],
        [InlineKeyboardButton("🎬 Cambiar Calidad", callback_data="quality"),
         InlineKeyboardButton("💎 Planes", callback_data="plans")],
        [InlineKeyboardButton("📋 Ver Cola", callback_data="queue"),
         InlineKeyboardButton("❓ Ayuda", callback_data="help")],
        [InlineKeyboardButton("👨‍💻 Desarrollador", callback_data="dev"),
         InlineKeyboardButton("⚠️ Reportar", callback_data="report")]
    ])

def quality_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 480p (Baja)", callback_data="set_low")],
        [InlineKeyboardButton("🔸 720p (Media)", callback_data="set_medium")],
        [InlineKeyboardButton("🔶 1080p (Alta)", callback_data="set_high")],
        [InlineKeyboardButton("💎 4K (Ultra) - Premium", callback_data="set_ultra")],
        [InlineKeyboardButton("🔙 Volver", callback_data="back_main")]
    ])

def video_compress_quality_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 480p (Baja)", callback_data="video_480p")],
        [InlineKeyboardButton("🔸 720p (Media)", callback_data="video_720p")],
        [InlineKeyboardButton("🔶 1080p (Alta)", callback_data="video_1080p")],
        [InlineKeyboardButton("💎 4K (Ultra)", callback_data="video_4k")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_compress")]
    ])

def file_compress_method_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗜️ GZIP", callback_data="comp_gzip")],
        [InlineKeyboardButton("📦 ZIP", callback_data="comp_zip")],
        [InlineKeyboardButton("📁 TAR.GZ", callback_data="comp_tar")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_compress")]
    ])

def youtube_quality_menu(info):
    buttons = []
    formats = info.get('formats', [])
    
    for fmt in formats[:10]:
        label = f"{fmt.get('resolution', 'Unknown')}"
        if fmt.get('filesize'):
            size_mb = fmt.get('filesize', 0) / (1024 * 1024)
            label += f" ({size_mb:.1f}MB)"
        res = fmt.get('resolution', '720p').replace('p', '')
        buttons.append([InlineKeyboardButton(label, callback_data=f"yt_res_{res}")])
    
    buttons.append([InlineKeyboardButton("🔊 Solo Audio", callback_data="yt_audio")])
    buttons.append([InlineKeyboardButton("🔙 Cancelar", callback_data="cancel_yt")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    await db.create_user(user.id, user.username, user.first_name)
    
    welcome_text = f"""
**¡Hola, {user.first_name}!**

Bienvenido a **CompresUltra Bot V.6**
🔥 **Comprimo tus archivos y videos**
📹 Videos: FFmpeg + libx265
📄 Archivos: GZIP, ZIP, TAR.GZ
🎬 YouTube: Cookies habilitadas

📊 Tu plan: **FREE**
🌐 Modo: Público

**Envía un video o archivo para comprimirlo.**
"""
    await message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = """
**📚 Comandos Disponibles:**

/start - Menú principal
/help - Ver comandos
/miperfil - Tu perfil
/calidad - Cambiar calidad (videos)
/ping - Verificar bot
/velocidad - Test velocidad
/id - Ver tu ID
/about - Info del bot

**Descargas:**
/yt [url] - YouTube (con calidad selectable)
/apk [url] - APKPure

**Compresión:**
/comprimir - Elegir método
/descomprimir - Descomprimir archivo
/comparar - Comparar métodos
"""
    await message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("miperfil"))
async def profile_command(client, message):
    user = message.from_user
    user_data = await db.get_user(user.id)
    
    if user_data:
        total_size_gb = user_data.get('total_size', 0) / (1024**3)
        joined_date = user_data.get('joined_date')
        if isinstance(joined_date, str):
            try:
                joined_date = datetime.fromisoformat(joined_date.replace('Z', '+00:00'))
            except:
                joined_date = datetime.now()
        elif joined_date is None:
            joined_date = datetime.now()
        
        profile_text = f"""
**👤 Perfil de {user.first_name}**

🆔 ID: `{user.id}`
📊 Plan: **{user_data.get('plan', 'FREE')}**
🎬 Calidad: **{QUALITIES.get(user_data.get('quality', 'medium'), 'Media')}**
📦 Compresiones: **{user_data.get('total_compressions', 0)}**
💾 Procesado: **{total_size_gb:.2f} GB**
📅 Miembro: **{joined_date.strftime('%d/%m/%Y')}**
"""
        await message.reply_text(profile_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("calidad"))
async def quality_command(client, message):
    await message.reply_text("**🎬 Selecciona la calidad:**", reply_markup=quality_menu(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("ping"))
async def ping_command(client, message):
    start = time.time()
    msg = await message.reply_text("🏓 Pong!")
    end = time.time()
    try:
        await msg.edit_text(f"🏓 **Pong!**\n⏱️ `{(end - start) * 1000:.2f}ms`", parse_mode=ParseMode.MARKDOWN)
    except:
        pass

@app.on_message(filters.command("velocidad"))
async def speed_command(client, message):
    msg = await message.reply_text("📊 Midiendo velocidad...")
    
    try:
        start = time.time()
        test_data = os.urandom(1024 * 1024)
        test_file = "speedtest.tmp"
        
        with open(test_file, "wb") as f:
            f.write(test_data)
        
        end = time.time()
        write_speed = 1 / (end - start) if (end - start) > 0 else 0
        
        start = time.time()
        with open(test_file, "rb") as f:
            f.read()
        end = time.time()
        read_speed = 1 / (end - start) if (end - start) > 0 else 0
        
        os.remove(test_file)
        
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        text = f"""
**📊 Resultados:**

💾 Escritura: `{write_speed:.2f} MB/s`
📀 Lectura: `{read_speed:.2f} MB/s`

🖥️ CPU: `{cpu}%`
🧠 RAM: `{mem.percent}%`
💿 Disco: `{disk.percent}%`
"""
        await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("id"))
async def id_command(client, message):
    await message.reply_text(f"🆔 `{message.from_user.id}`", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("about"))
async def about_command(client, message):
    about_text = """
**🤖 CompresUltra Bot V.6**

🔥 FFmpeg + libx265 (Videos)
🗜️ GZIP/ZIP/TAR.GZ (Archivos)
🎬 YouTube con Cookies
📦 SQLite
🚀 Render
👤 @Iro_dev
"""
    await message.reply_text(about_text, parse_mode=ParseMode.MARKDOWN)

async def safe_edit(message, text, **kwargs):
    try:
        await message.edit_text(text, **kwargs)
    except Exception:
        pass

@app.on_message(filters.text & filters.incoming)
async def auto_youtube_detect(client, message):
    if message.text and is_youtube_url(message.text):
        user_data = await db.get_user(message.from_user.id)
        if not user_data:
            await db.create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        
        url = extract_youtube_url(message.text)
        msg = await message.reply_text("🔍 Analizando video...", parse_mode=ParseMode.MARKDOWN)
        
        try:
            info = await youtube_dl.get_video_info(url)
            if not info:
                await safe_edit(msg, "❌ Error al obtener información del video", parse_mode=ParseMode.MARKDOWN)
                return
            
            user_states[message.from_user.id] = {'yt_url': url, 'yt_info': info}
            
            d = info.get('duration', 0)
            minutes = d // 60
            seconds = d % 60
            
            view_count = info.get('view_count', 0)
            views = f"👁️ {view_count:,} vistas" if view_count > 0 else ""
            
            info_text = f"""
**📹 Video Encontrado:**

📌 **{info.get('title', 'Unknown')}**
👤 {info.get('uploader', 'Unknown')}
⏱️ {minutes}:{seconds:02d}
{views}

**Selecciona la calidad:**
"""
            await safe_edit(msg, info_text, reply_markup=youtube_quality_menu(info), parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            await safe_edit(msg, f"❌ Error: {str(e)}", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("yt"))
async def youtube_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ `/yt [URL]`", parse_mode=ParseMode.MARKDOWN)
        return
    
    url = message.command[1]
    msg = await message.reply_text("🔍 Analizando video...", parse_mode=ParseMode.MARKDOWN)
    
    try:
        info = await youtube_dl.get_video_info(url)
        if not info:
            await safe_edit(msg, "❌ Error al obtener información del video", parse_mode=ParseMode.MARKDOWN)
            return
        
        user_states[message.from_user.id] = {'yt_url': url, 'yt_info': info}
        
        d = info.get('duration', 0)
        minutes = d // 60
        seconds = d % 60
        
        view_count = info.get('view_count', 0)
        if view_count > 0:
            views = f"👁️ {view_count:,} vistas"
        else:
            views = ""
        
        info_text = f"""
**📹 Video Encontrado:**

📌 **{info.get('title', 'Unknown')}**
👤 {info.get('uploader', 'Unknown')}
⏱️ {minutes}:{seconds:02d}
{views}

**Selecciona la calidad:**
"""
        await safe_edit(msg, info_text, reply_markup=youtube_quality_menu(info), parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        await safe_edit(msg, f"❌ Error: {str(e)}", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("apk"))
async def apk_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ `/apk [URL]`", parse_mode=ParseMode.MARKDOWN)
        return
    
    url = message.command[1]
    msg = await message.reply_text("🔍 Analizando APK...", parse_mode=ParseMode.MARKDOWN)
    
    try:
        info = await apk_dl.extract_apkpure_info(url)
        if not info:
            await msg.edit_text("❌ Error al obtener info")
            return
        
        info_text = f"""
**📱 APK Encontrado:**

📦 {info.get('title', 'Unknown')}
📌 `{info.get('package_name', 'Unknown')}`
🔄 {info.get('version', 'Unknown')}
💾 {info.get('size', 'Unknown')}

⏳ Descargando...
"""
        await msg.edit_text(info_text, parse_mode=ParseMode.MARKDOWN)
        
        apk_path = await apk_dl.download_apk(url)
        if apk_path and os.path.exists(apk_path):
            size = os.path.getsize(apk_path) / (1024**2)
            await msg.edit_text(f"📤 Subiendo ({size:.1f} MB)...", parse_mode=ParseMode.MARKDOWN)
            await message.reply_document(apk_path, caption=f"✅ {info.get('title', 'APK')}")
            os.remove(apk_path)
            await msg.delete()
        else:
            await msg.edit_text("❌ Error al descargar")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("reporte"))
async def report_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ `/reporte [texto]`", parse_mode=ParseMode.MARKDOWN)
        return
    
    text = " ".join(message.command[1:])
    try:
        await client.send_message(ADMIN_ID, f"**🚨 Reporte**\n👤 {message.from_user.mention}\n🆔 `{message.from_user.id}`\n\n{text}", parse_mode=ParseMode.MARKDOWN)
        await message.reply_text("✅ Enviado!")
    except:
        await message.reply_text("❌ Error")

@app.on_message(filters.video | filters.document)
async def handle_video(client, message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if not user_data:
        await message.reply_text("❌ Usa /start primero")
        return
    
    if message.video:
        file_size = message.video.file_size
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('video/'):
        file_size = message.document.file_size
    else:
        await message.reply_text("❌ **Solo acepto archivos de video**")
        return
    
    if user_id != ADMIN_ID and file_size > 200 * 1024 * 1024:
        await message.reply_text("❌ **Archivo demasiado grande** (Máx: 200MB para usuarios normales)")
        return
    
    download_path = await message.download("downloads/")
    if not download_path:
        await message.reply_text("❌ **Error al descargar**")
        return
    
    user_states[user_id] = {
        'action': 'compress_video',
        'file_path': download_path,
        'file_size': file_size
    }
    
    quality_text = f"""
**📹 Video detectado**

📦 Tamaño: {file_size / (1024**2):.1f} MB

**Selecciona la calidad de compresión:**
"""
    
    if user_id == ADMIN_ID:
        quality_text = "👑 **Modo Admin** - Sin límites\n\n" + quality_text
    
    await message.reply_text(quality_text, reply_markup=video_compress_quality_menu(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.document | filters.photo)
async def handle_file(client, message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if not user_data:
        await message.reply_text("❌ Usa /start primero")
        return
    
    if message.photo:
        file_path = await message.download("downloads/")
        file_size = message.photo.file_size
    else:
        doc = message.document
        if doc.mime_type and doc.mime_type.startswith('video/'):
            return
        file_size = doc.file_size
        file_path = await message.download("downloads/")
    
    if not file_path:
        await message.reply_text("❌ **Error al descargar**")
        return
    
    user_states[user_id] = {
        'action': 'compress_file',
        'file_path': file_path,
        'file_size': file_size
    }
    
    text = f"""
**📄 Archivo detectado**

📦 Tamaño: {file_size / (1024**2):.1f} MB

**Selecciona el método de compresión:**
"""
    await message.reply_text(text, reply_markup=file_compress_method_menu(), parse_mode=ParseMode.MARKDOWN)

async def safe_edit(message, text, **kwargs):
    try:
        await message.edit_text(text, **kwargs)
    except Exception:
        pass

async def process_video_compression(client, message, quality, user_id, file_path, file_size, user_data):
    quality_map = {
        'video_480p': 'low',
        'video_720p': 'medium',
        'video_1080p': 'high',
        'video_4k': 'ultra'
    }
    
    quality_key = quality_map.get(quality, 'medium')
    
    await safe_edit(message,
        f"🔄 **Comprimiendo video...**\n"
        f"🎬 Calidad: {QUALITIES.get(quality_key, 'Media')}\n"
        f"⏳ Espera un momento...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    output_path = f"compressed_{os.path.basename(file_path)}"
    
    try:
        result = await asyncio.wait_for(
            compressor.compress_video(file_path, output_path, quality_key, user_id),
            timeout=600
        )
    except asyncio.TimeoutError:
        await safe_edit(message, "❌ **Tiempo de compresión agotado**")
        if os.path.exists(file_path):
            os.remove(file_path)
        return
    except Exception as e:
        await safe_edit(message, f"❌ **Error:** {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    if result.get('success'):
        compressed_size_mb = result.get('compressed_size', 0) / (1024**2)
        ratio = result.get('compression_ratio', 0)
        
        await safe_edit(message,
            f"📤 **Subiendo...**\n"
            f"💾 Nuevo tamaño: {compressed_size_mb:.1f} MB\n"
            f"📊 Reducción: {ratio}%",
            parse_mode=ParseMode.MARKDOWN
        )
        
        caption = f"✅ **Comprimido con CompresUltra**\n📊 Reducción: {ratio}%"
        if user_id == ADMIN_ID:
            caption = "👑 **Admin**\n" + caption
            
        await message.reply_video(result['output_path'], caption=caption)
        
        await db.update_stats(user_id, file_size)
        
        if os.path.exists(result['output_path']):
            os.remove(result['output_path'])
    else:
        await safe_edit(message, f"❌ **Error en compresión:**\n{result.get('error', 'Error desconocido')}", parse_mode=ParseMode.MARKDOWN)

async def process_file_compression(client, message, method, user_id, file_path, file_size):
    await safe_edit(message,
        f"🔄 **Comprimiendo con {method.upper()}...**\n"
        f"⏳ Espera un momento...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        result = await asyncio.wait_for(
            file_compressor.compress_file(file_path, method=method),
            timeout=300
        )
    except asyncio.TimeoutError:
        await safe_edit(message, "❌ **Tiempo de compresión agotado**")
        if os.path.exists(file_path):
            os.remove(file_path)
        return
    except Exception as e:
        await safe_edit(message, f"❌ **Error:** {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    if result.get('success'):
        compressed_mb = result.get('compressed_size', 0) / (1024**2)
        ratio = result.get('compression_ratio', 0)
        original_mb = result.get('original_size', 0) / (1024**2)
        
        await safe_edit(message,
            f"📤 **Subiendo...**\n"
            f"📦 {original_mb:.2f} MB → {compressed_mb:.2f} MB\n"
            f"📊 Reducción: {ratio}%",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await message.reply_document(
            result['output_path'],
            caption=f"✅ **{result['method'].upper()}**\n📊 Reducción: {ratio}%"
        )
        
        if os.path.exists(result['output_path']):
            os.remove(result['output_path'])
    else:
        await safe_edit(message, f"❌ **Error:** {result.get('error', 'Error desconocido')}", parse_mode=ParseMode.MARKDOWN)

@app.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message
    
    if data.startswith("video_") and data not in ["video_480p", "video_720p", "video_1080p", "video_4k"]:
        return
    
    if data == "menu_compress_video":
        await callback_query.message.edit_text("📹 **Envía un video para comprimirlo.**", parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_compress_file":
        await callback_query.message.edit_text("📄 **Envía un archivo para comprimirlo.**", parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_decompress":
        user_states[user_id] = {'action': 'decompress'}
        await callback_query.message.edit_text("📥 **Envía el archivo comprimido para descomprimirlo.**", parse_mode=ParseMode.MARKDOWN)
    elif data == "menu_compare":
        user_states[user_id] = {'action': 'compare'}
        await callback_query.message.edit_text("📊 **Envía un archivo para comparar.**", parse_mode=ParseMode.MARKDOWN)
    elif data == "profile":
        user = callback_query.from_user
        user_data = await db.get_user(user.id)
        if user_data:
            total_size_gb = user_data.get('total_size', 0) / (1024**3)
            profile_text = f"""
**👤 Perfil de {user.first_name}**

🆔 ID: `{user.id}`
📊 Plan: **{user_data.get('plan', 'FREE')}**
📦 Compresiones: **{user_data.get('total_compressions', 0)}**
💾 Procesado: **{total_size_gb:.2f} GB**
"""
            await callback_query.message.edit_text(profile_text, parse_mode=ParseMode.MARKDOWN)
    elif data == "plan":
        user_data = await db.get_user(user_id)
        try:
            await callback_query.message.edit_text(f"**Plan:** {user_data.get('plan', 'FREE')}", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "quality":
        try:
            await callback_query.message.edit_text("**Selecciona calidad:**", reply_markup=quality_menu(), parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data.startswith("set_"):
        quality = data.replace("set_", "")
        user_data = await db.get_user(user_id)
        if quality == "ultra" and user_data.get('plan', 'FREE') == "FREE":
            await callback_query.answer("❌ Solo Premium", show_alert=True)
            return
        await db.update_quality(user_id, quality)
        await callback_query.answer(f"✅ {QUALITIES.get(quality, quality)}")
        try:
            await callback_query.message.edit_text(f"✅ Calidad: {QUALITIES.get(quality, quality)}", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data.startswith("video_"):
        state = user_states.get(user_id, {})
        if state.get('action') != 'compress_video':
            await callback_query.answer("❌ Sesión expirada", show_alert=True)
            return
        
        user_data = await db.get_user(user_id)
        await process_video_compression(
            client, message, data, user_id,
            state['file_path'], state['file_size'], user_data
        )
        user_states.pop(user_id, None)
    elif data.startswith("comp_"):
        method = data.replace("comp_", "")
        state = user_states.get(user_id, {})
        
        if state.get('action') != 'compress_file':
            await callback_query.answer("❌ Sesión expirada", show_alert=True)
            return
        
        await process_file_compression(client, message, method, user_id, state['file_path'], state['file_size'])
        user_states.pop(user_id, None)
    elif data == "cancel_compress":
        state = user_states.get(user_id, {})
        if state.get('file_path') and os.path.exists(state['file_path']):
            os.remove(state['file_path'])
        user_states.pop(user_id, None)
        try:
            await callback_query.message.edit_text("❌ Compresión cancelada")
        except:
            pass
    elif data.startswith("yt_res_"):
        resolution = data.replace("yt_res_", "")
        state = user_states.get(user_id, {})
        
        if not state:
            await callback_query.answer("❌ Sesión expirada", show_alert=True)
            return
        
        await safe_edit(callback_query.message, f"⏳ Descargando {resolution}p...", parse_mode=ParseMode.MARKDOWN)
        
        video_path = await youtube_dl.download_video(state['yt_url'], quality=f"{resolution}p")
        
        if video_path and os.path.exists(video_path):
            size = os.path.getsize(video_path) / (1024**2)
            await safe_edit(callback_query.message, f"📤 Subiendo ({size:.1f} MB)...", parse_mode=ParseMode.MARKDOWN)
            await callback_query.message.reply_video(video_path, caption=f"✅ {state['yt_info'].get('title', 'Video')}")
            os.remove(video_path)
            await callback_query.message.delete()
        else:
            await safe_edit(callback_query.message, "❌ Error al descargar", parse_mode=ParseMode.MARKDOWN)
        
        user_states.pop(user_id, None)
    elif data == "yt_audio":
        state = user_states.get(user_id, {})
        
        if not state:
            await callback_query.answer("❌ Sesión expirada", show_alert=True)
            return
        
        await safe_edit(callback_query.message, "⏳ Descargando audio...", parse_mode=ParseMode.MARKDOWN)
        
        video_path = await youtube_dl.download_video(state['yt_url'], format_id="bestaudio")
        
        if video_path and os.path.exists(video_path):
            size = os.path.getsize(video_path) / (1024**2)
            await safe_edit(callback_query.message, f"📤 Subiendo ({size:.1f} MB)...", parse_mode=ParseMode.MARKDOWN)
            await callback_query.message.reply_document(video_path, caption=f"🎵 {state['yt_info'].get('title', 'Audio')}")
            os.remove(video_path)
            await callback_query.message.delete()
        else:
            await safe_edit(callback_query.message, "❌ Error al descargar", parse_mode=ParseMode.MARKDOWN)
        
        user_states.pop(user_id, None)
    elif data == "cancel_yt":
        user_states.pop(user_id, None)
        try:
            await callback_query.message.edit_text("❌ Cancelado")
        except:
            pass
    elif data == "back_main":
        try:
            await callback_query.message.edit_text("**Menú Principal**", reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "help":
        await help_command(client, callback_query.message)
    elif data == "dev":
        try:
            await callback_query.message.edit_text("**👤 @Iro_dev**", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "plans":
        try:
            await callback_query.message.edit_text("**💎 FREE:** Básico\n**⭐ PREMIUM:** $5/mes - 4K\n\n**👑 Admin:** Sin límites", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "queue":
        pos = await db.get_queue_position(user_id)
        try:
            await callback_query.message.edit_text(f"📊 Posición: **#{pos}**", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "report":
        try:
            await callback_query.message.edit_text("Usa `/reporte [texto]`", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    
    await callback_query.answer()

async def health_check(request):
    return web.Response(text="OK")

async def start_web_server():
    app_web = web.Application()
    app_web.router.add_get('/', health_check)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ WEB: Puerto {port}")

async def main():
    await start_web_server()
    await asyncio.sleep(2)
    
    await db.connect()
    
    await app.start()
    print("✅ BOT: Iniciado!")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("compressed", exist_ok=True)
    app.run(main())