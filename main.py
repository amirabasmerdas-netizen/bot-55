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

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # User Flow (منوی اصلی کاربران)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(buy_pro|contact_admin|guide|start_menu)$"))
    
    # Service Conversation (مراحل دریافت ویو و ری‌اکشن)
    service_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_service_flow, pattern="^(service_view|service_reaction)$")],
        states={
            AWAITING_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_input)],
            AWAITING_POST: [MessageHandler(filters.UpdateType.CHANNEL_POST, handle_view_post)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(service_conv)

    # Admin Flow (پنل مدیریت)
    app.add_handler(CommandHandler("admin", admin_panel))
    
    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_button_handler, pattern="^(admin_users|create_reaction_bot|list_reaction_bots|close_admin|manage_user_|upgrade_|dur_|apply_|downgrade_|delete_bot_|admin_panel_back)")],
        states={
            AWAITING_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_reaction_bot_save)],
        },
        fallbacks=[CommandHandler("admin", admin_panel)],
    )
    app.add_handler(admin_conv)
    
    # هندلرهای اضافی برای دکمه‌های ادمین که نیازی به Conversation State ندارند
    app.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^(admin_users|create_reaction_bot|list_reaction_bots|close_admin|manage_user_\d+|upgrade_\d+|dur_\d+_\d+|apply_\d+_\d+|downgrade_\d+|delete_bot_\d+|admin_panel_back)$"))

    print("Core Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
