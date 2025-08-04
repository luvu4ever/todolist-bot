from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import ALLOWED_USERS
from gemini_service import parse_vietnamese_time, classify_message_type
from data_storage import data_manager
import re

def check_user_access(func):
    """Decorator to check if user is allowed"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if ALLOWED_USERS and ALLOWED_USERS[0] and user_id not in ALLOWED_USERS:
            await update.message.reply_text("❌ Bạn không có quyền sử dụng bot này.")
            return
        return await func(update, context)
    return wrapper

@check_user_access
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_message = """
🤖 **Smart Todolist & Calendar Bot**

Chào mừng! Tôi có thể giúp bạn:

📅 **Events/Lịch hẹn:**
- "event thứ 6 thợ lắp đồ"
- "meeting ngày 19/10 lúc 14h"

✅ **Todos:**
- "todo dọn nhà 5h"
- "mua sắm ngày mai"

💡 **Ideas/Ý tưởng:**
- "ghi nhớ mua sữa"
- "ý tưởng cho dự án mới"

🎯 **Commands:**
- `/idea` - Xem tất cả events và ideas
- `/list` - Xem todolist
- `/todone [mô tả]` - Hoàn thành task
- `/help` - Trợ giúp

🧠 Tôi hiểu thời gian tiếng Việt: thứ 6, ngày 19/10, 5h, mai, v.v.
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

@check_user_access
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced help command"""
    help_text = """
🤖 **Smart Todolist & Calendar Bot - Hướng dẫn**

🧠 **AI Tự động phân loại:**
Bot sẽ tự động hiểu bạn muốn thêm gì!

📅 **EVENTS (Lịch hẹn):**
• `event thứ 6 thợ lắp đồ`
• `meeting ngày 19/10 lúc 14h30`
• `cuộc họp mai 9h sáng`

✅ **TODOS (Công việc):**
• `todo dọn nhà 5h`
• `làm bài tập ngày mai`
• `mua sắm thứ 7`

💡 **IDEAS (Ý tưởng):**
• `ghi nhớ mua sữa`
• `ý tưởng app mới`
• `nhớ gọi mẹ`

⏰ **Định dạng thời gian hỗ trợ:**
• **Thứ**: thứ 2, thứ 3, ..., thứ 7, chủ nhật
• **Ngày**: ngày 19/10, 25/12/2024
• **Giờ**: 5h, 14h30, 9h sáng, 17h chiều
• **Tương đối**: hôm nay, mai, ngày mai

🎯 **Commands có sẵn:**
• `/help` - Xem hướng dẫn này
• `/idea` - Xem tất cả events & ideas
• `/list` - Xem todolist hiện tại
• `/todone [mô tả]` - Hoàn thành task

📝 **Ví dụ sử dụng:**
1. Gửi: `event thứ 6 thợ lắp đồ`
   → Bot tạo event vào thứ 6 tới

2. Gửi: `todo dọn nhà 5h`
   → Bot tạo todo hôm nay lúc 5h

3. Gửi: `/todone dọn nhà`
   → Bot đánh dấu task hoàn thành

🤖 **Đặc biệt:**
• Không cần gõ lệnh phức tạp
• Chỉ cần gõ tự nhiên bằng tiếng Việt
• AI sẽ hiểu và phân loại tự động

**Bắt đầu bằng cách gửi tin nhắn như: "event mai gặp bạn"**
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

@check_user_access
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle natural language messages"""
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Parse time information
    time_info = parse_vietnamese_time(text)
    
    # Classify message type
    message_type = classify_message_type(text)
    
    # Clean text for storage
    clean_text = time_info.get("parsed_text", text)
    
    if message_type == "event":
        item = data_manager.add_event(user_id, clean_text, time_info)
        emoji = "📅"
        type_name = "Event"
    elif message_type == "todo":
        item = data_manager.add_todo(user_id, clean_text, time_info)
        emoji = "✅"
        type_name = "Todo"
    else:  # idea
        item = data_manager.add_idea(user_id, clean_text, time_info)
        emoji = "💡"
        type_name = "Idea"
    
    # Format response
    time_display = time_info.get("display_time", "không xác định thời gian")
    
    response = f"{emoji} **{type_name} đã thêm!**\n\n"
    response += f"📝 {clean_text}\n"
    if time_info.get("has_time"):
        response += f"⏰ {time_display}\n"
    response += f"🆔 ID: {item['id']}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

@check_user_access
async def idea_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all events and ideas sorted by time"""
    user_id = update.effective_user.id
    all_items = data_manager.get_all_user_items(user_id)
    
    response = "📋 **Events & Ideas** (sắp xếp theo thời gian)\n\n"
    
    # Sort function for items
    def get_sort_key(item):
        time_info = item.get("time_info", {})
        if time_info.get("has_time") and time_info.get("datetime"):
            try:
                return datetime.fromisoformat(time_info["datetime"])
            except:
                pass
        # Items without time go to the end
        return datetime.max
    
    # Events
    if all_items["events"]:
        sorted_events = sorted(all_items["events"], key=get_sort_key)
        
        # Separate timed and non-timed events
        timed_events = [e for e in sorted_events if e["time_info"].get("has_time")]
        no_time_events = [e for e in sorted_events if not e["time_info"].get("has_time")]
        
        response += "📅 **Events:**\n"
        
        # Timed events first
        if timed_events:
            response += "⏰ *Có thời gian:*\n"
            for event in timed_events[-10:]:  # Last 10
                time_display = event["time_info"].get("display_time", "")
                response += f"• {event['text']}"
                if time_display:
                    response += f" - {time_display}"
                response += f" (ID: {event['id']})\n"
        
        # Non-timed events
        if no_time_events:
            if timed_events:
                response += "\n📝 *Chưa có thời gian:*\n"
            for event in no_time_events[-5:]:  # Last 5
                response += f"• {event['text']} (ID: {event['id']})\n"
        
        response += "\n"
    
    # Ideas
    if all_items["ideas"]:
        sorted_ideas = sorted(all_items["ideas"], key=get_sort_key)
        
        response += "💡 **Ideas:**\n"
        for idea in sorted_ideas[-10:]:  # Last 10
            time_display = idea["time_info"].get("display_time", "")
            response += f"• {idea['text']}"
            if idea["time_info"].get("has_time") and time_display:
                response += f" - {time_display}"
            response += f" (ID: {idea['id']})\n"
        response += "\n"
    
    if not all_items["events"] and not all_items["ideas"]:
        response += "Chưa có events hoặc ideas nào.\n"
        response += "Hãy thêm bằng cách gửi tin nhắn như: 'event thứ 6 thợ lắp đồ'\n\n"
    
    # Add removal instructions
    response += "🗑️ **Xóa items:**\n"
    response += "• `/eventdone [mô tả]` - xóa event\n" 
    response += "• `/ideadone [mô tả]` - xóa idea"
    
    await update.message.reply_text(response, parse_mode='Markdown')

