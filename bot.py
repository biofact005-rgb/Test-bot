import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from pymongo import MongoClient
import threading
import time
import os
import random
from dotenv import load_dotenv
from datetime import datetime
import json
from telebot.types import BotCommand
from flask import Flask
import threading
import os




# --- TERMUX DNS FIX ---
import dns.resolver
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']
# ----------------------

# --- PDF WATERMARK LIBRARIES ---
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

load_dotenv()

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789")) 
DB_GROUP_ID = int(os.getenv("DB_GROUP_ID", "-100xxxxxxx"))
MONGO_URI = os.getenv("MONGO_URI")

IMAGES = {
    "home": "https://images.unsplash.com/photo-1456406644174-8ddd4cd52a06?w=800&q=80",
    "folder": "https://images.unsplash.com/photo-1611339555312-e607c8352fd7?w=800&q=80"
}

bot = telebot.TeleBot(TOKEN)




# ==========================================
# 📢 FORCE SUBSCRIBE CHANNELS
# ==========================================
# Yahan dono channels ke username daalne hain
REQUIRED_CHANNELS = ["@testbotupdate", "@errorkid_05"]

def check_subscription(user_id):
    if user_id == ADMIN_ID: return True # Admin ko check nahi karna
    try:
        for channel in REQUIRED_CHANNELS:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except Exception as e:
        print(f"Sub Check Error: {e}")
        return False # Agar koi error aaye (bot admin na ho), toh False return karega

def send_force_sub_msg(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/testbotupdate"))
    markup.row(InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/errorkid_05"))
    markup.row(InlineKeyboardButton("✅ I Have Joined", callback_data="check_sub"))
    
    msg = (
        "🛑 <b>ACCESS DENIED!</b> 🛑\n\n"
        "Premium Test Papers aur mock tests download karne ke liye, "
        "kripya humare dono official channels ko join karein.\n\n"
        "<i>👇 Join karne ke baad 'I Have Joined' par click karein.</i>"
    )
    bot.send_message(chat_id, msg, parse_mode='HTML', reply_markup=markup)




# ==========================================
# 💾 MONGODB SETUP
# ==========================================
client = MongoClient(MONGO_URI)
db = client['test_paper_bot_vip']
users_col = db['users']
folders_col = db['folders'] 
papers_col = db['papers']   

# Root folder initialize karna
if not folders_col.find_one({"_id": "root"}):
    folders_col.insert_one({"_id": "root", "name": "Main Menu", "parent_id": None})

def gen_id(prefix):
    return f"{prefix}-{int(time.time())}-{random.randint(10,99)}"

# ==========================================
# ⏱️ 10-MIN AUTO DELETE & WATERMARK
# ==========================================
def delete_message_later(chat_id, message_id):
    time.sleep(600) 
    try:
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "⚠️ <b>A test paper was auto-deleted for security.</b>", parse_mode='HTML')
    except: pass

# ==========================================
# 💧 PDF WATERMARK ENGINE (REFINED VISIBILITY)
# ==========================================
# ==========================================
# 💧 PDF WATERMARK ENGINE (REFINED VISIBILITY)
# ==========================================
# ==========================================
# 💧 PDF WATERMARK ENGINE (TRUE TRANSPARENCY)
# ==========================================
def create_watermark(width, height):
    pdf = FPDF(unit='pt', format=[width, height])
    pdf.set_auto_page_break(False, margin=0) 
    pdf.add_page()
    
    # --- 1. CENTER DIAGONAL WATERMARK (@errorkidk) ---
    pdf.set_font("helvetica", style="B", size=65)
    
    center_x = width / 2
    center_y = height / 2
    
    # 🚨 FIX: ASLI TRANSPARENCY (Opacity) YAHAN HAI
    # fill_opacity=0.15 ka matlab 15% text dikhega, 85% transparent rahega.
    # Peeche ka Allen ka question ekdum clear padhne me aayega!
    with pdf.local_context(fill_opacity=0.15):
        pdf.set_text_color(0, 0, 0) # Black color with 85% transparency looks best
        with pdf.rotation(45, x=center_x, y=center_y):
            text = "@errorkidk"
            text_width = pdf.get_string_width(text)
            pdf.set_xy(center_x - (text_width / 2), center_y - 30)
            pdf.cell(text_width, 60, text=text, align='C')
            
    # --- 2. BOTTOM CLEAN CLICKABLE HYPERLINK ---
    # Isme transparency nahi lagayi taaki link ekdum bright aur clickable rahe
    pdf.set_font("helvetica", style="B", size=13)
    pdf.set_text_color(0, 0, 255) # Blue link
    pdf.set_y(height - 40)
    
    bottom_text = "Click Here For More PDFs & Mock Tests"
    link_url = "https://t.me/ERTESTPAPERBOT"
    
    pdf.cell(0, 10, text=bottom_text, align='C', link=link_url)
    
    pdf.output("watermark_temp.pdf")




def add_watermark(input_pdf, output_pdf):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    # Original PDF ka size nikalna
    first_page = reader.pages[0]
    width = float(first_page.mediabox.width)
    height = float(first_page.mediabox.height)
    
    # Watermark generate karna
    create_watermark(width, height)
    
    # Watermark read karna
    watermark_reader = PdfReader("watermark_temp.pdf")
    watermark_page = watermark_reader.pages[0]
    
    # Har page par watermark chipkana
    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)
        
    # Final PDF save karna
    with open(output_pdf, "wb") as f:
        writer.write(f)
        
    # Temp file delete karna
    if os.path.exists("watermark_temp.pdf"):
        os.remove("watermark_temp.pdf")





