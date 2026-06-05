from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import SessionLocal, User, ReactionBot
from datetime import datetime, timedelta
from config import ADMIN_ID
import httpx

AWAITING_BOT_TOKEN = 1

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی به این بخش را ندارید.")
        return
        
    keyboard = [
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("➕ ساخت ربات ری‌اکشن", callback_data="create_reaction_bot")],
        [InlineKeyboardButton("🤖 لیست ربات‌های ری‌اکشن", callback_data="list_reaction_bots")],
        [InlineKeyboardButton("بستن", callback_data="close_admin")]
    ]
    await update.message.reply_text("🛠 پنل مدیریت اصلی:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "close_admin":
        await query.edit_message_text("پنل مدیریت بسته شد.")
    elif query.data == "admin_users":
        await show_users_list(query)
    elif query.data == "create_reaction_bot":
        await query.edit_message_text("🤖 لطفاً توکن ربات جدید را ارسال کنید:\n(فرمت: 123456:ABC-DEF...)")
        return AWAITING_BOT_TOKEN
    elif query.data == "list_reaction_bots":
        await show_reaction_bots(query)
    elif query.data.startswith("manage_user_"):
        await manage_user(query, int(query.data.split("_")[2]))
    elif query.data.startswith("upgrade_"):
        await show_duration_menu(query, int(query.data.split("_")[1]))
    elif query.data.startswith("apply_"):
        await apply_duration(query)
    elif query.data.startswith("downgrade_"):
        await downgrade_user(query, int(query.data.split("_")[1]))
    elif query.data.startswith("delete_bot_"):
        await delete_reaction_bot(query, int(query.data.split("_")[2]))
    elif query.data == "admin_panel_back":
        await admin_panel(update, context)
        
    return ConversationHandler.END

async def show_users_list(query):
    db = SessionLocal()
    users = db.query(User).all()
    msg = "📊 لیست کاربران:\n\n"
    keyboard = []
    for u in users:
        status = "Pro" if u.user_type == "pro" else "Normal"
        msg += f"👤 {u.telegram_id} | {status}\n"
        keyboard.append([InlineKeyboardButton(f"مدیریت {u.telegram_id}", callback_data=f"manage_user_{u.telegram_id}")])
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="admin_panel_back")])
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    db.close()

async def manage_user(query, target_id):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == target_id).first()
    db.close()
    
    keyboard = [
        [InlineKeyboardButton("⬆️ ارتقا به Pro", callback_data=f"upgrade_{target_id}")],
        [InlineKeyboardButton("⬇️ تنزل به Normal", callback_data=f"downgrade_{target_id}")],
        [InlineKeyboardButton("بازگشت", callback_data="admin_users")]
    ]
    msg = f"مدیریت کاربر: {target_id}\nنوع فعلی: {user.user_type}\nانقضا: {user.pro_expiry}"
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_duration_menu(query, target_id):
    keyboard = [
        [InlineKeyboardButton("۱ هفته", callback_data=f"apply_7_{target_id}")],
        [InlineKeyboardButton("۱ ماه", callback_data=f"apply_30_{target_id}")],
        [InlineKeyboardButton("۳ ماه", callback_data=f"apply_90_{target_id}")],
        [InlineKeyboardButton("۱ سال", callback_data=f"apply_365_{target_id}")],
        [InlineKeyboardButton("بازگشت", callback_data=f"manage_user_{target_id}")]
    ]
    await query.edit_message_text("مدت زمان اشتراک پرو را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def apply_duration(query):
    parts = query.data.split("_")
    days = int(parts[1])
    target_id = int(parts[2])
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == target_id).first()
    user.user_type = "pro"
    user.pro_expiry = datetime.utcnow() + timedelta(days=days)
    db.commit()
    db.close()
    
    await query.edit_message_text(f"✅ کاربر {target_id} با موفقیت به مدت {days} روز به Pro ارتقا یافت.")

async def downgrade_user(query, target_id):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == target_id).first()
    user.user_type = "normal"
    user.pro_expiry = None
    db.commit()
    db.close()
    
    await query.edit_message_text(f"✅ کاربر {target_id} به حالت عادی بازگردانده شد.")

async def create_reaction_bot_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=10.0)
            data = res.json()
        except Exception:
            await update.message.reply_text("❌ خطا در اتصال به سرور تلگرام.")
            return AWAITING_BOT_TOKEN

    if data.get("ok"):
        username = data["result"]["username"]
        db = SessionLocal()
        existing = db.query(ReactionBot).filter(ReactionBot.token == token).first()
        if not existing:
            new_bot = ReactionBot(token=token, username=username)
            db.add(new_bot)
            db.commit()
            await update.message.reply_text(
                f"✅ ربات @{username} با موفقیت به شبکه اضافه شد!\n\n"
                f"⚠️ توجه: برای اعمال تغییرات، باید اسکریپت reaction_worker.py را ری‌استارت کنید."
            )
        else:
            await update.message.reply_text("⚠️ این ربات قبلاً ثبت شده است.")
        db.close()
    else:
        await update.message.reply_text("❌ توکن نامعتبر است.")
        return AWAITING_BOT_TOKEN
        
    return ConversationHandler.END

async def show_reaction_bots(query):
    db = SessionLocal()
    bots = db.query(ReactionBot).all()
    msg = "🤖 لیست ربات‌های ری‌اکشن:\n\n"
    keyboard = []
    for b in bots:
        msg += f"🆔 @{b.username}\n"
        keyboard.append([InlineKeyboardButton(f"حذف @{b.username}", callback_data=f"delete_bot_{b.id}")])
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="admin_panel_back")])
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    db.close()

async def delete_reaction_bot(query, bot_id):
    db = SessionLocal()
    bot = db.query(ReactionBot).get(bot_id)
    if bot:
        username = bot.username
        db.delete(bot)
        db.commit()
        await query.edit_message_text(f"✅ ربات @{username} حذف شد.\nاسکریپت ورکر را ری‌استارت کنید.")
    db.close()
