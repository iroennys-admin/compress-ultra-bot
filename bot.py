import asyncio
import os
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

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📹 Comprimir Video", callback_data="compress_video"),
         InlineKeyboardButton("📄 Comprimir Archivo", callback_data="compress_file")],
        [InlineKeyboardButton("📥 Descomprimir", callback_data="decompress"),
         InlineKeyboardButton("📊 Comparar Métodos", callback_data="compare_methods")],
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

def compression_method_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗜️ GZIP (Rápido)", callback_data="method_gzip")],
        [InlineKeyboardButton("📦 ZIP (Universal)", callback_data="method_zip")],
        [InlineKeyboardButton("📁 TAR.GZ (Lote)", callback_data="method_tar")],
        [InlineKeyboardButton("🔙 Volver", callback_data="back_main")]
    ])

def youtube_format_menu(formats):
    buttons = []
    for fmt in formats[:8]:
        label = f"{fmt['resolution']} - {fmt['ext']}"
        if fmt.get('filesize'):
            size_mb = fmt['filesize'] / (1024 * 1024)
            label += f" ({size_mb:.1f}MB)"
        buttons.append([InlineKeyboardButton(label, callback_data=f"yt_{fmt['format_id']}")])
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
/yt [url] - YouTube
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
📦 SQLite
🚀 Render
👤 @Iro_dev
"""
    await message.reply_text(about_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("comprimir"))
async def compress_method_command(client, message):
    user_states[message.from_user.id] = {'action': 'compress_file'}
    await message.reply_text("**📄 Selecciona el método de compresión:**", reply_markup=compression_method_menu(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("descomprimir"))
async def decompress_command(client, message):
    user_states[message.from_user.id] = {'action': 'decompress'}
    await message.reply_text("📄 **Envía el archivo comprimido para descomprimirlo.**", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("comparar"))
async def compare_command(client, message):
    user_states[message.from_user.id] = {'action': 'compare'}
    await message.reply_text("📊 **Envía un archivo para comparar todos los métodos.**", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("yt"))
async def youtube_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ `/yt [URL]`", parse_mode=ParseMode.MARKDOWN)
        return
    
    url = message.command[1]
    msg = await message.reply_text("🔍 Analizando...", parse_mode=ParseMode.MARKDOWN)
    
    try:
        info = await youtube_dl.get_video_info(url)
        if not info:
            await msg.edit_text("❌ Error al obtener info")
            return
        
        user_states[message.from_user.id] = {'yt_url': url, 'yt_info': info}
        
        d = info.get('duration', 0)
        info_text = f"""
**📹 Video Encontrado:**