# ==========================================
# 🖼️ PREMIUM DYNAMIC UI GENERATOR
# ==========================================


def get_neet_countdown():
    # Target: 3 May 2026, 14:30 (2:30 PM)
    target = datetime(2026, 5, 3, 14, 30)
    now = datetime.now()
    
    if now > target:
        return "Exam Day! All the Best! 🎯"
        
    diff = target - now
    days = diff.days
    hours = diff.seconds // 3600
    return f"{days} Days, {hours} Hours"


def get_folder_ui(user_id, first_name, folder_id="root", is_admin=False):
    current_folder = folders_col.find_one({"_id": folder_id})
    if not current_folder: return None, None, None
    
    subfolders = list(folders_col.find({"parent_id": folder_id}))
    papers = list(papers_col.find({"folder_id": folder_id}))
    
    # 📌 UI Titles (Small Caps font pehle se add kar diya hai)
    title = current_folder.get("title", "🏆 <b>Pʀᴇᴍɪᴜᴍ Tᴇsᴛ Sᴇʀɪᴇs Pᴏʀᴛᴀʟ</b> 🏆")
    bottom_text = current_folder.get("bottom_text", "⚡ <i>Nᴇᴇᴄʜᴇ sᴇ ᴀᴘɴᴀ Tᴇsᴛ Pᴀᴘᴇʀ sᴇʟᴇᴄᴛ ᴋᴀʀᴇɪɴ:</i>")
    default_img = IMAGES['home'] if folder_id == "root" else IMAGES['folder']
    img = current_folder.get("photo", default_img)
    
    # 🎨 THEME LOGIC
    theme_color = "primary" if folder_id == "root" else "success"
    
    
        # ==========================================
    # 👤 1. GLOBAL INFO BLOCK (Bina blockquote tag ke)
    # ==========================================
    user_count = users_col.count_documents({})
    timer = get_neet_countdown()
    
    global_info = (
        f"👤 <b>Sᴛᴜᴅᴇɴᴛ:</b> {first_name}\n"
        f"🆔 <b>Usᴇʀ ID:</b> <code>{user_id}</code>\n"
        f"👥 <b>Lɪᴠᴇ Asᴘɪʀᴀɴᴛs:</b> <code>{user_count}</code>\n"
        f"⏳ <b>Nᴇᴇᴛ Cᴏᴜɴᴛᴅᴏᴡɴ:</b> <code>{timer}</code>"
    )
    
    # ==========================================
    # 📂 2. PATH GENERATOR (Tree/Branch Format)
    # ==========================================
    path_names = []
    curr = folder_id
    
    while curr and curr != "root":
        f = folders_col.find_one({"_id": curr})
        if f:
            path_names.append(f['name'])
            curr = f.get('parent_id')
        else:
            break
            
    path_names.reverse()
    
    if folder_id == "root":
        path_text = "📂 <b>Pᴀᴛʜ:</b> Hᴏᴍᴇ"
    else:
        path_text = "📂 <b>Hᴏᴍᴇ</b>\n"
        space = ""
        for name in path_names:
            path_text += f"{space}  ╰── <b>{name}</b>\n"
            space += "      "
        path_text = path_text.rstrip() # Last wali extra empty line hatane ke liye
        
    # ==========================================
    # 📝 FINAL CAPTION BANA NA (SINGLE BOX FIX)
    # ==========================================
    # Ab dono cheezon ko ek hi <blockquote> tag ke andar daal diya hai
    caption = (
        f"{title}\n\n"
        f"<blockquote>{global_info}\n"
        f"━━━━━━━━━━━━━━\n" # Ye ek premium divider line hai
        f"{path_text}</blockquote>\n\n"
        f"{bottom_text}"
    )

    
    # ==========================================
    # 🔘 BUTTONS RENDER LOGIC
    # ==========================================
    markup = InlineKeyboardMarkup()
    
    if is_admin:
        markup.row(
            InlineKeyboardButton("➕ Add Folder", callback_data=f"addf_{folder_id}", style=theme_color), 
            InlineKeyboardButton("📤 Upload Paper", callback_data=f"addp_{folder_id}", style=theme_color)
        )
        markup.row(InlineKeyboardButton("🎨 Edit Page UI", callback_data=f"editui_{folder_id}", style=theme_color))
        if folder_id != "root":
            markup.row(InlineKeyboardButton("🗑️ Delete This Folder", callback_data=f"delf_{folder_id}", style="danger"))
            
    folder_btns = [InlineKeyboardButton(f"📁 {f['name']}", callback_data=f"{'adf_' if is_admin else 'vwf_'}{f['_id']}", style=theme_color) for f in subfolders]
    for btn in folder_btns:
        markup.row(btn)
        
    for p in papers:
        if is_admin: 
            markup.row(
                InlineKeyboardButton(f"📄 {p['name']}", callback_data=f"delp_{p['_id']}", style=theme_color), 
                InlineKeyboardButton("❌", callback_data=f"delp_{p['_id']}", style="danger")
            ) 
        else: 
            markup.row(InlineKeyboardButton(f"📄 {p['name']}", callback_data=f"getp_{p['_id']}", style=theme_color))
            
    if folder_id == "root":
        markup.row(InlineKeyboardButton("ℹ️ Help & Bot Rules", callback_data="help_page", style=theme_color))
    elif folder_id != "root":
        back_id = current_folder.get('parent_id', 'root')
        markup.row(InlineKeyboardButton("🔙 Back", callback_data=f"{'adf_' if is_admin else 'vwf_'}{back_id}", style="danger"))
        
    return img, caption, markup





