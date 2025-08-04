"""
Utility functions for the todolist bot
"""

from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple

def format_time_display(time_info: Dict) -> str:
    """Format time information for display"""
    if not time_info.get("has_time"):
        return ""
    
    display = time_info.get("display_time", "")
    if display and display != "không xác định":
        return f"⏰ {display}"
    
    # Fallback formatting
    if time_info.get("datetime"):
        dt = datetime.fromisoformat(time_info["datetime"])
        weekday = get_vietnamese_weekday(dt.weekday())
        return f"⏰ {weekday} ngày {dt.strftime('%d/%m')} lúc {dt.strftime('%H:%M')}"
    elif time_info.get("date_only"):
        dt = datetime.fromisoformat(time_info["date_only"])
        weekday = get_vietnamese_weekday(dt.weekday())
        return f"⏰ {weekday} ngày {dt.strftime('%d/%m')}"
    elif time_info.get("time_only"):
        return f"⏰ hôm nay {time_info['time_only']}"
    
    return ""

def get_vietnamese_weekday(weekday_num: int) -> str:
    """Convert weekday number to Vietnamese"""
    weekdays = {
        0: "thứ 2",  # Monday
        1: "thứ 3",  # Tuesday  
        2: "thứ 4",  # Wednesday
        3: "thứ 5",  # Thursday
        4: "thứ 6",  # Friday
        5: "thứ 7",  # Saturday
        6: "chủ nhật"  # Sunday
    }
    return weekdays.get(weekday_num, f"thứ {weekday_num + 2}")

def parse_weekday_vietnamese(weekday_str: str) -> Optional[int]:
    """Parse Vietnamese weekday to number (0=Monday)"""
    weekday_str = weekday_str.lower().strip()
    
    mappings = {
        "thứ 2": 0, "thứ hai": 0, "t2": 0,
        "thứ 3": 1, "thứ ba": 1, "t3": 1,
        "thứ 4": 2, "thứ tư": 2, "t4": 2,
        "thứ 5": 3, "thứ năm": 3, "t5": 3,
        "thứ 6": 4, "thứ sáu": 4, "t6": 4,
        "thứ 7": 5, "thứ bảy": 5, "t7": 5,
        "chủ nhật": 6, "cn": 6, "sunday": 6
    }
    
    return mappings.get(weekday_str)

def extract_time_patterns(text: str) -> List[Dict]:
    """Extract time patterns from text using regex"""
    patterns = []
    
    # Time patterns (5h, 14h30, 9h sáng)
    time_pattern = r'(\d{1,2}h(?:\d{2})?(?:\s*(?:sáng|chiều|tối|đêm))?)'
    times = re.findall(time_pattern, text.lower())
    for time_match in times:
        patterns.append({
            "type": "time",
            "match": time_match,
            "pattern": "time"
        })
    
    # Weekday patterns (thứ 2, thứ 6)
    weekday_pattern = r'(thứ\s+[2-7]|chủ\s+nhật)'
    weekdays = re.findall(weekday_pattern, text.lower())
    for weekday_match in weekdays:
        patterns.append({
            "type": "weekday", 
            "match": weekday_match,
            "pattern": "weekday"
        })
    
    # Date patterns (ngày 19/10, 25/12)
    date_pattern = r'(?:ngày\s+)?(\d{1,2}/\d{1,2}(?:/\d{4})?)'
    dates = re.findall(date_pattern, text)
    for date_match in dates:
        patterns.append({
            "type": "date",
            "match": date_match,
            "pattern": "date"
        })
    
    # Relative time (hôm nay, mai, ngày mai)
    relative_pattern = r'(hôm\s+nay|ngày\s+mai|mai(?:\s+này)?)'
    relatives = re.findall(relative_pattern, text.lower())
    for relative_match in relatives:
        patterns.append({
            "type": "relative",
            "match": relative_match,
            "pattern": "relative"
        })
    
    return patterns

def clean_text_from_time(text: str, time_patterns: List[Dict]) -> str:
    """Remove time expressions from text"""
    clean_text = text
    
    for pattern in time_patterns:
        # Remove the matched pattern from text
        clean_text = re.sub(
            re.escape(pattern["match"]), 
            "", 
            clean_text, 
            flags=re.IGNORECASE
        ).strip()
    
    # Clean up extra spaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

def format_item_list(items: List[Dict], item_type: str) -> str:
    """Format list of items for display"""
    if not items:
        return f"Không có {item_type} nào."
    
    emoji_map = {
        "event": "📅",
        "todo": "✅", 
        "idea": "💡"
    }
    
    emoji = emoji_map.get(item_type, "📝")
    result = f"{emoji} **{item_type.title()}s:**\n"
    
    for item in items[-10:]:  # Show last 10 items
        status = ""
        if item_type == "todo":
            status = "☑️ " if item.get("completed") else "⬜ "
        
        result += f"{status}• {item['text']}"
        
        # Add time info if available
        time_display = format_time_display(item.get("time_info", {}))
        if time_display:
            result += f" {time_display}"
        
        result += f" (ID: {item['id']})\n"
    
    return result

def validate_environment() -> Tuple[bool, List[str]]:
    """Validate required environment variables"""
    errors = []
    
    from config import TELEGRAM_BOT_TOKEN, GEMINI_API_KEY
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is missing")
    
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is missing")
    
    return len(errors) == 0, errors

def get_upcoming_items(items: List[Dict], days_ahead: int = 7) -> List[Dict]:
    """Get items with upcoming deadlines"""
    upcoming = []
    now = datetime.now()
    future_limit = now + timedelta(days=days_ahead)
    
    for item in items:
        time_info = item.get("time_info", {})
        if not time_info.get("has_time"):
            continue
        
        try:
            if time_info.get("datetime"):
                item_time = datetime.fromisoformat(time_info["datetime"])
                if now <= item_time <= future_limit:
                    upcoming.append(item)
            elif time_info.get("date_only"):
                item_date = datetime.fromisoformat(time_info["date_only"])
                if now.date() <= item_date.date() <= future_limit.date():
                    upcoming.append(item)
        except:
            continue  # Skip items with invalid time info
    
    return sorted(upcoming, key=lambda x: x.get("time_info", {}).get("datetime", ""))

def generate_summary_stats(all_items: Dict[str, List[Dict]]) -> str:
    """Generate summary statistics"""
    stats = []
    
    # Count by type
    events_count = len(all_items.get("events", []))
    todos_total = len(all_items.get("todos", []))
    todos_pending = len([t for t in all_items.get("todos", []) if not t.get("completed")])
    ideas_count = len(all_items.get("ideas", []))
    
    stats.append(f"📅 Events: {events_count}")
    stats.append(f"✅ Todos: {todos_pending}/{todos_total}")
    stats.append(f"💡 Ideas: {ideas_count}")
    
    # Upcoming items
    all_timed_items = []
    for item_list in all_items.values():
        all_timed_items.extend(item_list)
    
    upcoming = get_upcoming_items(all_timed_items)
    if upcoming:
        stats.append(f"⏰ Upcoming: {len(upcoming)}")
    
    return " | ".join(stats)