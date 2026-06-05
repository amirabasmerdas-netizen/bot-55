# ... (سایر ایمپورت‌ها و کدها بدون تغییر)

async def start_service_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (بدون تغییر)

async def handle_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (بدون تغییر)

async def handle_view_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # بررسی اینکه آیا پیام فوروارد شده از کانال است یا خیر
    if not update.message or not update.message.forward_from_chat:
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