# ==========================================
# 👑 ADMIN COMMANDS & CMS ACTIONS
# ==========================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    img, caption, markup = get_folder_ui(message.from_user.id, "Admin", "root", is_admin=True)
    bot.send_photo(message.chat.id, photo=img, caption=caption, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['resetui'])
def reset_ui(message):
    if message.from_user.id != ADMIN_ID: return
    
    # Ye command database se saare custom title aur text hata dega (Reset to default)
    folders_col.update_many({}, {"$unset": {"title": "", "bottom_text": "", "photo": ""}})
    
    bot.reply_to(message, "🛠️ <b>Emergency Fix Applied!</b>\nSabhi folders ka UI default par set ho gaya hai. Ab koi crash nahi hoga.", parse_mode='HTML')



@bot.message_handler(commands=['end'])
def end_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.split()[1])
        users_col.update_one({"_id": target_id}, {"$set": {"access": False}}, upsert=True)
        bot.reply_to(message, f"✅ User {target_id} access ended.")
    except:
        bot.reply_to(message, "⚠️ Format: /end <user_id>")


# ==========================================
# 👑 PRO ADMIN COMMANDS
# ==========================================

# 📊 1. ADMIN STATUS
@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID: return
    u_count = users_col.count_documents({})
    f_count = folders_col.count_documents({})
    p_count = papers_col.count_documents({})
    bot.reply_to(message, f"📊 <b>BOT SYSTEM STATUS</b>\n\n👥 Total Users: {u_count}\n📁 Total Folders: {f_count}\n📄 Total Papers: {p_count}", parse_mode='HTML')

