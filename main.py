import logging
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_BOT_TOKEN, PORT
from handlers import (
    start,
    help_command,
    todo_command,
    event_command,
    idea_command,
    todolist_command,
    eventlist_command,
    idealist_command,
    done_command,
    delete_event_command,
    delete_idea_command
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the todolist bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Main feature commands
    application.add_handler(CommandHandler("todo", todo_command))
    application.add_handler(CommandHandler("event", event_command))
    application.add_handler(CommandHandler("idea", idea_command))
    
    # List commands
    application.add_handler(CommandHandler("todolist", todolist_command))
    application.add_handler(CommandHandler("eventlist", eventlist_command))
    application.add_handler(CommandHandler("idealist", idealist_command))
    
    # Action commands
    application.add_handler(CommandHandler("done", done_command))
    
    # Optional deletion commands
    application.add_handler(CommandHandler("delete_event", delete_event_command))
    application.add_handler(CommandHandler("delete_idea", delete_idea_command))
    
    # Start the bot
    print("🤖 Smart Todolist & Calendar Bot is starting...")
    print("✅ Todos with priority support (urgent/normal/chill)")
    print("📅 Events with Vietnamese time parsing")
    print("💡 Ideas for future reference")
    print("🔍 Fuzzy search for task completion")
    print("🗄️ Powered by Supabase database")
    print("🧠 AI time parsing with Gemini Flash")
    print(f"🚀 Running on port {PORT}")
    
    # Run the bot (sync mode to avoid event loop conflicts)
    try:
        # Use polling for both development and production
        application.run_polling(allowed_updates=["message"])
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise

if __name__ == "__main__":
    main()