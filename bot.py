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

# Inicializar bot
app = Client(
    "compress_ultra_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Diccionario para estados temporales
user_states = {}

# Botones del menú principal
def main_menu():
    return InlineKeyboardMarkup([
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

Bienvenido a **CompresUltra Bot V.6 Ultra Supabase**
🔥 **Comprimo tus videos con la mejor calidad**
🎬 Motor: FFmpeg + libx265

📊 Tu plan: **FREE**
🌐 Modo: Público

**Envía un video como documento o directo para comprimirlo.**

_Usa los botones de abajo para navegar_
"""
    await message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = """
**📚 Comandos Disponibles:**

**Usuario:**
/start - Bienvenida con menú
/help - Ver comandos
/miperfil - Tu perfil y estadísticas
/calidad - Cambiar calidad
/ping - Verificar si el bot responde
/velocidad - Test de velocidad
/id - Ver tu ID
/about - Info del bot

**YouTube:**
/yt [url] - Descargar video de YouTube

**APK:**
/apk [url] - Descargar APK de APKPure
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
📦 Total compresiones: **{user_data.get('total_compressions', 0)}**
💾 Total procesado: **{total_size_gb:.2f} GB**
📅 Miembro desde: **{joined_date.strftime('%d/%m/%Y')}**
"""
        await message.reply_text(profile_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("calidad"))
async def quality_command(client, message):
    await message.reply_text("**🎬 Selecciona la calidad de compresión:**", reply_markup=quality_menu(), parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("ping"))
async def ping_command(client, message):
    start = time.time()
    msg = await message.reply_text("🏓 Pong!")
    end = time.time()
    await msg.edit_text(f"🏓 **Pong!**\n⏱️ Latencia: `{(end - start) * 1000:.2f}ms`", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("velocidad"))
async def speed_command(client, message):
    msg = await message.reply_text("📊 Midiendo velocidad del servidor...")
    
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
        
        if os.path.exists(test_file):
            os.remove(test_file)
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        speed_text = f"""
**📊 Resultados del Test:**

💾 **Escritura:** `{write_speed:.2f} MB/s`
📀 **Lectura:** `{read_speed:.2f} MB/s`

**💻 Sistema:**
🖥️ CPU: `{cpu_percent}%`
🧠 RAM: `{memory.percent}%`
💿 Disco: `{disk.percent}%`

⏱️ **Test completado**
"""
        await msg.edit_text(speed_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Error en test: {str(e)}")

@app.on_message(filters.command("id"))
async def id_command(client, message):
    await message.reply_text(f"🆔 **Tu ID:** `{message.from_user.id}`", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("about"))
async def about_command(client, message):
    about_text = """
**🤖 CompresUltra Bot V.6**

🔥 Motor: **FFmpeg + libx265**
📦 Base de datos: **SQLite**
🚀 Hosting: **Render**
👤 Dev: **@Iro_dev**
"""
    await message.reply_text(about_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("yt"))
async def youtube_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Uso:** `/yt [URL]`", parse_mode=ParseMode.MARKDOWN)
        return
    
    url = message.command[1]
    msg = await message.reply_text("🔍 **Analizando video...**", parse_mode=ParseMode.MARKDOWN)
    
    try:
        info = await youtube_dl.get_video_info(url)
        if not info:
            await msg.edit_text("❌ **Error:** No se pudo obtener información del video")
            return
        
        user_states[message.from_user.id] = {'yt_url': url, 'yt_info': info}
        
        duration_min = info.get('duration', 0) // 60
        duration_sec = info.get('duration', 0) % 60
        
        info_text = f"""
**📹 Video Encontrado:**

📌 **Título:** {info.get('title', 'Unknown')[:100]}
⏱️ **Duración:** {duration_min}:{duration_sec:02d}
🎬 **Formatos:** {len(info.get('formats', []))}

**Selecciona la calidad:**
"""
        await msg.edit_text(info_text, reply_markup=youtube_format_menu(info.get('formats', [])), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ **Error:** {str(e)}")

@app.on_message(filters.command("apk"))
async def apk_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Uso:** `/apk [URL]`", parse_mode=ParseMode.MARKDOWN)
        return
    
    url = message.command[1]
    msg = await message.reply_text("🔍 **Analizando APK...**", parse_mode=ParseMode.MARKDOWN)
    
    try:
        info = await apk_dl.extract_apkpure_info(url)
        if not info:
            await msg.edit_text("❌ **Error:** No se pudo obtener información del APK")
            return
        
        info_text = f"""
**📱 APK Encontrado:**

📦 **Nombre:** {info.get('title', 'Unknown')}
📌 **Paquete:** `{info.get('package_name', 'Unknown')}`
🔄 **Versión:** {info.get('version', 'Unknown')}
💾 **Tamaño:** {info.get('size', 'Unknown')}

⏳ **Iniciando descarga...**
"""
        await msg.edit_text(info_text, parse_mode=ParseMode.MARKDOWN)
        
        apk_path = await apk_dl.download_apk(url)
        if apk_path and os.path.exists(apk_path):
            file_size = os.path.getsize(apk_path)
            await msg.edit_text(f"📤 **Subiendo APK...** ({file_size / (1024**2):.1f} MB)", parse_mode=ParseMode.MARKDOWN)
            await message.reply_document(apk_path, caption=f"✅ **{info.get('title', 'APK')}**\n📦 Versión: {info.get('version', 'Unknown')}")
            os.remove(apk_path)
            await msg.delete()
        else:
            await msg.edit_text("❌ **Error:** No se pudo descargar el APK")
    except Exception as e:
        await msg.edit_text(f"❌ **Error:** {str(e)}")

@app.on_message(filters.command("reporte"))
async def report_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Uso:** `/reporte [descripción]`", parse_mode=ParseMode.MARKDOWN)
        return
    
    report_text = " ".join(message.command[1:])
    try:
        await client.send_message(ADMIN_ID, f"**🚨 Nuevo Reporte**\n\n👤 Usuario: {message.from_user.mention}\n🆔 ID: `{message.from_user.id}`\n\n📝 **Reporte:**\n{report_text}", parse_mode=ParseMode.MARKDOWN)
        await message.reply_text("✅ **Reporte enviado.** Gracias!")
    except:
        await message.reply_text("❌ Error al enviar el reporte")

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
    
    if file_size > 200 * 1024 * 1024:
        await message.reply_text("❌ **Archivo demasiado grande** (Máx: 200MB)")
        return
    
    msg = await message.reply_text(f"📥 **Descargando video...**\n📦 Tamaño: {file_size / (1024**2):.1f} MB", parse_mode=ParseMode.MARKDOWN)
    
    download_path = await message.download("downloads/")
    if not download_path:
        await msg.edit_text("❌ **Error al descargar**")
        return
    
    await msg.edit_text("🔄 **Comprimiendo video...**\n⏳ Esto puede tomar varios minutos", parse_mode=ParseMode.MARKDOWN)
    
    output_path = f"compressed_{os.path.basename(download_path)}"
    result = await compressor.compress_video(download_path, output_path, user_data.get('quality', 'medium'))
    
    if os.path.exists(download_path):
        os.remove(download_path)
    
    if result.get('success'):
        await msg.edit_text(f"📤 **Subiendo video comprimido...**\n📊 Compresión: {result.get('compression_ratio', 0)}%", parse_mode=ParseMode.MARKDOWN)
        await message.reply_video(result['output_path'], caption=f"✅ **Comprimido con CompresUltra**\n📊 Reducción: {result.get('compression_ratio', 0)}%")
        await db.update_stats(user_id, file_size)
        if os.path.exists(result['output_path']):
            os.remove(result['output_path'])
        await msg.delete()
    else:
        await msg.edit_text(f"❌ **Error en compresión:**\n{result.get('error', 'Error desconocido')}")

@app.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "profile":
        await profile_command(client, callback_query.message)
    elif data == "plan":
        user_data = await db.get_user(user_id)
        plan_text = f"**📊 Tu Plan Actual:**\n\n🎯 Plan: **{user_data.get('plan', 'FREE')}**"
        try:
            await callback_query.message.edit_text(plan_text, parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "quality":
        try:
            await callback_query.message.edit_text("**🎬 Selecciona la calidad:**", reply_markup=quality_menu(), parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data.startswith("set_"):
        quality = data.replace("set_", "")
        user_data = await db.get_user(user_id)
        if quality == "ultra" and user_data.get('plan', 'FREE') == "FREE":
            await callback_query.answer("❌ Calidad Ultra solo para Premium", show_alert=True)
            return
        await db.update_quality(user_id, quality)
        await callback_query.answer(f"✅ Calidad: {QUALITIES.get(quality, quality)}")
        try:
            await callback_query.message.edit_text(f"✅ **Calidad actualizada:** {QUALITIES.get(quality, quality)}", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data.startswith("yt_"):
        format_id = data.replace("yt_", "")
        state = user_states.get(user_id, {})
        if not state:
            await callback_query.answer("❌ Sesión expirada", show_alert=True)
            return
        try:
            await callback_query.message.edit_text("⏳ **Descargando video...**", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
        video_path = await youtube_dl.download_video(state['yt_url'], format_id, "medium")
        if video_path and os.path.exists(video_path):
            try:
                await callback_query.message.edit_text(f"📤 **Subiendo video...** ({os.path.getsize(video_path) / (1024**2):.1f} MB)", parse_mode=ParseMode.MARKDOWN)
            except:
                pass
            await callback_query.message.reply_video(video_path, caption=f"✅ **{state['yt_info'].get('title', 'Video')}**")
            os.remove(video_path)
            await callback_query.message.delete()
        else:
            try:
                await callback_query.message.edit_text("❌ **Error al descargar**")
            except:
                pass
        user_states.pop(user_id, None)
    elif data == "cancel_yt":
        user_states.pop(user_id, None)
        try:
            await callback_query.message.edit_text("❌ **Descarga cancelada**")
        except:
            pass
    elif data == "back_main":
        try:
            await callback_query.message.edit_text("**🎬 Menú Principal**\n\n_Selecciona una opción:_", reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "help":
        await help_command(client, callback_query.message)
    elif data == "dev":
        dev_text = "**👨‍💻 Desarrollador**\n\n🤖 Bot: **CompresUltra V.6**\n👤 Dev: **@Iro_dev**"
        try:
            await callback_query.message.edit_text(dev_text, parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "plans":
        plans_text = "**💎 Planes Disponibles:**\n\n**🆓 FREE:** Compresión básica\n**⭐ PREMIUM:** $5/mes - 4K y sin límites"
        try:
            await callback_query.message.edit_text(plans_text, parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "queue":
        position = await db.get_queue_position(user_id)
        try:
            await callback_query.message.edit_text(f"**📋 Cola:**\n📊 Posición: **#{position}**", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    elif data == "report":
        try:
            await callback_query.message.edit_text("**⚠️ Reportar:**\nUsa `/reporte [texto]`", parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    
    await callback_query.answer()

# Servidor web falso para Render
async def health_check(request):
    return web.Response(text="Bot is running")

async def start_web_server():
    app_web = web.Application()
    app_web.router.add_get('/', health_check)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ Servidor web iniciado en puerto {port}")

# Inicialización
async def main():
    await db.connect()
    await app.start()
    await start_web_server()
    print("✅ Bot iniciado correctamente con SQLite!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("compressed", exist_ok=True)
    app.run(main())
