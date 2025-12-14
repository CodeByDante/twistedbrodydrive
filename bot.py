import os
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import firebase_admin
from firebase_admin import credentials, storage, firestore

# ================= CONFIGURACIÓN =================
API_ID = 33226415
API_HASH = "01999dae3e5348c7ab0dbcc6f7f4edc5"
BOT_TOKEN = "8517308010:AAFNVBIH5Mo3m8htxZ6JvFkfwI-U0gZJKWg"

# Configuración Firebase
FIREBASE_BUCKET = "twistedbrody-9d163.firebasestorage.app"
CREDENTIALS_PATH = "serviceAccountKey.json"

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {
        'storageBucket': FIREBASE_BUCKET
    })

bucket = storage.bucket()
db = firestore.client()

app = Client("my_bot_firebase", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================= COMANDOS =================

@app.on_message(filters.command("start"))
async def start(client, message):
    print(f"DEBUG: Start command received from {message.from_user.id}")
    
    welcome_text = (
        "👋 **Bienvenido a Entity of Brody Bot (Firebase Edition)**\n\n"
        "Subo tus archivos directamente a **Firebase Storage**.\n"
        "📂 **Carpeta:** `Entity of Brody/`\n"
        "🌍 **Acceso:** Público\n\n"
        "👇 ¡Envíame un archivo para empezar!"
    )
    
    # Botón informativo (ya no hace falta Auth)
    buttons = [
        [InlineKeyboardButton("📤 Información de Subida", callback_data="upload_info")]
    ]
    
    await message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query()
async def handle_callbacks(client, callback_query):
    data = callback_query.data
    message = callback_query.message
    
    if data == "upload_info":
        await message.reply_text(
            "ℹ️ **Cómo subir archivos:**\n\n"
            "1. Envíame cualquier Video, Foto o Documento.\n"
            "2. Si quieres **cambiarle el nombre**, escribe el nuevo nombre en el **comentario (caption)**.\n"
            "3. Lo guardaré en 'Entity of Brody' y te daré el link."
        )
    
    await callback_query.answer()

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def handle_file(client, message):
    status_msg = await message.reply_text("🔎 Buscando en caché...")
    
    # Obtener ID único y MIME
    unique_id = None
    file_id = None
    mime_type = None
    
    if message.video:
        unique_id = message.video.file_unique_id
        file_id = message.video.file_id
        mime_type = message.video.mime_type
    elif message.document:
        unique_id = message.document.file_unique_id
        file_id = message.document.file_id
        mime_type = message.document.mime_type
    elif message.audio:
        unique_id = message.audio.file_unique_id
        file_id = message.audio.file_id
        mime_type = message.audio.mime_type
    elif message.photo:
        # Foto es una lista, tomamos la más grande
        photo = message.photo
        unique_id = photo.file_unique_id
        file_id = photo.file_id
        mime_type = "image/jpeg"

    # CHEQUEAR CACHÉ EN FIRESTORE
    doc_ref = db.collection('files').document(unique_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        public_url = data.get('public_url')
        name = data.get('name', 'Archivo')
        await status_msg.edit_text(
            f"⚡ **Encontrado en Caché**\n\n"
            f"📄 **Nombre:** `{name}`\n"
            f"🌍 **Link:** [Ver Archivo]({public_url})",
            disable_web_page_preview=True
        )
        return

    # SI NO EXISTE:
    file_path = None
    try:
        await status_msg.edit_text("📥 Descargando archivo...")
        # Descarga local
        file_path = await message.download()
        await status_msg.edit_text("📤 Subiendo a Firebase Storage...")
        
        # Determinar nombre final
        original_name = os.path.basename(file_path)
        final_name = original_name
        
        if message.caption:
            name_without_ext, ext = os.path.splitext(original_name)
            if "." not in message.caption[-5:]: 
                final_name = f"{message.caption}{ext}"
            else:
                final_name = message.caption
        
        # Ruta en Firebase
        blob_path = f"Entity of Brody/{final_name}"
        blob = bucket.blob(blob_path)
        
        # Mime Type explícito
        mime_type = None
        if message.video:
            mime_type = message.video.mime_type
        elif message.document:
            mime_type = message.document.mime_type
        elif message.audio:
            mime_type = message.audio.mime_type
            
        # Subir
        blob.upload_from_filename(file_path, content_type=mime_type)
        
        # Hacer público
        blob.make_public()
        public_url = blob.public_url

        # GUARDAR EN FIRESTORE (CACHÉ)
        # Guardamos datos útiles para otros bots
        doc_data = {
            'file_unique_id': unique_id,
            'file_id': file_id,
            'name': final_name,
            'public_url': public_url,
            'mime_type': mime_type,
            'size': os.path.getsize(file_path),
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(doc_data)

        await status_msg.edit_text(
            f"✅ **Subido Exitosamente**\n\n"
            f"📄 **Nombre:** `{final_name}`\n"
            f"🌍 **Link:** [Ver Archivo]({public_url})",
            disable_web_page_preview=True
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")
    
    finally:
        if file_path and os.path.exists(file_path):
            # Reintentar borrado por bloqueo de Windows
            for i in range(5):
                try:
                    os.remove(file_path)
                    break
                except PermissionError:
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Error borrando archivo: {e}")
                    break

async def main():
    await app.start()
    
    # Configurar comandos
    try:
        await app.set_bot_commands([
            BotCommand("start", "Iniciar el bot")
        ])
    except Exception as e:
        print(f"⚠️ Error comandos: {e}")

    print("🔥 Bot Firebase Iniciado...")
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
