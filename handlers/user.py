from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from utils import get_or_create_user
from datetime import datetime

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_or_create_user(update.effective_user.id)
    
    keyboard = [
        [InlineKeyboardButton("خرید / تمدید پرو", callback_data="buy_pro")],
        [InlineKeyboardButton("ارتباط با ادمین", callback_data="contact_admin")],
        [InlineKeyboardButton("راهنما", callback_data="guide")],
        [InlineKeyboardButton("ویو", callback_data="service_view")],
        [InlineKeyboardButton("ری‌اکشن", callback_data="service_reaction")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_msg = f"سلام {update.effective_user.first_name}! به ربات مدیریت کانال خوش آمدید.\n\n"
    if user.user_type == "pro":
        welcome_msg += f"🌟 شما کاربر ویژه (Pro) هستید.\nتاریخ انقضا: {user.pro_expiry.strftime('%Y-%m-%d')}"
    else:
        days_left = 7 - (datetime.utcnow() - user.created_at).days
        if days_left <= 0:
            welcome_msg += "⚠️ دوره آزمایشی شما به پایان رسیده است."
        else:
            welcome_msg += f"🎁 شما کاربر عادی هستید.\n{days_left} روز از دوره آزمایشی شما باقی مانده است."

    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_or_create_user(query.from_user.id)

    if query.data == "buy_pro":
        from config import ADMIN_ID
        await query.edit_message_text(
            f"🛒 برای خرید یا تمدید اشتراک پرو، لطفاً با ادمین تماس بگیرید:\n\n"
            f"آیدی ادمین: @{ADMIN_ID}\n"
            f"پیام: Contact admin to purchase Pro"
        )
    elif query.data == "contact_admin":
        from config import ADMIN_ID
        await query.edit_message_text(f"📞 برای پشتیبانی با ادمین در ارتباط باشید:\n@{ADMIN_ID}")
    elif query.data == "guide":
        await query.edit_message_text(
            "📖 راهنمای استفاده:\n\n"
            "۱. برای استفاده از خدمات، ابتدا کانال خود را معرفی کنید.\n"
            "۲. ربات‌ها را به عنوان ادمین در کانال خود اضافه کنید.\n"
            "۳. از منوی ویو یا ری‌اکشن استفاده کنید.\n\n"
            "✨ در سرویس ری‌اکشن، ربات‌ها به صورت خودکار به تمام پست‌های جدید ری‌اکشن می‌دهند!"
        )
