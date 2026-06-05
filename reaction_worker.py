import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from database import SessionLocal, ReactionBot

async def auto_react(update: Update, context):
    if update.effective_chat.type != 'channel':
        return
        
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    token = context.bot.token

    url = f"https://api.telegram.org/bot{token}/setMessageReaction"
    
    emojis = ["🔥", "👍", "❤️", "👏", "😁", "🎉", "🤩", "💯", "⚡️", "🥰"]
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": [{"type": "emoji", "emoji": e} for e in emojis],
        "is_big": True
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=data, timeout=10.0)
            if res.status_code == 200:
                print(f"✅ Reacted to post {message_id} in {chat_id} using @{context.bot.username}")
    except Exception as e:
        print(f"❌ Error reacting: {e}")

async def run_bot_worker(token):
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_react))
    await app.run_polling()

async def main():
    db = SessionLocal()
    bots = db.query(ReactionBot).filter(ReactionBot.is_active == True).all()
    db.close()
    
    if not bots:
        print("No active reaction bots found in database.")
        return
        
    print(f"🚀 Starting {len(bots)} reaction bots...")
    tasks = [run_bot_worker(bot.token) for bot in bots]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("Reaction Worker System Starting...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down reaction workers...")
