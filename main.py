import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import sqlite3
import time
from flask import Flask
from threading import Thread

# --- 1. CONFIGURATION (Yahan apni details dalein) ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"       # 🔴 Apna Bot Token Yahan Dalein
ADMIN_ID = 123456789                    # 🔴 Apna Telegram ID Yahan Dalein (Warna Admin Panel nahi khulega)
UPI_ID = "your-upi@okaxis"              # 🔴 Apni UPI ID Yahan Dalein
ADMIN_USERNAME = "@ABVerseBots"         # Support ke liye username

# SMM PANEL DETAILS (Aapka API Key Laga Diya Hai)
SMM_API_URL = "https://thesmmpro.com/api/v2"
SMM_API_KEY = "Ac2d63d680b858d5955f347beadf6ce4" 

# ⚠️ SERVICE IDs (Aapki Select ki gayi IDs)
SERVICE_IDS = {
    'tg_views': 2221,   # Last 5 Posts Views (Sasta: ₹2.17)
    'tg_subs': 2460,    # Non-Drop Subscribers (Quality: ₹115)
    'tg_likes': 2066    # Like Reaction (₹4.8)
}

# ⚠️ SELLING PRICES (Aapka Rate)
PRICES_PER_1K = {
    'tg_views': 10.0,   # Aap ₹10 mein bech rahe hain
    'tg_subs': 160.0,   # Aap ₹160 mein bech rahe hain
    'tg_likes': 10.0    # Aap ₹10 mein bech rahe hain
}

bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. RENDER SERVER (Bot ko 24/7 chalane ke liye) ---
app = Flask('')

@app.route('/')
def home():
    return "ABVerse Bot is Running! 🚀"

