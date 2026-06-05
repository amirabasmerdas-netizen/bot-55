import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from handlers.user import start, button_handler
from handlers.admin import (
    admin_panel, admin_button_handler, create_reaction_bot_save, AWAITING_BOT_TOKEN
)
from handlers.services import (
    start_service_flow, handle_channel_input, handle_view_post, AWAITING_CHANNEL_ID, AWAITING_POST
)
from config import BOT_TOKEN, ADMIN_ID

# --- بخش فلاسک (سرور وب برای بیدار نگه داشتن رندر) ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "ربات با موفقیت در حال اجراست!", 200

@flask_app.route('/ping')
def ping():
    return "Pong!", 200
# -----------------------------------------------------

def run_telegram_bot():
    """این تابع ربات تلگرام را در یک Thread جداگانه (پس‌زمینه) اجرا می‌کند."""
    print("Starting Telegram Bot...")
    
    # بررسی وجود توکن
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_MAIN_BOT_TOKEN":
        print("❌ ERROR: BOT_TOKEN is not set! Please set it in Render Environment Variables.")
        return

    try:
        app = Application.builder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^(buy_pro|contact_admin|guide|start_menu)$"))
        
        service_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(start_service_flow, pattern=r"^(service_view|service_reaction)$")],
            states={
                AWAITING_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_input)],
                AWAITING_POST: [MessageHandler(filters.UpdateType.CHANNEL_POST, handle_view_post)],
            },
            fallbacks=[CommandHandler("start", start)],
        )
        app.add_handler(service_conv)

        app.add_handler(CommandHandler("admin", admin_panel))
        
        admin_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(admin_button_handler, pattern=r"^(admin_users|create_reaction_bot|list_reaction_bots|close_admin|manage_user_|upgrade_|apply_|downgrade_|delete_bot_|admin_panel_back)")],
            states={
                AWAITING_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_reaction_bot_save)],
            },
            fallbacks=[CommandHandler("admin", admin_panel)],
        )
        app.add_handler(admin_conv)
        
        app.add_handler(CallbackQueryHandler(admin_button_handler, pattern=r"^(admin_users|create_reaction_bot|list_reaction_bots|close_admin|manage_user_\d+|upgrade_\d+|apply_\d+_\d+|downgrade_\d+|delete_bot_\d+|admin_panel_back)$"))

        print("✅ Core Bot is running...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"❌ FATAL ERROR in Telegram Bot: {e}")

def main():
    # ۱. اجرای ربات تلگرام در پس‌زمینه
    bot_thread = Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # ۲. اجرای سرور فلاسک در Thread اصلی (بسیار مهم برای رندر)
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting Flask server on port {port} for Render Health Check...")
    
    # use_reloader=False باید حتماً False باشد تا با Thread تداخل پیدا نکند
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False, debug=False)

if __name__ == "__main__":
    main()
