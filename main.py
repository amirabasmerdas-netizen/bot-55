import os
import asyncio
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

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    # use_reloader=False بسیار مهم است تا با asyncio تداخل نکند
    flask_app.run(host='0.0.0.0', port=port, use_reloader=False, debug=False)
# -----------------------------------------------------

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_MAIN_BOT_TOKEN":
        print("❌ ERROR: BOT_TOKEN is not set! Please set it in Render Environment Variables.")
        return

    print("Initializing Telegram Bot...")
    app = Application.builder().token(BOT_TOKEN).build()

    # User Flow
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^(buy_pro|contact_admin|guide|start_menu)$"))
    
    # Service Conversation (توجه: فیلتر AWAITING_POST به filters.ALL تغییر کرده است)
    service_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_service_flow, pattern=r"^(service_view|service_reaction)$")],
        states={
            AWAITING_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_input)],
            AWAITING_POST: [MessageHandler(filters.ALL, handle_view_post)], # <--- تغییر مهم
        },
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(service_conv)

    # Admin Flow
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

    # راه‌اندازی استاندارد ربات تلگرام با asyncio
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # اجرای فلاسک در پس‌زمینه
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("🚀 Flask and Telegram Bot are running successfully!")

    # بیدار نگه داشتن اسکریپت
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
