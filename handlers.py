from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import ALLOWED_USERS
from gemini_service import parse_vietnamese_time, parse_priority, clean_priority_from_text
from supabase_service import db_manager

def check_user_access(func):
    """Decorator to check if user is allowed"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if ALLOWED_USERS and user_id not in ALLOWED_USERS:
            await update.message.reply_text("❌ Bạn không có quyền sử dụng bot này.")
            return
        return await func(update, context)
    return wrapper

@check_user_access
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_message = """
🤖 **Smart Todolist & Calendar Bot** 

Chào mừng! Tôi có thể giúp bạn quản lý:

✅ **TODOS (Công việc):**
- `/todo [công việc] [thời gian] [mức độ]`
- `/todolist` - Xem danh sách todos
- `/done [mô tả]` - Hoàn thành task (fuzzy search)

📅 **EVENTS (Sự kiện):**
- `/event [hoạt động] [thời gian]`
- `/eventlist` - Xem danh sách events

💡 **IDEAS (Ý tưởng):**
- `/idea [ý tưởng]`
- `/idealist` - Xem danh sách ideas

⏰ **Thời gian hỗ trợ:**
- sáng (9h), chiều (17h), tối (20h), đêm (22h)
- hôm nay, mai, thứ 6, thứ 6 tuần sau
- 19/10, ngày 25/12
- Thứ tự linh hoạt: "tối thứ 3" hoặc "thứ 3 tối"

🎯 **Mức độ ưu tiên:**
- prio:1 (urgent) 🔴
- prio:2 (normal) 🟡  
- prio:3 (chill) 🟢

**Ví dụ:**
- `/todo tối thứ 6 đón mèo prio:1`
- `/todo đón mèo tối thứ 6 prio:1`
- `/event meeting chiều mai`
- `/idea học tiếng Nhật`
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

