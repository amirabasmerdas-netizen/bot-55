from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from database import SessionLocal, User, ReactionBot
from utils import check_permission, is_bot_admin, get_or_create_user
from config import TARGET_GROUPS

AWAITING_CHANNEL_ID = 1
AWAITING_POST = 2

async def start_service_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_or_create_user(query.from_user.id)
    
    service_type = "view" if "view" in query.data else "reaction"
    allowed, msg = check_permission(user, service_type)
    
    if not allowed:
        await query.edit_message_text(msg)
        return ConversationHandler.END
        
    context.user_data['service_type'] = service_type
    
    if service_type == "view":
        text = "📊 سرویس ویو:\n۱. ربات اصلی را در کانال خود ادمین کنید.\n۲. آیدی کانال (با @) را ارسال کنید."
    else:
        text = "🔥 سرویس ری‌اکشن:\nآیدی کانال خود (با @) را ارسال کنید تا ربات‌های ری‌اکشن به شما معرفی شوند."
        
    await query.edit_message_text(text)
    return AWAITING_CHANNEL_ID

async def handle_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_id = update.message.text.strip()
    service_type = context.user_data.get('service_type')
    
    if service_type == "view":
        is_admin = await is_bot_admin(context.bot, channel_id)
        if not is_admin:
            await update.message.reply_text("❌ خطا: ربات اصلی در این کانال ادمین نیست. لطفاً ابتدا ربات را ادمین کنید.")
            return AWAITING_CHANNEL_ID
            
        context.user_data['verified_channel'] = channel_id
        await update.message.reply_text("✅ کانال تایید شد. لطفاً یک پست از کانال خود را به اینجا فوروارد کنید.")
        return AWAITING_POST
        
    elif service_type == "reaction":
        db = SessionLocal()
        bots = db.query(ReactionBot).filter(ReactionBot.is_active == True).all()
        db.close()
        
        if not bots:
            await update.message.reply_text("❌ در حال حاضر هیچ ربات ری‌اکشنی در شبکه فعال نیست. لطفاً بعداً مراجعه کنید.")
            return ConversationHandler.END
            
        bot_usernames = "\n".join([f"@{bot.username}" for bot in bots if bot.username])
        
        await update.message.reply_text(
            f"🤖 برای فعال‌سازی ری‌اکشن خودکار، لطفاً ربات‌های زیر را به عنوان ادمین در کانال {channel_id} اضافه کنید:\n\n"
            f"{bot_usernames}\n\n"
            f"✨ پس از اضافه کردن، این ربات‌ها به صورت خودکار و نامحدود به تمام پست‌های جدید کانال شما ری‌اکشن خواهند داد!"
        )
        
        db = SessionLocal()
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if user:
            user.channel_id = channel_id
            user.channel_verified = True
            user.daily_reactions += 1
            db.commit()
        db.close()
        
        return ConversationHandler.END

async def handle_view_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.forward_from_chat:
        await update.message.reply_text("❌ لطفاً یک پست را از کانال خود به اینجا فوروارد کنید.")
        return AWAITING_POST
        
    channel_id = context.user_data.get('verified_channel')
    fwd_chat = update.message.forward_from_chat
    
    if fwd_chat.username != channel_id.strip('@') and str(fwd_chat.id) != channel_id:
        await update.message.reply_text("❌ این پست متعلق به کانال معرفی شده نیست.")
        return AWAITING_POST
        
    await update.message.reply_text("⏳ پست دریافت شد. در حال ارسال ویو به گروه‌های هدف...")
    
    success_count = 0
    for group in TARGET_GROUPS:
        try:
            await context.bot.forward_message(
                chat_id=group,
                from_chat_id=fwd_chat.id,
                message_id=update.message.forward_from_message_id
            )
            success_count += 1
        except Exception as e:
            print(f"Failed to forward to {group}: {e}")
            
    await update.message.reply_text(f"✅ پست با موفقیت به {success_count} گروه ارسال شد.")
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
    if user:
        user.daily_views += 1
        db.commit()
    db.close()
    
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("بازگشت به منو", callback_data="start_menu")]]
    await update.message.reply_text("عملیات با موفقیت انجام شد.", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END
