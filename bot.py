import asyncio
import os
import time
import psutil
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from datetime import datetime  # AÑADIDO AQUÍ
from config import *
from database import db
from youtube_handler import youtube_dl
from apk_handler import apk_dl
from compress_handler import compressor
import aiofiles
import subprocess

# Inicializar bot
app = Client(
    "compress_ultra_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Diccionario para estados temporales
user_states = {}
download_tasks = {}

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

# Botones de calidad
def quality_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 480p (Baja)", callback_data="set_low")],
        [InlineKeyboardButton("🔸 720p (Media)", callback_data="set_medium")],
        [InlineKeyboardButton("🔶 1080p (Alta)", callback_data="set_high")],
        [InlineKeyboardButton("💎 4K (Ultra) - Premium", callback_data="set_ultra")],
        [InlineKeyboardButton("🔙 Volver", callback_data="back_main")]
    ])

# Botones de YouTube
def youtube_format_menu(formats):
    buttons = []
    for fmt in formats[:8]:  # Máximo 8 botones
        label = f"{fmt['resolution']} - {fmt['ext']}"
        if fmt.get('filesize'):
            size_mb = fmt['filesize'] / (1024 * 1024)
            label += f" ({size_mb:.1f}MB)"
        buttons.append([InlineKeyboardButton(
            label, 
            callback_data=f"yt_{fmt['format_id']}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Cancelar", callback_data="cancel_yt")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    
    # Crear usuario en DB
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
    
    await message.reply_text(
        welcome_text,
        reply_markup=main_menu(),
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = """
**📚 Comandos Disponibles:**

**Usuario:**
/start - Bienvenida con menú
/help - Ver comandos
/miperfil - Tu perfil y estadísticas
/miplan - Tu plan con días restantes
/planes - Ver planes disponibles
/micalidad - Tu calidad actual
/calidad - Cambiar calidad (menú visual)
/cola - Ver estado de la cola
/cancelar - Cancelar tu compresión
/reporte [texto] - Reportar un problema
/id - Ver tu ID
/about - Info del bot
/ping - Verificar si el bot responde
/velocidad - Test de velocidad

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
        
        # Manejar diferentes formatos de fecha
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
    await message.reply_text(
        "**🎬 Selecciona la calidad de compresión:**",
        reply_markup=quality_menu(),
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command("ping"))
async def ping_command(client, message):
    start_time = time.time()
    msg = await message.reply_text("🏓 Pong!")
    end_time = time.time()
    
    await msg.edit_text(
        f"🏓 **Pong!**\n"
        f"⏱️ Latencia: `{(end_time - start_time) * 1000:.2f}ms`\n"
        f"✅ Bot está operativo",
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command("velocidad"))
async def speed_command(client, message):
    msg = await message.reply_text("📊 Midiendo velocidad del servidor...")
    
    try:
        # Medir velocidad de descarga
        start = time.time()
        test_data = os.urandom(1024 * 1024)  # 1MB
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
        
        # Obtener info del sistema
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        speed_text = f"""
**📊 Resultados del Test:**

💾 **Escritura:** `{write_speed:.2f} MB/s`
📀 **Lectura:** `{read_speed:.2f} MB/s`

**💻 Sistema:**
🖥️ CPU: `{cpu_percent}%`
🧠 RAM: `{memory.percent}%` (Libre: `{memory.available / (1024**3):.1f}GB`)
💿 Disco: `{disk.percent}%` (Libre: `{disk.free / (1024**3):.1f}GB`)

⏱️ **Test completado**
"""
        await msg.edit_text(speed_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Error en test: {str(e)}")

@app.on_message(filters.command("yt"))
async def youtube_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Uso:** `/yt [URL de YouTube]`", parse_mode=ParseMode.MARKDOWN)
        return
    
    url = message.command[1]
    msg = await message.reply_text("🔍 **Analizando video de YouTube...**", parse_mode=ParseMode.MARKDOWN)
    
    try:
        info = await youtube_dl.get_video_info(url)
        
        if not info:
            await msg.edit_text("❌ **Error:** No se pudo obtener información del video")
            return
        
        # Guardar info en estado temporal
        user_states[message.from_user.id] = {
            'yt_url': url,
            'yt_info': info
        }
        
        duration_min = info.get('duration', 0) // 60
        duration_sec = info.get('duration', 0) % 60
        
        info_text = f"""
**📹 Video Encontrado:**

📌 **Título:** {info.get('title', 'Unknown')[:100]}
⏱️ **Duración:** {duration_min}:{duration_sec:02d}
🎬 **Formatos disponibles:** {len(info.get('formats', []))}

**Selecciona la calidad:**
"""
        
        await msg.edit_text(
            info_text,
            reply_markup=youtube_format_menu(info.get('formats', [])),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await msg.edit_text(f"❌ **Error:** {str(e)}")

@app.on_message(filters.command("apk"))
async def apk_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Uso:** `/apk [URL de APKPure]`", parse_mode=ParseMode.MARKDOWN)
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
        
        # Descargar APK
        apk_path = await apk_dl.download_apk(url)
        
        if apk_path and os.path.exists(apk_path):
            file_size = os.path.getsize(apk_path)
            
            await msg.edit_text(
                f"📤 **Subiendo APK...** ({file_size / (1024**2):.1f} MB)",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Enviar archivo
            await message.reply_document(
                apk_path,
                caption=f"✅ **{info.get('title', 'APK')}**\n📦 Versión: {info.get('version', 'Unknown')}"
            )
            
            os.remove(apk_path)
            await msg.delete()
        else:
            await msg.edit_text("❌ **Error:** No se pudo descargar el APK")
    except Exception as e:
        await msg.edit_text(f"❌ **Error:** {str(e)}")

@app.on_message(filters.command("id"))
async def id_command(client, message):
    user = message.from_user
    await message.reply_text(f"🆔 **Tu ID:** `{user.id}`", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("about"))
async def about_command(client, message):
    about_text = """
**🤖 CompresUltra Bot V.6**

🔥 Motor de compresión: **FFmpeg + libx265**
📦 Base de datos: **SQLite**
🎬 Descargas: **yt-dlp + APKPure**
🚀 Hosting: **Render**

**Desarrollador:** @Iro_dev
**Versión:** 6.0 Ultra Supabase
"""
    await message.reply_text(about_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("reporte"))
async def report_command(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Uso:** `/reporte [descripción]`", parse_mode=ParseMode.MARKDOWN)
        return
    
    report_text = " ".join(message.command[1:])
    
    # Enviar reporte al admin
    try:
        await client.send_message(
            ADMIN_ID,
            f"**🚨 Nuevo Reporte**\n\n"
            f"👤 Usuario: {message.from_user.mention}\n"
            f"🆔 ID: `{message.from_user.id}`\n\n"
            f"📝 **Reporte:**\n{report_text}",
            parse_mode=ParseMode.MARKDOWN
        )
        await message.reply_text("✅ **Reporte enviado.** Gracias por tu feedback!")
    except Exception as e:
        await message.reply_text(f"❌ Error al enviar el reporte: {str(e)}")

@app.on_message(filters.video | filters.document)
async def handle_video(client, message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if not user_data:
        await message.reply_text("❌ Usa /start primero")
        return
    
    # Verificar tipo de archivo
    if message.video:
        file_size = message.video.file_size
        file_name = message.video.file_name or f"video_{message.video.file_unique_id}.mp4"
    elif message.document:
        # Verificar que sea video
        if message.document.mime_type and not message.document.mime_type.startswith('video/'):
            await message.reply_text("❌ **Solo acepto archivos de video**")
            return
        file_size = message.document.file_size
        file_name = message.document.file_name or f"video_{message.document.file_unique_id}.mp4"
    else:
        return
    
    if file_size > 200 * 1024 * 1024:  # 200MB límite
        await message.reply_text("❌ **Archivo demasiado grande** (Máx: 200MB)")
        return
    
    msg = await message.reply_text(
        f"📥 **Descargando video...**\n"
        f"📦 Tamaño: {file_size / (1024**2):.1f} MB\n"
        f"🎬 Calidad: {QUALITIES.get(user_data.get('quality', 'medium'), 'Media')}",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Descargar archivo
    download_path = await message.download(f"downloads/")
    
    if not download_path:
        await msg.edit_text("❌ **Error al descargar el archivo**")
        return
    
    await msg.edit_text(
        f"🔄 **Comprimiendo video...**\n"
        f"⏳ Esto puede tomar varios minutos",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Comprimir video
    output_path = f"compressed_{os.path.basename(download_path)}"
    result = await compressor.compress_video(
        download_path, 
        output_path, 
        user_data.get('quality', 'medium')
    )
    
    # Limpiar archivo original
    if os.path.exists(download_path):
        os.remove(download_path)
    
    if result.get('success'):
        # Enviar video comprimido
        await msg.edit_text(
            f"📤 **Subiendo video comprimido...**\n"
            f"📊 Compresión: {result.get('compression_ratio', 0)}%\n"
            f"💾 Nuevo tamaño: {result.get('compressed_size', 0) / (1024**2):.1f} MB",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await message.reply_video(
            result['output_path'],
            caption=f"✅ **Comprimido con CompresUltra**\n"
                   f"📊 Reducción: {result.get('compression_ratio', 0)}%\n"
                   f"🎬 Calidad: {QUALITIES.get(user_data.get('quality', 'medium'), 'Media')}"
        )
        
        # Actualizar estadísticas
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
        await callback_query.answer()
        
    elif data == "plan":
        user_data = await db.get_user(user_id)
        plan_expiry = user_data.get('plan_expiry')
        if plan_expiry:
            if isinstance(plan_expiry, str):
                try:
                    plan_expiry = datetime.fromisoformat(plan_expiry.replace('Z', '+00:00'))
                except:
                    plan_expiry = None
            expiry_text = plan_expiry.strftime('%d/%m/%Y') if plan_expiry else "Nunca"
        else:
            expiry_text = "Nunca"
            
        plan_text = f"""
**📊 Tu Plan Actual:**

🎯 Plan: **{user_data.get('plan', 'FREE')}**
⏳ Expira: **{expiry_text}**
💎 Beneficios: **Compresión ilimitada**
"""
        await callback_query.message.edit_text(plan_text, parse_mode=ParseMode.MARKDOWN)
        await callback_query.answer()
        
    elif data == "quality":
        await callback_query.message.edit_text(
            "**🎬 Selecciona la calidad de compresión:**",
            reply_markup=quality_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        await callback_query.answer()
        
    elif data.startswith("set_"):
        quality = data.replace("set_", "")
        
        if quality == "ultra":
            user_data = await db.get_user(user_id)
            if user_data.get('plan', 'FREE') == "FREE":
                await callback_query.answer("❌ Calidad Ultra solo para planes Premium", show_alert=True)
                return
        
        await db.update_quality(user_id, quality)
        await callback_query.answer(f"✅ Calidad cambiada a {QUALITIES.get(quality, quality)}")
        await callback_query.message.edit_text(
            f"✅ **Calidad actualizada:** {QUALITIES.get(quality, quality)}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data.startswith("yt_"):
        format_id = data.replace("yt_", "")
        state = user_states.get(user_id, {})
        
        if not state or 'yt_url' not in state:
            await callback_query.answer("❌ Sesión expirada", show_alert=True)
            return
        
        await callback_query.message.edit_text(
            "⏳ **Descargando video de YouTube...**",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Descargar video
        video_path = await youtube_dl.download_video(
            state['yt_url'], 
            format_id, 
            "medium"
        )
        
        if video_path and os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            
            await callback_query.message.edit_text(
                f"📤 **Subiendo video...** ({file_size / (1024**2):.1f} MB)",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Enviar video
            await callback_query.message.reply_video(
                video_path,
                caption=f"✅ **{state['yt_info'].get('title', 'Video')}**"
            )
            
            os.remove(video_path)
            await callback_query.message.delete()
        else:
            await callback_query.message.edit_text("❌ **Error al descargar el video**")
        
        if user_id in user_states:
            del user_states[user_id]
        
    elif data == "cancel_yt":
        if user_id in user_states:
            del user_states[user_id]
        await callback_query.message.edit_text("❌ **Descarga cancelada**")
        await callback_query.answer()
        
    elif data == "back_main":
        await callback_query.message.edit_text(
            "**🎬 Menú Principal**\n\n_Selecciona una opción:_",
            reply_markup=main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
        await callback_query.answer()
        
    elif data == "help":
        await help_command(client, callback_query.message)
        await callback_query.answer()
        
    elif data == "dev":
        dev_text = """
**👨‍💻 Desarrollador**

🤖 Bot: **CompresUltra V.6**
👤 Dev: **@Iro_dev**
📱 Contacto: [Telegram](https://t.me/Iro_dev)

**Tecnologías:**
• Pyrogram 2.0
• FFmpeg + libx265
• SQLite
• yt-dlp
• Render.com

**Versión:** 6.0 Ultra Supabase
"""
        await callback_query.message.edit_text(dev_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        await callback_query.answer()
        
    elif data == "plans":
        plans_text = """
**💎 Planes Disponibles:**

**🆓 FREE:**
• Compresión básica (480p, 720p)
• 10 compresiones/día
• Cola pública

**⭐ PREMIUM - $5/mes:**
• Todas las calidades (hasta 4K)
• Compresiones ilimitadas
• Cola prioritaria
• Sin anuncios

**👑 ULTRA - $10/mes:**
• Todo lo de Premium
• Servidores dedicados
• Soporte prioritario 24/7
• API access

_Contacta a @Iro_dev para activar_
"""
        await callback_query.message.edit_text(plans_text, parse_mode=ParseMode.MARKDOWN)
        await callback_query.answer()
        
    elif data == "queue":
        position = await db.get_queue_position(user_id)
        queue_text = f"""
**📋 Estado de la Cola:**

📊 Posición en cola: **#{position if position else 0}**
⏳ Tiempo estimado: **{position * 2 if position else 0} minutos**

_La cola se actualiza en tiempo real_
"""
        await callback_query.message.edit_text(queue_text, parse_mode=ParseMode.MARKDOWN)
        await callback_query.answer()
        
    elif data == "report":
        await callback_query.message.edit_text(
            "**⚠️ Reportar Problema**\n\n"
            "Usa el comando:\n"
            "`/reporte [descripción del problema]`\n\n"
            "Ejemplo:\n"
            "`/reporte El video no se comprime correctamente`",
            parse_mode=ParseMode.MARKDOWN
        )
        await callback_query.answer()

# Inicialización
async def main():
    await db.connect()
    await app.start()
    print("✅ Bot iniciado correctamente con SQLite!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Crear directorios necesarios
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("compressed", exist_ok=True)
    
    app.run(main())