@check_user_access
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = """
🆘 **HƯỚNG DẪN CHI TIẾT**

✅ **TODOS:**
• `/todo dọn nhà tối thứ 6 prio:1` - Todo khẩn cấp
• `/todo mua sắm sáng mai prio:2` - Todo bình thường
• `/todo đọc sách prio:3` - Todo không gấp
• `/todolist` - Xem todos (sắp xếp theo mức độ + thời gian)
• `/done dọn` - Hoàn thành (tìm kiếm mờ)

📅 **EVENTS:**
• `/event họp chiều thứ 2` - Tạo sự kiện
• `/event sinh nhật tối 25/12` - Sự kiện theo ngày
• `/eventlist` - Xem events (sắp xếp theo thời gian)

💡 **IDEAS:**
• `/idea học guitar` - Lưu ý tưởng
• `/idealist` - Xem tất cả ideas

⏰ **Thời gian linh hoạt:**
• `sáng` = 09:00, `chiều` = 17:00, `tối` = 20:00, `đêm` = 22:00
• Thứ tự bất kỳ: `tối thứ 3` = `thứ 3 tối` = `đón mèo tối thứ 3`
• `hôm nay`, `mai`, `thứ 6 tuần sau`

🎯 **Mức độ ưu tiên:**
• 🔴 **prio:1**: khẩn cấp, quan trọng
• 🟡 **prio:2**: bình thường (mặc định)
• 🟢 **prio:3**: không gấp, chill

🔍 **Fuzzy Search:**
Bot tìm kiếm thông minh - chỉ cần gõ một phần tên task!

**Bắt đầu:** `/todo tối mai học tiếng Anh prio:1`
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

@check_user_access
async def todo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new todo"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Cần mô tả công việc!\n"
            "Ví dụ: `/todo tối thứ 6 đón mèo prio:1`\n"
            "Thứ tự từ linh hoạt!",
            parse_mode='Markdown'
        )
        return
    
    text = " ".join(context.args)
    
    # Parse time and priority
    time_info = parse_vietnamese_time(text)
    priority = parse_priority(text)
    
    # Clean text from both time and priority
    clean_text = time_info.get("parsed_text", text)
    clean_text = clean_priority_from_text(clean_text)
    
    # Add to database
    todo = await db_manager.add_todo(user_id, clean_text, time_info, priority)
    
    if todo:
        # Priority emojis
        priority_emoji = {"urgent": "🔴", "normal": "🟡", "chill": "🟢"}
        
        response = f"✅ **Todo đã thêm!**\n\n"
        response += f"📝 {clean_text}\n"
        response += f"{priority_emoji.get(priority, '🟡')} Mức độ: {priority}\n"
        
        if time_info.get("has_time"):
            response += f"⏰ {time_info.get('display_time', '')}\n"
        
        response += f"🆔 ID: {todo['id']}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Lỗi khi thêm todo!")

@check_user_access
async def event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new event"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Cần mô tả sự kiện!\n"
            "Ví dụ: `/event meeting chiều thứ 6`",
            parse_mode='Markdown'
        )
        return
    
    text = " ".join(context.args)
    
    # Parse time
    time_info = parse_vietnamese_time(text)
    clean_text = time_info.get("parsed_text", text)
    
    # Add to database
    event = await db_manager.add_event(user_id, clean_text, time_info)
    
    if event:
        response = f"📅 **Event đã thêm!**\n\n"
        response += f"📝 {clean_text}\n"
        
        if time_info.get("has_time"):
            response += f"⏰ {time_info.get('display_time', '')}\n"
        else:
            response += "⏰ Chưa có thời gian cụ thể\n"
        
        response += f"🆔 ID: {event['id']}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Lỗi khi thêm event!")

@check_user_access
async def idea_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new idea"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Cần mô tả ý tưởng!\n"
            "Ví dụ: `/idea học guitar`",
            parse_mode='Markdown'
        )
        return
    
    text = " ".join(context.args)
    
    # Add to database
    idea = await db_manager.add_idea(user_id, text)
    
    if idea:
        response = f"💡 **Idea đã thêm!**\n\n"
        response += f"📝 {text}\n"
        response += f"🆔 ID: {idea['id']}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Lỗi khi thêm idea!")

@check_user_access
async def todolist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View todolist sorted by priority and time"""
    user_id = update.effective_user.id
    todos = await db_manager.get_todos(user_id)
    
    if not todos:
        response = "📋 **Todolist trống**\n\n"
        response += "Thêm todo bằng: `/todo công việc thời gian prio:X`"
        await update.message.reply_text(response, parse_mode='Markdown')
        return
    
    response = "📋 **TODOLIST** (sắp xếp theo mức độ + thời gian)\n\n"
    
    # Group by priority
    urgent_todos = [t for t in todos if t.get("priority") == "urgent"]
    normal_todos = [t for t in todos if t.get("priority") == "normal"]
    chill_todos = [t for t in todos if t.get("priority") == "chill"]
    
    # Display urgent todos first
    if urgent_todos:
        response += "🔴 **URGENT:**\n"
        for todo in urgent_todos:
            status = "☑️" if todo["completed"] else "⬜"
            time_display = ""
            if todo.get("has_time") and todo.get("display_time"):
                time_display = f" - {todo['display_time']}"
            
            response += f"{status} {todo['text']}{time_display} (ID: {todo['id']})\n"
        response += "\n"
    
    # Normal todos
    if normal_todos:
        response += "🟡 **NORMAL:**\n"
        for todo in normal_todos:
            status = "☑️" if todo["completed"] else "⬜"
            time_display = ""
            if todo.get("has_time") and todo.get("display_time"):
                time_display = f" - {todo['display_time']}"
            
            response += f"{status} {todo['text']}{time_display} (ID: {todo['id']})\n"
        response += "\n"
    
    # Chill todos
    if chill_todos:
        response += "🟢 **CHILL:**\n"
        for todo in chill_todos:
            status = "☑️" if todo["completed"] else "⬜"
            time_display = ""
            if todo.get("has_time") and todo.get("display_time"):
                time_display = f" - {todo['display_time']}"
            
            response += f"{status} {todo['text']}{time_display} (ID: {todo['id']})\n"
        response += "\n"
    
    response += f"📊 Tổng: {len(todos)} tasks"
    response += "\n💡 Dùng `/done [mô tả]` để hoàn thành"
    
    await update.message.reply_text(response, parse_mode='Markdown')

