import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import sqlite3
import time

# --- 1. CONFIGURATION (Yahan apni details dalein) ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 123456789          # Apna Telegram ID dalein (Rose Bot se check karein)
UPI_ID = "your-upi@okaxis"    # Apni UPI ID dalein

# SMM PANEL DETAILS
SMM_API_URL = "https://thesmmpro.com/api/v2" 
SMM_API_KEY = "ac2d63d680b858d5955f347beadf6ce4"

# SERVICE IDs (Panel se dekh kar ID yahan dalein)
SERVICE_IDS = {
    'tg_views': 101,  # Example ID
    'tg_subs': 102,   # Example ID
    'tg_likes': 103   # Example ID
}
PRICES_PER_1K = {
    'tg_views': 10.0,  # ₹10 per 1000 views
    'tg_subs': 150.0,  # ₹150 per 1000 subs
    'tg_likes': 20.0   # ₹20 per 1000 likes
}

bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. DATABASE FUNCTIONS (SQLite) ---
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Users table: ID, Balance
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL)''')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        # New user create karein
        add_user(user_id)
        return 0.0

def add_user(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0.0))
        conn.commit()
    except:
        pass
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

# --- 3. SMM API FUNCTION ---
def place_smm_order(service_id, link, quantity):
    payload = {
        'key': SMM_API_KEY,
        'action': 'add',
        'service': service_id,
        'link': link,
        'quantity': quantity
    }
    try:
        # response = requests.post(SMM_API_URL, data=payload)
        # return response.json()
        
        # --- TESTING KE LIYE FAKE RESPONSE (Jab tak real API key na ho ise use karein) ---
        return {"order": 12345} 
    except Exception as e:
        return {"error": str(e)}

# --- 4. MENUS (UI Buttons) ---
def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("IG FOLLOW ⚡️", callback_data="coming_soon")
    btn2 = InlineKeyboardButton("INSTAGRAM 🔥", callback_data="coming_soon")
    btn3 = InlineKeyboardButton("TELEGRAM 🐬", callback_data="tg_menu") # Main Feature
    btn4 = InlineKeyboardButton("YOUTUBE 📺", callback_data="coming_soon")
    btn5 = InlineKeyboardButton("💰 DEPOSIT", callback_data="deposit")
    btn6 = InlineKeyboardButton("👤 PROFILE", callback_data="profile")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

def telegram_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    btn1 = InlineKeyboardButton("TG Subscribe ❄️", callback_data="order_tg_subs")
    btn2 = InlineKeyboardButton("TG Like => ❤️", callback_data="order_tg_likes")
    btn3 = InlineKeyboardButton("TG Post Views 🫧", callback_data="order_tg_views")
    btn4 = InlineKeyboardButton("BACK 🔙", callback_data="back_main")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# --- 5. HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    init_db() # Database check/create
    add_user(message.chat.id)
    bot.send_message(message.chat.id, "🌿 **WELCOME TO SMM BOT** 🌿\nSelect Service:", reply_markup=main_menu(), parse_mode='Markdown')

# --- CALLBACKS (Button Clicks) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.message.chat.id
    
    if call.data == "back_main":
        bot.edit_message_text("🌿 **MAIN MENU** 🌿", uid, call.message.message_id, reply_markup=main_menu(), parse_mode='Markdown')

    elif call.data == "tg_menu":
        bot.edit_message_text("🐬 **TELEGRAM SERVICES**\nChoose Option:", uid, call.message.message_id, reply_markup=telegram_menu(), parse_mode='Markdown')

    elif call.data == "profile":
        bal = get_balance(uid)
        bot.answer_callback_query(call.id, f"Balance: ₹{bal}")
        bot.send_message(uid, f"👤 **USER PROFILE**\n\n🆔 ID: `{uid}`\n💰 Balance: ₹{bal}", parse_mode='Markdown')

    elif call.data == "deposit":
        text = (
            "💰 **DEPOSIT FUNDS**\n\n"
            f"UPI ID: `{UPI_ID}`\n\n"
            "1️⃣ Is ID par payment karein.\n"
            "2️⃣ Screenshot Admin ko bhejein.\n"
            "3️⃣ Admin verify karke balance add karega."
        )
        bot.send_message(uid, text, parse_mode='Markdown')

    elif call.data.startswith("order_"):
        service_type = call.data.replace("order_", "")
        rate = PRICES_PER_1K[service_type]
        
        msg = bot.send_message(uid, f"Selected: {service_type}\nPrice: ₹{rate}/1k\n\n🔗 **Link Bhejein:**")
        bot.register_next_step_handler(msg, process_link, service_type)
        
    elif call.data == "coming_soon":
        bot.answer_callback_query(call.id, "Coming Soon!")

# --- ORDER PROCESSING STEPS ---

def process_link(message, service_type):
    link = message.text
    msg = bot.reply_to(message, "🔢 **Quantity Dalein (e.g., 100, 1000):**")
    bot.register_next_step_handler(msg, process_qty, service_type, link)

def process_qty(message, service_type, link):
    try:
        qty = int(message.text)
        uid = message.chat.id
        
        # Calculate Cost
        price_per_1k = PRICES_PER_1K[service_type]
        total_cost = (price_per_1k / 1000) * qty
        
        # Check Balance
        current_bal = get_balance(uid)
        
        if current_bal >= total_cost:
            # 1. Deduct Balance (Database)
            update_balance(uid, -total_cost)
            
            # 2. Call API
            smm_service_id = SERVICE_IDS[service_type]
            api_res = place_smm_order(smm_service_id, link, qty)
            
            if "order" in api_res:
                bot.reply_to(message, f"✅ **SUCCESS!**\nOrder ID: {api_res['order']}\nCost: ₹{total_cost}\nRemaining: ₹{current_bal - total_cost}")
            else:
                # Refund agar API fail ho
                update_balance(uid, total_cost)
                bot.reply_to(message, "❌ Order Failed (API Error). Money Refunded.")
        else:
            bot.reply_to(message, f"❌ **Insufficient Balance**\nCost: ₹{total_cost}\nYour Balance: ₹{current_bal}\n\nPlease /deposit")
            
    except ValueError:
        bot.reply_to(message, "❌ Invalid Number.")

# --- ADMIN COMMANDS ---

# Balance add karne ke liye: /addfund [UserID] [Amount]
@bot.message_handler(commands=['addfund'])
def add_fund_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split()
            target_id = int(parts[1])
            amount = float(parts[2])
            
            update_balance(target_id, amount)
            bot.reply_to(message, f"✅ Added ₹{amount} to {target_id}")
            bot.send_message(target_id, f"💰 **Deposit Successful!**\nAdded: ₹{amount}")
        except:
            bot.reply_to(message, "Format: /addfund user_id amount")

# Broadcast message
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == ADMIN_ID:
        msg = message.text.replace('/broadcast', '')
        users = get_all_users()
        count = 0
        for u in users:
            try:
                bot.send_message(u, f"📢 **NOTICE:**\n{msg}")
                count += 1
            except:
                pass
        bot.reply_to(message, f"Sent to {count} users.")

# --- START BOT ---
init_db()
print("Bot Started...")
bot.polling()