@check_user_access
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View todolist sorted by time"""
    user_id = update.effective_user.id
    todos = data_manager.get_user_todos(user_id)
    
    if not todos:
        response = "📋 **Todolist trống**\n\n"
        response += "Thêm todo bằng cách gửi: 'todo dọn nhà 5h'"
        await update.message.reply_text(response, parse_mode='Markdown')
        return
    
    # Sort todos by datetime
    def get_sort_key(todo):
        time_info = todo.get("time_info", {})
        if time_info.get("has_time") and time_info.get("datetime"):
            try:
                return datetime.fromisoformat(time_info["datetime"])
            except:
                pass
        # Items without time go to the end
        return datetime.max
    
    sorted_todos = sorted(todos, key=get_sort_key)
    
    response = "📋 **Todolist** (sắp xếp theo thời gian)\n\n"
    
    # Group by time status
    timed_todos = []
    no_time_todos = []
    
    for todo in sorted_todos:
        if todo["time_info"].get("has_time"):
            timed_todos.append(todo)
        else:
            no_time_todos.append(todo)
    
    # Show timed todos first
    if timed_todos:
        response += "⏰ **Có thời gian:**\n"
        for todo in timed_todos:
            status = "☑️" if todo["completed"] else "⬜"
            time_display = todo["time_info"].get("display_time", "")
            
            response += f"{status} {todo['text']}"
            if time_display:
                response += f" - {time_display}"
            response += f" (ID: {todo['id']})\n"
        response += "\n"
    
    # Show non-timed todos
    if no_time_todos:
        response += "📝 **Chưa có thời gian:**\n"
        for todo in no_time_todos:
            status = "☑️" if todo["completed"] else "⬜"
            response += f"{status} {todo['text']} (ID: {todo['id']})\n"
        response += "\n"
    
    response += f"📊 Tổng: {len(todos)} tasks"
    response += "\n💡 Dùng `/todone [mô tả]` để hoàn thành task"
    
    await update.message.reply_text(response, parse_mode='Markdown')

@check_user_access
async def todone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark todo as completed"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Cần mô tả task cần hoàn thành.\n"
            "Ví dụ: `/todone dọn nhà`",
            parse_mode='Markdown'
        )
        return
    
    description = " ".join(context.args)
    
    # Try to complete by description
    success = data_manager.complete_todo(user_id, description=description)
    
    if success:
        await update.message.reply_text(
            f"✅ **Task hoàn thành!**\n\n"
            f"📝 {description}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Không tìm thấy task: '{description}'\n\n"
            f"Dùng `/list` để xem danh sách todos",
            parse_mode='Markdown'
        )

@check_user_access
async def eventdone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove event by description"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Cần mô tả event cần xóa.\n"
            "Ví dụ: `/eventdone thợ lắp đồ`",
            parse_mode='Markdown'
        )
        return
    
    description = " ".join(context.args)
    
    # Try to remove by description
    success = data_manager.remove_event(user_id, description=description)
    
    if success:
        await update.message.reply_text(
            f"🗑️ **Event đã xóa!**\n\n"
            f"📅 {description}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Không tìm thấy event: '{description}'\n\n"
            f"Dùng `/idea` để xem danh sách events",
            parse_mode='Markdown'
        )

@check_user_access
async def ideadone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove idea by description"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Cần mô tả idea cần xóa.\n"
            "Ví dụ: `/ideadone mua sữa`",
            parse_mode='Markdown'
        )
        return
    
    description = " ".join(context.args)
    
    # Try to remove by description
    success = data_manager.remove_idea(user_id, description=description)
    
    if success:
        await update.message.reply_text(
            f"🗑️ **Idea đã xóa!**\n\n"
            f"💡 {description}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Không tìm thấy idea: '{description}'\n\n"
            f"Dùng `/idea` để xem danh sách ideas",
            parse_mode='Markdown'
        )

# Additional helper functions
async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explicit event adding (if needed)"""
    pass

async def add_todo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explicit todo adding (if needed)"""
    pass