@check_user_access
async def eventlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View event list sorted by time"""
    user_id = update.effective_user.id
    events = await db_manager.get_events(user_id)
    
    if not events:
        response = "📅 **Event list trống**\n\n"
        response += "Thêm event bằng: `/event hoạt động thời gian`"
        await update.message.reply_text(response, parse_mode='Markdown')
        return
    
    response = "📅 **EVENT LIST** (sắp xếp theo thời gian)\n\n"
    
    # Separate timed and non-timed events
    timed_events = [e for e in events if e.get("has_time")]
    no_time_events = [e for e in events if not e.get("has_time")]
    
    # Show timed events first
    if timed_events:
        response += "⏰ **Có thời gian:**\n"
        for event in timed_events:
            time_display = event.get("display_time", "")
            response += f"• {event['text']} - {time_display} (ID: {event['id']})\n"
        response += "\n"
    
    # Show non-timed events
    if no_time_events:
        response += "📝 **Chưa có thời gian:**\n"
        for event in no_time_events:
            response += f"• {event['text']} (ID: {event['id']})\n"
        response += "\n"
    
    response += f"📊 Tổng: {len(events)} events"
    
    await update.message.reply_text(response, parse_mode='Markdown')

@check_user_access
async def idealist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View idea list"""
    user_id = update.effective_user.id
    ideas = await db_manager.get_ideas(user_id)
    
    if not ideas:
        response = "💡 **Idea list trống**\n\n"
        response += "Thêm idea bằng: `/idea ý tưởng của bạn`"
        await update.message.reply_text(response, parse_mode='Markdown')
        return
    
    response = "💡 **IDEA LIST** (mới nhất trước)\n\n"
    
    for idea in ideas[:20]:  # Show latest 20 ideas
        response += f"• {idea['text']} (ID: {idea['id']})\n"
    
    if len(ideas) > 20:
        response += f"\n... và {len(ideas) - 20} ideas khác"
    
    response += f"\n📊 Tổng: {len(ideas)} ideas"
    
    await update.message.reply_text(response, parse_mode='Markdown')

@check_user_access
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark todo as completed using fuzzy search"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Cần mô tả task cần hoàn thành!\n"
            "Ví dụ: `/done đón mèo`\n"
            "Bot sẽ tìm task phù hợp nhất!",
            parse_mode='Markdown'
        )
        return
    
    search_text = " ".join(context.args)
    
    # Use fuzzy search to complete todo
    success = await db_manager.complete_todo_fuzzy(user_id, search_text)
    
    if success:
        await update.message.reply_text(
            f"✅ **Task hoàn thành!**\n\n"
            f"🔍 Tìm kiếm: '{search_text}'\n"
            f"📝 Task đã được đánh dấu hoàn thành!",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Không tìm thấy task phù hợp!\n\n"
            f"🔍 Tìm kiếm: '{search_text}'\n"
            f"💡 Dùng `/todolist` để xem danh sách",
            parse_mode='Markdown'
        )

# Additional helper functions for deletion (optional)
@check_user_access
async def delete_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete event using fuzzy search"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Cần mô tả event cần xóa!\n"
            "Ví dụ: `/delete_event meeting`",
            parse_mode='Markdown'
        )
        return
    
    search_text = " ".join(context.args)
    success = await db_manager.delete_event_fuzzy(user_id, search_text)
    
    if success:
        await update.message.reply_text(
            f"🗑️ **Event đã xóa!**\n\n"
            f"🔍 Tìm kiếm: '{search_text}'",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Không tìm thấy event phù hợp!\n\n"
            f"🔍 Tìm kiếm: '{search_text}'",
            parse_mode='Markdown'
        )

@check_user_access
async def delete_idea_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete idea using fuzzy search"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Cần mô tả idea cần xóa!\n"
            "Ví dụ: `/delete_idea học guitar`",
            parse_mode='Markdown'
        )
        return
    
    search_text = " ".join(context.args)
    success = await db_manager.delete_idea_fuzzy(user_id, search_text)
    
    if success:
        await update.message.reply_text(
            f"🗑️ **Idea đã xóa!**\n\n"
            f"🔍 Tìm kiếm: '{search_text}'",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Không tìm thấy idea phù hợp!\n\n"
            f"🔍 Tìm kiếm: '{search_text}'",
            parse_mode='Markdown'
        )