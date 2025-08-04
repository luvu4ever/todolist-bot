from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN
from handlers import (
    start,
    handle_message,
    help_command,
    idea_command,
    list_command,
    add_event,
    add_todo,
    todone_command
)

def main():
    """Main function to run the todolist bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("idea", idea_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("todone", todone_command))
    
    # Message handler for natural language processing (should be last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    print("🤖 Smart Todolist & Calendar Bot is starting...")
    print("📅 Supports Vietnamese time formats: 'thứ 6', 'ngày 19/10', etc.")
    print("📝 Features: Events, Ideas, Todos with AI parsing")
    print("🧠 Powered by Gemini AI for intelligent time parsing")
    application.run_polling()

if __name__ == "__main__":
    main()