📌 {info.get('title', 'Unknown')[:100]}
⏱️ {d//60}:{d%60:02d}
🎬 Formatos: {len(info.get('formats', []))}

**Selecciona calidad:**
"""
        await msg.edit_text(info_text, reply_markup=youtube_format_menu(info.get('formats', [])), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

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
    
    if user_id == ADMIN_ID:
        await message.reply_text("👑 **Modo Admin Activado** - Sin límites, máxima calidad")
    
    msg = await message.reply_text(
        f"📥 **Descargando video...**\n"
        f"📦 Tamaño: {file_size / (1024**2):.1f} MB\n"
        f"🎬 Calidad: {QUALITIES.get(user_data.get('quality', 'medium'), 'Media')}",
        parse_mode=ParseMode.MARKDOWN
    )
    
    download_path = await message.download("downloads/")
    if not download_path:
        await msg.edit_text("❌ **Error al descargar**")
        return
    
    await msg.edit_text(
        "🔄 **Comprimiendo video...**\n"
        "⏳ Esto puede tomar varios minutos",
        parse_mode=ParseMode.MARKDOWN
    )
    
    output_path = f"compressed_{os.path.basename(download_path)}"
    result = await compressor.compress_video(
        download_path, 
        output_path, 
        user_data.get('quality', 'medium'),
        user_id
    )
    
    if os.path.exists(download_path):
        os.remove(download_path)
    
    if result.get('success'):
        compressed_size_mb = result.get('compressed_size', 0) / (1024**2)
        ratio = result.get('compression_ratio', 0)
        
        await msg.edit_text(
            f"📤 **Subiendo video comprimido...**\n"
            f"📊 Compresión: {ratio}%\n"
            f"💾 Nuevo tamaño: {compressed_size_mb:.1f} MB",
            parse_mode=ParseMode.MARKDOWN
        )
        
        caption = f"✅ **Comprimido con CompresUltra**\n📊 Reducción: {ratio}%"
        if user_id == ADMIN_ID:
            caption = "👑 **Admin**\n" + caption
            
        await message.reply_video(
            result['output_path'],
            caption=caption
        )
        
        await db.update_stats(user_id, file_size)
        
        if os.path.exists(result['output_path']):
            os.remove(result['output_path'])
        await msg.delete()
    else:
        await msg.edit_text(f"❌ **Error en compresión:**\n{result.get('error', 'Error desconocido')}")

@app.on_message(filters.document | filters.photo)
async def handle_file(client, message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if not user_data:
        await message.reply_text("❌ Usa /start primero")
        return
    
    state = user_states.get(user_id, {})
    action = state.get('action', 'compress_file')
    
    if message.photo:
        file_path = await message.download("downloads/")
        is_photo = True
        file_size = message.photo.file_size
        file_name = f"photo_{message.photo.file_unique_id}.jpg"
    else:
        doc = message.document
        file_size = doc.file_size
        file_path = await message.download("downloads/")
        file_name = doc.file_name or f"file_{doc.file_unique_id}"
    
    if not file_path:
        await message.reply_text("❌ **Error al descargar**")
        return
    
    if action == 'decompress':
        msg = await message.reply_text("📤 **Descomprimiendo...**", parse_mode=ParseMode.MARKDOWN)
        
        result = await file_compressor.decompress_file(file_path)
        
        os.remove(file_path)
        
        if result.get('success'):
            output_paths = result.get('output_paths', [result.get('output_path')])
            
            await msg.edit_text("📤 **Subiendo archivos...**", parse_mode=ParseMode.MARKDOWN)
            
            for output_file in output_paths:
                if output_file and os.path.exists(output_file):
                    await message.reply_document(output_file, caption=f"✅ Descomprimido: {os.path.basename(output_file)}")
                    os.remove(output_file)
            
            await msg.delete()
        else:
            await msg.edit_text(f"❌ **Error:** {result.get('error', 'Error desconocido')}")
        
        user_states.pop(user_id, None)
        return
    
    if action == 'compare':
        msg = await message.reply_text("📊 **Comparando métodos...**", parse_mode=ParseMode.MARKDOWN)
        
        result = await file_compressor.compress_multiple_methods(file_path)
        
        os.remove(file_path)
        
        if result.get('success'):
            original_mb = result['original_size'] / (1024**2)
            text = f"**📊 Comparación de compresión:**\n\n📦 Original: {original_mb:.2f} MB\n\n"
            
            for r in result['results']:
                method = r['method']
                size_mb = r['size'] / (1024**2)
                ratio = r['ratio']
                text += f"**{method.upper()}**: {size_mb:.2f} MB ({ratio}% reducción)\n"
            
            text += f"\n🏆 **Mejor método:** {result['best_method'].upper()} ({result['best_ratio']}% reducción)"
            
            await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            
            for r in result['results']:
                if os.path.exists(r['output_path']):
                    await message.reply_document(r['output_path'], caption=f"📦 {r['method'].upper()}")
                    os.remove(r['output_path'])
        else:
            await msg.edit_text(f"❌ **Error:** {result.get('error', 'Error desconocido')}")
        
        user_states.pop(user_id, None)
        return
    
    if action.startswith('method_'):
        method = action.replace('method_', '')
    else:
        method = 'gzip'
    
    msg = await message.reply_text(
        f"📥 **Descargando archivo...**\n"
        f"📦 Tamaño: {file_size / (1024**2):.1f} MB\n"
        f"🗜️ Método: {method.upper()}",
        parse_mode=ParseMode.MARKDOWN
    )
    
    await msg.edit_text("🔄 **Comprimiendo...**", parse_mode=ParseMode.MARKDOWN)
    
    result = await file_compressor.compress_file(file_path, method=method)
    
    os.remove(file_path)
    
    if result.get('success'):
        compressed_mb = result.get('compressed_size', 0) / (1024**2)
        ratio = result.get('compression_ratio', 0)
        original_mb = result.get('original_size', 0) / (1024**2)
        
        await msg.edit_text(
            f"📤 **Subiendo archivo comprimido...**\n"
            f"📦 Original: {original_mb:.2f} MB\n"
            f"💾 Comprimido: {compressed_mb:.2f} MB\n"
            f"📊 Reducción: {ratio}%",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await message.reply_document(
            result['output_path'],
            caption=f"✅ **Comprimido con {result['method'].upper()}**\n📊 Reducción: {ratio}%"
        )
        
        if os.path.exists(result['output_path']):
            os.remove(result['output_path'])
        await msg.delete()
    else:
        await msg.edit_text(f"❌ **Error:** {result.get('error', 'Error desconocido')}")
    
    user_states.pop(user_id, None)

@app.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "profile":
        await profile_command(client, callback_query.message)
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
    elif data == "compress_video":
        try:
            await callback_query.message.edit_text("**📹 Envía un video para comprimirlo.**", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "compress_file":
        user_states[user_id] = {'action': 'compress_file'}
        try:
            await callback_query.message.edit_text("**📄 Selecciona el método de compresión:**", reply_markup=compression_method_menu(), parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "decompress":
        user_states[user_id] = {'action': 'decompress'}
        try:
            await callback_query.message.edit_text("**📥 Envía el archivo comprimido para descomprimirlo.**", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "compare_methods":
        user_states[user_id] = {'action': 'compare'}
        try:
            await callback_query.message.edit_text("**📊 Envía un archivo para comparar todos los métodos.**", parse_mode=ParseMode.MARKDOWN)
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
    elif data.startswith("method_"):
        method = data.replace("method_", "")
        user_states[user_id] = {'action': f'method_{method}'}
        await callback_query.answer(f"🗜️ Método: {method.upper()}")
        try:
            await callback_query.message.edit_text(f"**📄 Método {method.upper()} seleccionado.**\n\nEnvía un archivo para comprimirlo.", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data.startswith("yt_"):
        format_id = data.replace("yt_", "")
        state = user_states.get(user_id, {})
        if not state:
            await callback_query.answer("❌ Sesión expirada", show_alert=True)
            return
        try:
            await callback_query.message.edit_text("⏳ Descargando...", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
        video_path = await youtube_dl.download_video(state['yt_url'], format_id, "medium")
        if video_path and os.path.exists(video_path):
            size = os.path.getsize(video_path) / (1024**2)
            try:
                await callback_query.message.edit_text(f"📤 Subiendo ({size:.1f} MB)...", parse_mode=ParseMode.MARKDOWN)
            except:
                pass
            await callback_query.message.reply_video(video_path, caption=f"✅ {state['yt_info'].get('title', 'Video')}")
            os.remove(video_path)
            await callback_query.message.delete()
        else:
            try:
                await callback_query.message.edit_text("❌ Error al descargar")
            except:
                pass
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