def run_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# --- 3. DATABASE FUNCTIONS (SQLite) ---
def init_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL)''')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('database.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0.0

def add_user(user_id):
    conn = sqlite3.connect('database.db', check_same_thread=False)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0.0))
        conn.commit()
    except: pass
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect('database.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

# --- 4. SMM API FUNCTION ---
def place_smm_order(service_id, link, quantity):
    payload = {
        'key': SMM_API_KEY, 
        'action': 'add', 
        'service': service_id, 
        'link': link, 
        'quantity': quantity
    }
    try:
        response = requests.post(SMM_API_URL, data=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- 5. MENUS (BUTTONS) ---
def main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Buttons
    btn_tg = InlineKeyboardButton("🐬 TELEGRAM SERVICES", callback_data="tg_menu")
    markup.add(btn_tg)
    
    btn_dep = InlineKeyboardButton("💰 ADD FUNDS", callback_data="deposit")
    btn_prof = InlineKeyboardButton("👤 MY ACCOUNT", callback_data="profile")
    markup.add(btn_dep, btn_prof)
    
    btn_sup = InlineKeyboardButton("📞 SUPPORT", callback_data="support")
    # ✅ Aapka Channel Link
    btn_upd = InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/ABVerseBots") 
    markup.add(btn_sup, btn_upd)
    
    # Admin Panel (Sirf Admin ko dikhega)
    if user_id == ADMIN_ID:
        btn_admin = InlineKeyboardButton("🔒 ADMIN PANEL", callback_data="admin_panel")
        markup.add(btn_admin)
        
    return markup

def telegram_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("TG Subscribe ❄️", callback_data="order_tg_subs"),
        InlineKeyboardButton("TG Like => ❤️", callback_data="order_tg_likes"),
        InlineKeyboardButton("TG Post Views 🫧", callback_data="order_tg_views"),
        InlineKeyboardButton("BACK 🔙", callback_data="back_main")
    )
    return markup

def admin_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_cast"),
        InlineKeyboardButton("💰 Add Funds", callback_data="admin_fund"),
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        InlineKeyboardButton("❌ Close", callback_data="back_main")
    )
    return markup

# --- 6. HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    init_db()
    add_user(message.chat.id)
    
    # ✅ Aapki Photo
    photo_url = "https://graph.org/file/a9e830577def913c831f5-197bb7e861be034518.jpg"
    
    caption_text = (
        f"👋 **Hello {message.from_user.first_name}!**\n\n"
        "🚀 **Welcome to ABVerse SMM Bot**\n"
        "Best & Cheapest Telegram Promotion Service.\n\n"
        "💎 **Why Choose Us?**\n"
        "✅ Cheapest Rates (Views @ ₹10)\n"
        "✅ Non-Drop Subscribers\n"
        "✅ Instant Delivery\n\n"
        "👇 **Select a Service Below:**"
    )
    
    try:
        bot.send_photo(
            message.chat.id, 
            photo=photo_url, 
            caption=caption_text, 
            reply_markup=main_menu(message.chat.id), 
            parse_mode='Markdown'
        )
    except:
        bot.send_message(
            message.chat.id, 
            caption_text, 
            reply_markup=main_menu(message.chat.id), 
            parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    
    # --- USER ACTIONS ---
    if call.data == "back_main":
        bot.delete_message(uid, call.message.message_id) # Purana message delete karke fresh start
        start(call.message)

    elif call.data == "tg_menu":
        bot.edit_message_text("🐬 **TELEGRAM SERVICES**\nSelect Option:", uid, call.message.message_id, reply_markup=telegram_menu(), parse_mode='Markdown')

    elif call.data == "deposit":
        bot.send_message(uid, f"💰 **ADD FUNDS**\n\nUPI ID: `{UPI_ID}`\n\n1. Payment karein.\n2. Screenshot Support ko bhejein.", parse_mode='Markdown')

    elif call.data == "profile":
        bal = get_balance(uid)
        bot.send_message(uid, f"👤 **MY PROFILE**\n\n🆔 User ID: `{uid}`\n💰 Balance: ₹{bal}", parse_mode='Markdown')
        
    elif call.data == "support":
        bot.send_message(uid, f"📞 **Support:** {ADMIN_USERNAME}")

    # --- ORDER SYSTEM ---
    elif call.data.startswith("order_"):
        sType = call.data.replace("order_", "")
        rate = PRICES_PER_1K[sType]
        msg = bot.send_message(uid, f"Selected: {sType}\nPrice: ₹{rate}/1k\n\n🔗 **Apna Link Bhejein:**")
        bot.register_next_step_handler(msg, process_link, sType)

    # --- ADMIN PANEL ---
    elif call.data == "admin_panel":
        if uid == ADMIN_ID:
            bot.edit_message_text("🔒 **ADMIN CONTROL PANEL**", uid, call.message.message_id, reply_markup=admin_menu(), parse_mode='Markdown')

    elif call.data == "admin_stats":
        users = get_all_users()
        bot.answer_callback_query(call.id, f"Total Users: {len(users)}")

    elif call.data == "admin_cast":
        msg = bot.send_message(uid, "📢 **Broadcast Message Likhein:**")
        bot.register_next_step_handler(msg, process_broadcast)

    elif call.data == "admin_fund":
        msg = bot.send_message(uid, "👤 **User ID Bhejein jisko paise dene hain:**")
        bot.register_next_step_handler(msg, process_fund_step1)

# --- PROCESS FUNCTIONS ---
def process_link(message, sType):
    link = message.text
    msg = bot.reply_to(message, "🔢 **Quantity Dalein (e.g. 100, 1000):**")
    bot.register_next_step_handler(msg, process_qty, sType, link)

def process_qty(message, sType, link):
    try:
        qty = int(message.text)
        uid = message.chat.id
        cost = (PRICES_PER_1K[sType]/1000) * qty
        
        # Balance Check
        if get_balance(uid) >= cost:
            update_balance(uid, -cost)
            # API Call
            res = place_smm_order(SERVICE_IDS[sType], link, qty)
            
            if "order" in res:
                bot.reply_to(message, f"✅ **Order Successful!**\nOrder ID: {res['order']}\n💰 Cost: ₹{cost}\nRem Balance: ₹{get_balance(uid)}")
            else:
                # API Fail hua to Refund
                update_balance(uid, cost)
                err = res.get('error', 'Unknown')
                bot.reply_to(message, f"❌ **Order Failed!**\nReason: {err}\n\nMoney Refunded.")
        else:
            bot.reply_to(message, "❌ **Insufficient Balance**\nPlease add funds.")
    except ValueError:
        bot.reply_to(message, "❌ Invalid Number.")

# --- ADMIN FUNCTIONS ---
def process_broadcast(message):
    users = get_all_users()
    count = 0
    for u in users:
        try:
            bot.send_message(u, f"📢 **ANNOUNCEMENT:**\n\n{message.text}")
            count += 1
        except: pass
    bot.reply_to(message, f"✅ Sent to {count} users.")

def process_fund_step1(message):
    try:
        target_id = int(message.text)
        msg = bot.reply_to(message, "💰 **Amount Dalein:**")
        bot.register_next_step_handler(msg, process_fund_step2, target_id)
    except: bot.reply_to(message, "❌ Invalid ID")

def process_fund_step2(message, target_id):
    try:
        amount = float(message.text)
        update_balance(target_id, amount)
        bot.reply_to(message, f"✅ Added ₹{amount} to {target_id}")
        bot.send_message(target_id, f"💰 **Balance Added!**\nAmount: ₹{amount}\nCheck /profile")
    except: bot.reply_to(message, "❌ Invalid Amount")

# --- START BOT ---
init_db()
keep_alive()
print("Bot Started... 🚀")
bot.polling()
