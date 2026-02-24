import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN not found in environment")

# -------------------------
# MEMORY STORAGE
# -------------------------
waiting_users = []
active_pairs = {}
users = {}
reports = {}

# -------------------------
# MENUS
# -------------------------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🚀 Find Partner", callback_data="find")],
        [InlineKeyboardButton("⚙️ Set Interests", callback_data="set_interest")]
    ]
    return InlineKeyboardMarkup(keyboard)

def chat_menu():
    keyboard = [
        [
            InlineKeyboardButton("⏭ Next", callback_data="next"),
            InlineKeyboardButton("⛔ Stop", callback_data="stop")
        ],
        [InlineKeyboardButton("🚨 Report", callback_data="report")]
    ]
    return InlineKeyboardMarkup(keyboard)

def interest_menu():
    keyboard = [
        [
            InlineKeyboardButton("🎵 Music", callback_data="interest_Music"),
            InlineKeyboardButton("💻 Coding", callback_data="interest_Coding")
        ],
        [
            InlineKeyboardButton("🎮 Gaming", callback_data="interest_Gaming"),
            InlineKeyboardButton("💖 Dating", callback_data="interest_Dating")
        ],
        [InlineKeyboardButton("❌ Clear Interest", callback_data="clear_interest")]
    ]
    return InlineKeyboardMarkup(keyboard)

# -------------------------
# START
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Anonymous Chat*\n\n"
        "Chat privately with strangers worldwide.\n\n"
        "Choose an option below:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# -------------------------
# MATCHING LOGIC
# -------------------------
async def connect(user_id, context):

    # Prevent duplicate queue entry
    if user_id in waiting_users:
        return

    # Prevent reconnect while already chatting
    if user_id in active_pairs:
        return

    user_interest = users.get(user_id)

    # Try interest-based match first
    for partner in waiting_users:
        if partner != user_id:
            if users.get(partner) == user_interest:
                waiting_users.remove(partner)

                active_pairs[user_id] = partner
                active_pairs[partner] = user_id

                await context.bot.send_message(user_id, "✅ Connected!", reply_markup=chat_menu())
                await context.bot.send_message(partner, "✅ Connected!", reply_markup=chat_menu())
                return

    # Random match fallback
    for partner in waiting_users:
        if partner != user_id:
            waiting_users.remove(partner)

            active_pairs[user_id] = partner
            active_pairs[partner] = user_id

            await context.bot.send_message(user_id, "✅ Connected!", reply_markup=chat_menu())
            await context.bot.send_message(partner, "✅ Connected!", reply_markup=chat_menu())
            return

    # If no partner found → wait
    waiting_users.append(user_id)
    await context.bot.send_message(user_id, "⏳ Waiting for partner...")

async def disconnect(user_id, context):

    # Remove from waiting queue if present
    if user_id in waiting_users:
        waiting_users.remove(user_id)

    if user_id in active_pairs:
        partner = active_pairs.get(user_id)

        # Clean both sides safely
        active_pairs.pop(user_id, None)
        active_pairs.pop(partner, None)

        try:
            await context.bot.send_message(partner, "❌ Partner left.", reply_markup=main_menu())
        except:
            pass

# -------------------------
# BUTTON HANDLER
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    data = query.data

    if data == "find":
        await connect(user_id, context)

    elif data == "next":
        await disconnect(user_id, context)
        await connect(user_id, context)

    elif data == "stop":
        await disconnect(user_id, context)
        await context.bot.send_message(user_id, "❌ Chat stopped.", reply_markup=main_menu())

    elif data == "report":
        partner = active_pairs.get(user_id)
        if partner:
            reports[partner] = reports.get(partner, 0) + 1
            await context.bot.send_message(user_id, "🚨 User reported.")
        await disconnect(user_id, context)

    elif data == "set_interest":
        await context.bot.send_message(user_id, "Select your interest:", reply_markup=interest_menu())

    elif data.startswith("interest_"):
        interest = data.split("_")[1]
        users[user_id] = interest
        await context.bot.send_message(user_id, f"✅ Interest set to: {interest}", reply_markup=main_menu())

    elif data == "clear_interest":
        users[user_id] = None
        await context.bot.send_message(user_id, "Interest cleared.", reply_markup=main_menu())

# -------------------------
# MESSAGE RELAY
# -------------------------
async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in active_pairs:
        return

    partner = active_pairs.get(user_id)

    # Extra safety: prevent self-relay
    if partner == user_id:
        return

    await update.message.copy(chat_id=partner)

# -------------------------
# APP
# -------------------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, relay))

print("🚀 Anonymous Chat Platform Running...")
app.run_polling()