# 📢 2. BROADCAST MESSAGE
@bot.message_handler(commands=['broadcast'])
def broadcast_msg(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/broadcast ", "")
    if text == "/broadcast":
        return bot.reply_to(message, "⚠️ Format: /broadcast <message>")
    
    users = users_col.find({})
    success, failed = 0, 0
    msg = bot.reply_to(message, "⏳ Broadcasting message to all aspirants...")
    
    for u in users:
        try:
            bot.send_message(u['_id'], text, parse_mode='HTML')
            success += 1
        except:
            failed += 1
            
    bot.edit_message_text(f"✅ <b>Broadcast Complete!</b>\n\n🟢 Sent: {success}\n🔴 Failed (Blocked bot): {failed}", chat_id=message.chat.id, message_id=msg.message_id, parse_mode='HTML')

# 💾 3. BACKUP DATABASE
@bot.message_handler(commands=['backup'])
def backup_db(message):
    if message.from_user.id != ADMIN_ID: return
    bot.reply_to(message, "⏳ Generating JSON Backup...")
    
    # Folders aur Papers ka data JSON me convert karna
    data = {
        "folders": list(folders_col.find({}, {"_id": 1, "name": 1, "parent_id": 1, "photo": 1, "title": 1, "bottom_text": 1})),
        "papers": list(papers_col.find({}, {"_id": 1, "name": 1, "file_id": 1, "folder_id": 1}))
    }
    
    with open("bot_backup.json", "w") as f:
        json.dump(data, f)
        
    with open("bot_backup.json", "rb") as f:
        bot.send_document(message.chat.id, f, caption="💾 <b>Database Backup</b>\nKeep this file safe. Use /recover to restore.", parse_mode='HTML')
        
    os.remove("bot_backup.json")

# 🔄 4. RECOVER DATABASE
@bot.message_handler(commands=['recover'])
def recover_db(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, "📤 <b>Send me the 'bot_backup.json' file to restore data:</b>", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_recovery)

def process_recovery(message):
    if not message.document or not message.document.file_name.endswith('.json'):
        return bot.reply_to(message, "❌ Invalid file. Recovery Cancelled.")
        
    bot.reply_to(message, "⏳ Restoring Database...")
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    data = json.loads(downloaded_file)
    
    # Purana data delete karke naya insert karna (Overwriting)
    folders_col.delete_many({})
    papers_col.delete_many({})
    
    if data.get("folders"): folders_col.insert_many(data["folders"])
    if data.get("papers"): papers_col.insert_many(data["papers"])
    
    bot.send_message(message.chat.id, "✅ <b>Database Successfully Recovered!</b> All folders and papers are back.", parse_mode='HTML')



# --- FOLDER & PAPER UPLOAD HANDLERS ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("addf_") or call.data.startswith("addp_"))
def admin_add_actions(call):
    action, folder_id = call.data.split("_", 1)
    if action == "addf":
        msg = bot.send_message(call.message.chat.id, "✏️ <b>Enter Folder Name (e.g., Major Tests):</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_new_folder, folder_id)
    elif action == "addp":
        msg = bot.send_message(call.message.chat.id, "📤 <b>Send the Test Paper PDF now:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_new_paper, folder_id)

def process_new_folder(message, parent_id):
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    if not message.text: # Safety Check
        return bot.send_message(message.chat.id, "❌ Please enter a valid name. Try again.")
    new_id = gen_id("f")
    folders_col.insert_one({"_id": new_id, "name": message.text.strip(), "parent_id": parent_id})
    img, caption, markup = get_folder_ui(message.from_user.id, "Admin", parent_id, is_admin=True)
    bot.send_photo(message.chat.id, photo=img, caption=caption, parse_mode='HTML', reply_markup=markup)


def process_new_paper(message, folder_id):
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    
    if message.document and message.document.mime_type == 'application/pdf':
        
        # 🚨 FIX 1: Size check (Telegram limit is 20MB)
        if message.document.file_size > 20 * 1024 * 1024:
            return bot.send_message(message.chat.id, "❌ <b>File 20MB se badi hai!</b> Telegram API isse download nahi kar sakti.", parse_mode='HTML')
            
        loading_msg = bot.send_message(message.chat.id, "⏳ <b>Adding Watermark to PDF...</b>", parse_mode='HTML')
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_pdf = f"temp_{message.document.file_id}.pdf"
        output_pdf = f"watermarked_{message.document.file_id}.pdf"
        
        with open(input_pdf, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        name = message.caption if message.caption else message.document.file_name
        paper_id = gen_id("p")
        
        # 🚨 FIX 2: Safety Shield (Try-Except)
        try:
            add_watermark(input_pdf, output_pdf)
            file_to_send = output_pdf # Watermark lag gaya toh nayi file bhejenge
        except Exception as e:
            # Agar PDF corrupt ya locked nikli
            bot.send_message(message.chat.id, f"⚠️ <b>Warning:</b> Ye PDF corrupt ya locked hai. Watermark fail ho gaya.\nBina watermark ke upload kar raha hoon...", parse_mode='HTML')
            file_to_send = input_pdf # Fail hone par original file bhejenge
        
        # Uploading to Database Group
        with open(file_to_send, 'rb') as f:
            sent_msg = bot.send_document(DB_GROUP_ID, document=(name, f), caption=f"Added: {name}")
            new_file_id = sent_msg.document.file_id
            
        papers_col.insert_one({"_id": paper_id, "name": name, "file_id": new_file_id, "folder_id": folder_id})
        
        # Temp files delete karna
        if os.path.exists(input_pdf): os.remove(input_pdf)
        if os.path.exists(output_pdf): os.remove(output_pdf)
        
        bot.delete_message(message.chat.id, loading_msg.message_id)
        
        # UI Refresh
        img, caption, markup = get_folder_ui(message.from_user.id, "Admin", folder_id, is_admin=True)
        bot.send_photo(message.chat.id, photo=img, caption=caption, parse_mode='HTML', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Please send a valid PDF file only.")


# --- CMS (EDIT UI) HANDLERS ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("editui_"))
def edit_ui_start(call):
    folder_id = call.data.split("_", 1)[1]
    msg = bot.send_message(call.message.chat.id, "🖼️ <b>Step 1/3: Nayi Photo Bhejein</b>\n\nIs page ke liye ek nayi image send karein.\n<i>(Agar cancel karna ho toh /admin likhein)</i>", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_edit_photo, folder_id)

def process_edit_photo(message, folder_id):
    if message.text == '/admin': return admin_panel(message)
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ Sirf photo bhejein. Wapas photo bhejein:")
        return bot.register_next_step_handler(msg, process_edit_photo, folder_id)
        
    photo_id = message.photo[-1].file_id
    msg = bot.send_message(message.chat.id, "📝 <b>Step 2/3: Naya Title Bhejein</b>\n\nJaise: <code>🏆 MAJOR TESTS PHASE-1 🏆</code>\n(Aap HTML tags like &lt;b&gt; use kar sakte hain)", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_edit_title, folder_id, photo_id)

def process_edit_title(message, folder_id, photo_id):
    if message.text == '/admin': return admin_panel(message)
    title = message.text
    
    msg = bot.send_message(message.chat.id, "💬 <b>Step 3/3: Bottom Text Bhejein</b>\n\nJaise: <code>⚡ Neeche diye gaye papers jaldi solve karein:</code>", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_edit_bottom_text, folder_id, photo_id, title)



def process_edit_bottom_text(message, folder_id, photo_id, title):
    if message.text == '/admin': return admin_panel(message)
    bottom_text = message.text
    
    # --- SAFETY SHIELD: Pehle ek dummy caption banakar test karenge ---
    test_caption = (
        f"{title}\n\n"
        f"<blockquote>👤 <b>Student:</b> Admin\n"
        f"🆔 <b>User ID:</b> <code>12345</code>\n"
        f"📂 <b>Current Folder:</b> Test Folder</blockquote>\n\n"
        f"{bottom_text}"
    )
    
    try:
        # Bot pehle chupchap ek message bhej kar test karega ki HTML sahi hai ya nahi
        test_msg = bot.send_photo(message.chat.id, photo=photo_id, caption=test_caption, parse_mode='HTML')
        bot.delete_message(message.chat.id, test_msg.message_id) # Test pass hua toh turant delete kar dega
        
        # Agar test pass ho gaya (matlab HTML me koi error nahi hai), tabhi Database me save hoga!
        folders_col.update_one({"_id": folder_id}, {"$set": {
            "photo": photo_id,
            "title": title,
            "bottom_text": bottom_text
        }})
        
        bot.send_message(message.chat.id, "✅ <b>UI Successfully Updated!</b>", parse_mode='HTML')
        
        # Naya UI render karna
        img, caption, markup = get_folder_ui(message.from_user.id, "Admin", folder_id, is_admin=True)
        bot.send_photo(message.chat.id, photo=img, caption=caption, parse_mode='HTML', reply_markup=markup)
        
    except Exception as e:
        # Agar HTML me error hua (jaise </b> chhut gaya), toh bot crash hone se bach jayega aur ye error dega:
        error_msg = (
            f"❌ <b>HTML FORMATTING ERROR!</b> ❌\n\n"
            f"Aapke bheje gaye text me koi tag galat hai (Jaise <code>&lt;b&gt;</code> ko band na karna ya galat slash lagana).\n\n"
            f"<b>Error Details:</b> <code>{e}</code>\n\n"
            f"⚠️ <i>Aapka purana UI safe hai aur save nahi hua. Kripya wapas '🎨 Edit Page UI' par click karke sahi tags ke sath try karein.</i>"
        )
        bot.send_message(message.chat.id, error_msg, parse_mode='HTML')



# --- NAVIGATION & DELETE ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("delf_") or call.data.startswith("delp_"))
def admin_delete_actions(call):
    action, target_id = call.data.split("_", 1)
    if action == "delf":
        folder = folders_col.find_one({"_id": target_id})
        parent_id = folder['parent_id']
        folders_col.delete_one({"_id": target_id})
        papers_col.delete_many({"folder_id": target_id})
        bot.answer_callback_query(call.id, "🗑️ Folder deleted!", show_alert=True)
        img, caption, markup = get_folder_ui(call.from_user.id, "Admin", parent_id, is_admin=True)
        bot.edit_message_media(media=InputMediaPhoto(img, caption=caption, parse_mode='HTML'), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    elif action == "delp":
        paper = papers_col.find_one({"_id": target_id})
        folder_id = paper['folder_id']
        papers_col.delete_one({"_id": target_id})
        bot.answer_callback_query(call.id, "🗑️ Paper deleted!", show_alert=True)
        img, caption, markup = get_folder_ui(call.from_user.id, "Admin", folder_id, is_admin=True)
        bot.edit_message_media(media=InputMediaPhoto(img, caption=caption, parse_mode='HTML'), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adf_"))
def admin_navigate(call):
    folder_id = call.data.split("adf_")[1]
    img, caption, markup = get_folder_ui(call.from_user.id, "Admin", folder_id, is_admin=True)
    bot.edit_message_media(media=InputMediaPhoto(img, caption=caption, parse_mode='HTML'), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)




# ==========================================
# ℹ️ HELP PAGE & SUPPORT
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "help_page")
def show_help_page(call):
    is_admin = call.from_user.id == ADMIN_ID
    
    help_text = (
        "📚 <b>HOW TO USE THIS BOT?</b>\n\n"
        "1️⃣ <b>Select Institute:</b> Home page se apna folder chunein (e.g., Allen, PW).\n"
        "2️⃣ <b>Choose Test:</b> Jo paper solve karna hai uspe click karein.\n"
        "3️⃣ <b>Download & Save:</b> Bot aapko turant PDF bhej dega.\n\n"
        "⚠️ <i>Attention: Security ke liye saari PDFs 10 minute me auto-delete ho jati hain. Kripya unhe turant save ya forward kar lein!</i>\n\n"
        "📞 <b>Need Help or Found an Error?</b>\n"
        "Agar koi paper missing hai ya bot kaam nahi kar raha, toh seedha Admin se baat karein 👇"
    )
    
    markup = InlineKeyboardMarkup()
    # Direct aapke chat par le jane wala button
    markup.row(InlineKeyboardButton("💬 Talk to Admin", url="https://t.me/errorkidk"))
    
    # Wapas Home par aane ka button
    back_data = "adf_root" if is_admin else "vwf_root"
    markup.row(InlineKeyboardButton("🔙 Back to Home", callback_data=back_data))
    
    try:
        bot.edit_message_media(media=InputMediaPhoto(IMAGES['home'], caption=help_text, parse_mode='HTML'), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"Help Page Error: {e}")
            
    bot.answer_callback_query(call.id)



@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_user_sub(call):
    user_id = call.from_user.id
    
    if check_subscription(user_id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        # User verify ho gaya, usko home page bhej do
        img, caption, markup = get_folder_ui(user_id, call.from_user.first_name, "root", is_admin=False)
        bot.send_photo(call.message.chat.id, photo=img, caption=caption, parse_mode='HTML', reply_markup=markup)
        bot.answer_callback_query(call.id, "✅ Verification Successful! Welcome.", show_alert=True)
    else:
        # Agar jhooth bol raha hai aur join nahi kiya
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak dono channels join nahi kiye hain! Pehle join karein.", show_alert=True)




# ==========================================
# 🎓 STUDENT UI & DOWNLOAD
# ==========================================



@bot.message_handler(commands=['start'])
def student_home(message):
    user_id = message.from_user.id
    users_col.update_one({"_id": user_id}, {"$set": {"first_name": message.from_user.first_name}}, upsert=True)
    
    user = users_col.find_one({"_id": user_id})
    if user and user.get("access") == False:
        return bot.send_message(message.chat.id, "❌ Access Denied.")
        
    # 🚨 FORCE SUB CHECK 🚨
    if not check_subscription(user_id):
        return send_force_sub_msg(message.chat.id)
        
    img, caption, markup = get_folder_ui(user_id, message.from_user.first_name, "root", is_admin=False)
    bot.send_photo(message.chat.id, photo=img, caption=caption, parse_mode='HTML', reply_markup=markup)




# ==========================================
# 🎓 STUDENT UI & DOWNLOAD (WITH FORCE SUB)
# ==========================================

@bot.message_handler(commands=['start'])
def student_home(message):
    user_id = message.from_user.id
    users_col.update_one({"_id": user_id}, {"$set": {"first_name": message.from_user.first_name}}, upsert=True)
    
    user = users_col.find_one({"_id": user_id})
    if user and user.get("access") == False:
        return bot.send_message(message.chat.id, "❌ Access Denied.")
        
    # 🚨 FORCE SUB CHECK
    if not check_subscription(user_id):
        return send_force_sub_msg(message.chat.id)
        
    img, caption, markup = get_folder_ui(user_id, message.from_user.first_name, "root", is_admin=False)
    bot.send_photo(message.chat.id, photo=img, caption=caption, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vwf_"))
def student_navigate(call):
    # 🚨 FORCE SUB CHECK
    if not check_subscription(call.from_user.id):
        return bot.answer_callback_query(call.id, "❌ Please join our channels first. Type /start", show_alert=True)
        
    folder_id = call.data.split("vwf_")[1]
    img, caption, markup = get_folder_ui(call.from_user.id, call.from_user.first_name, folder_id, is_admin=False)
    
    try:
        bot.edit_message_media(media=InputMediaPhoto(img, caption=caption, parse_mode='HTML'), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    except Exception as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            print(f"Navigation Error: {e}")
            
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("getp_"))
def get_paper(call):
    # 🚨 FORCE SUB CHECK
    if not check_subscription(call.from_user.id):
        return bot.answer_callback_query(call.id, "❌ Please join our channels first. Type /start", show_alert=True)
        
    paper_id = call.data.split("getp_")[1]
    paper = papers_col.find_one({"_id": paper_id})
    
    if paper:
        # Fake Loading Animation
        loading_msg = bot.send_message(call.message.chat.id, "📥 <b>Preparing File...</b>\n<code>[⬛⬜⬜⬜⬜⬜⬜⬜⬜⬜] 10%</code>", parse_mode='HTML')
        time.sleep(0.5)
        bot.edit_message_text("📥 <b>Bypassing servers...</b>\n<code>[⬛⬛⬛⬛⬜⬜⬜⬜⬜⬜] 40%</code>", chat_id=call.message.chat.id, message_id=loading_msg.message_id, parse_mode='HTML')
        time.sleep(0.5)
        bot.edit_message_text("📥 <b>Extracting Document...</b>\n<code>[⬛⬛⬛⬛⬛⬛⬛⬜⬜⬜] 75%</code>", chat_id=call.message.chat.id, message_id=loading_msg.message_id, parse_mode='HTML')
        time.sleep(0.5)
        bot.edit_message_text("✅ <b>Document Ready!</b>\n<code>[⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛] 100%</code>", chat_id=call.message.chat.id, message_id=loading_msg.message_id, parse_mode='HTML')
        time.sleep(0.5)
        bot.delete_message(call.message.chat.id, loading_msg.message_id)
        
        premium_caption = (
            f"<blockquote>📄 <b>Your PDF is here!</b></blockquote>\n\n"
            f"👤 <b>Uploaded by:</b> <a href='https://t.me/errorkidk'>ERROR</a>\n\n"
            f"⚠️ <i>Note: This file will auto-delete in 10 mins. Please save it.</i>"
        )
        
        sent_msg = bot.send_document(call.message.chat.id, paper['file_id'], caption=premium_caption, parse_mode='HTML')
        bot.answer_callback_query(call.id, "File delivered! Timer started ⏳")
        threading.Thread(target=delete_message_later, args=(call.message.chat.id, sent_msg.message_id)).start()






# ==========================================
# 🚀 RUN BOT
# ==========================================
# ==========================================
# 🌐 DUMMY WEB SERVER (FOR RENDER) & BOT RUN
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 VIP Test Paper Bot is LIVE and Running 24/7!"

def run_web_server():
    # Render khud ek PORT environment variable deta hai
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    print("Setting up Bot Commands...")
    bot.set_my_commands([
        BotCommand("start", "Start the bot & Go to Home"),
        BotCommand("admin", "👑 Open Admin Panel"),
        BotCommand("stats", "📊 Check Bot Live Stats"),
        BotCommand("broadcast", "📢 Send msg to all users"),
        BotCommand("backup", "💾 Download Database Backup"),
        BotCommand("recover", "🔄 Restore Database from Backup"),
        BotCommand("end", "🚫 Block a user")
    ])

    # Dummy server ko alag background thread me chalana
    print("Starting Web Server for Render...")
    server_thread = threading.Thread(target=run_web_server)
    server_thread.start()

    # Main thread me apna bot chalega
    print("VIP Test Paper Bot v3.0 Started...")
    bot.infinity_polling()
