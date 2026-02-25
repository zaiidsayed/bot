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

# -------------------------
# LOAD ENV
# -------------------------
load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN not found in environment")

# -------------------------
# MEMORY STORAGE
# -------------------------
waiting_users = set()
active_pairs = {}
users = {}
reports = {}

# -------------------------
# MENUS
# -------------------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Find Partner", callback_data="find")],
        [InlineKeyboardButton("⚙️ Set Interests", callback_data="set_interest")]
    ])

def chat_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏭ Next", callback_data="next"),
            InlineKeyboardButton("⛔ Stop", callback_data="stop")
        ],
        [InlineKeyboardButton("🚨 Report", callback_data="report")]
    ])

def interest_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎵 Music", callback_data="interest_Music"),
            InlineKeyboardButton("💻 Coding", callback_data="interest_Coding")
        ],
        [
            InlineKeyboardButton("🎮 Gaming", callback_data="interest_Gaming"),
            InlineKeyboardButton("💖 Dating", callback_data="interest_Dating")
        ],
        [InlineKeyboardButton("❌ Clear Interest", callback_data="clear_interest")]
    ])

# -------------------------
# START
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await disconnect(user_id, context)

    await update.message.reply_text(
        "👋 *Anonymous Chat*\n\n"
        "Chat privately with strangers worldwide.\n\n"
        "Choose an option below:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# -------------------------
# MATCHING
# -------------------------
async def connect(user_id, context):

    # already chatting
    if user_id in active_pairs:
        return

    # already waiting
    if user_id in waiting_users:
        return

    interest = users.get(user_id)

    # Interest matching
    for partner in list(waiting_users):

        if partner == user_id:
            continue

        if users.get(partner) == interest:

            waiting_users.remove(partner)

            active_pairs[user_id] = partner
            active_pairs[partner] = user_id

            await context.bot.send_message(
                user_id,
                "✅ Connected!",
                reply_markup=chat_menu()
            )

            await context.bot.send_message(
                partner,
                "✅ Connected!",
                reply_markup=chat_menu()
            )
            return

    # Random fallback
    if waiting_users:

        partner = waiting_users.pop()

        if partner != user_id:

            active_pairs[user_id] = partner
            active_pairs[partner] = user_id

            await context.bot.send_message(
                user_id,
                "✅ Connected!",
                reply_markup=chat_menu()
            )

            await context.bot.send_message(
                partner,
                "✅ Connected!",
                reply_markup=chat_menu()
            )
            return

    # Wait
    waiting_users.add(user_id)

    await context.bot.send_message(
        user_id,
        "⏳ Waiting for partner..."
    )


# -------------------------
# DISCONNECT
# -------------------------
async def disconnect(user_id, context):

    waiting_users.discard(user_id)

    partner = active_pairs.pop(user_id, None)

    if partner:
        active_pairs.pop(partner, None)

        try:
            await context.bot.send_message(
                partner,
                "❌ Partner left.",
                reply_markup=main_menu()
            )
        except:
            pass


# -------------------------
# BUTTONS
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "find":
        await connect(user_id, context)

    elif data == "next":
        await disconnect(user_id, context)
        await connect(user_id, context)

    elif data == "stop":
        await disconnect(user_id, context)

        await context.bot.send_message(
            user_id,
            "❌ Chat stopped.",
            reply_markup=main_menu()
        )

    elif data == "report":

        partner = active_pairs.get(user_id)

        if partner:
            reports[partner] = reports.get(partner, 0) + 1

        await context.bot.send_message(
            user_id,
            "🚨 User reported."
        )

        await disconnect(user_id, context)

    elif data == "set_interest":

        await context.bot.send_message(
            user_id,
            "Select your interest:",
            reply_markup=interest_menu()
        )

    elif data.startswith("interest_"):

        interest = data.split("_")[1]
        users[user_id] = interest

        await context.bot.send_message(
            user_id,
            f"✅ Interest set to: {interest}",
            reply_markup=main_menu()
        )

    elif data == "clear_interest":

        users.pop(user_id, None)

        await context.bot.send_message(
            user_id,
            "Interest cleared.",
            reply_markup=main_menu()
        )

# -------------------------
# MESSAGE RELAY
# -------------------------
async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    partner = active_pairs.get(user_id)

    if not partner:
        return

    if partner == user_id:
        return

    try:
        await update.message.copy(chat_id=partner)
    except:
        pass


# -------------------------
# ERROR HANDLER
# -------------------------
async def error_handler(update, context):
    print("Error:", context.error)


# -------------------------
# APP
# -------------------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, relay))

app.add_error_handler(error_handler)

print("🚀 Anonymous Chat Platform Running...")

PORT = int(os.environ.get("PORT", 8080))

RAILWAY_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN")

if not RAILWAY_URL:
    print("Local mode")
    app.run_polling()
else:
    WEBHOOK_URL = f"https://{RAILWAY_URL}/{TOKEN}"

    print("Webhook:", WEBHOOK_URL)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True
    )