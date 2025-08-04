import google.generativeai as genai
from config import GEMINI_API_KEY
from datetime import datetime, timedelta
import json
import re

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def parse_vietnamese_time(text):
    """
    Parse Vietnamese time expressions using enhanced logic
    Returns parsed datetime and cleaned text
    """
    # Always try simple parsing first for reliability
    simple_result = fallback_time_parse(text)
    
    # If simple parsing found time, use it
    if simple_result["has_time"]:
        return simple_result
    
    # Try Gemini as backup
    current_date = datetime.now()
    current_weekday_vn = get_vietnamese_weekday_name(current_date.weekday())
    current_date_str = current_date.strftime("%d/%m/%Y")
    
    prompt = f"""
Phân tích thời gian trong câu tiếng Việt. Hôm nay là {current_weekday_vn} ngày {current_date_str}.

Câu: "{text}"

QUAN TRỌNG: Chỉ trả về JSON, không giải thích gì thêm.

Format JSON:
{{
    "has_time": true/false,
    "datetime": "YYYY-MM-DD HH:MM",
    "display_time": "thứ X ngày DD/MM",
    "parsed_text": "text sau khi bỏ thời gian"
}}

Ví dụ:
- "thứ 4 liên hệ gửi mèo" → {{"has_time": true, "datetime": "2025-08-06 09:00", "display_time": "thứ 4 ngày 06/08", "parsed_text": "liên hệ gửi mèo"}}
- "7/8 tiêm mèo" → {{"has_time": true, "datetime": "2025-08-07 09:00", "display_time": "thứ 4 ngày 07/08", "parsed_text": "tiêm mèo"}}
"""

    try:
        response = model.generate_content(prompt)
        clean_response = response.text.strip()
        # Remove markdown code blocks if present
        if clean_response.startswith('```'):
            clean_response = clean_response.split('\n', 1)[1]
        if clean_response.endswith('```'):
            clean_response = clean_response.rsplit('\n', 1)[0]
        
        result = json.loads(clean_response)
        return result
    except Exception as e:
        print(f"Gemini parsing error: {e}")
        return simple_result

def fallback_time_parse(text):
    """Enhanced fallback parser for Vietnamese time"""
    has_time = False
    parsed_text = text
    display_time = ""
    datetime_str = None
    
    current_date = datetime.now()
    
    # Pattern matching for Vietnamese time expressions
    text_lower = text.lower().strip()
    
    # 1. Weekday patterns (thứ 2, thứ 3, etc.)
    weekday_match = re.search(r'thứ\s+([2-7])', text_lower)
    if weekday_match:
        weekday_num = int(weekday_match.group(1)) - 2  # Convert to 0-6 (Mon-Sun)
        next_date = get_next_weekday(weekday_num)
        
        has_time = True
        datetime_str = next_date.strftime("%Y-%m-%d 09:00")  # Default to 9 AM
        display_time = f"{get_vietnamese_weekday_name(weekday_num)} ngày {next_date.strftime('%d/%m')}"
        parsed_text = re.sub(r'thứ\s+[2-7]', '', text, flags=re.IGNORECASE).strip()
    
    # 2. Sunday pattern
    elif re.search(r'chủ\s*nhật', text_lower):
        next_date = get_next_weekday(6)  # Sunday = 6
        has_time = True
        datetime_str = next_date.strftime("%Y-%m-%d 09:00")
        display_time = f"chủ nhật ngày {next_date.strftime('%d/%m')}"
        parsed_text = re.sub(r'chủ\s*nhật', '', text, flags=re.IGNORECASE).strip()
    
    # 3. Date patterns (7/8, ngày 7/8, 19/10)
    date_match = re.search(r'(?:ngày\s+)?(\d{1,2})/(\d{1,2})(?:/(\d{4}))?', text)
    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3)) if date_match.group(3) else current_date.year
        
        try:
            target_date = datetime(year, month, day)
            # If date is in the past, assume next year
            if target_date.date() < current_date.date():
                target_date = datetime(year + 1, month, day)
            
            has_time = True
            datetime_str = target_date.strftime("%Y-%m-%d 09:00")
            weekday_vn = get_vietnamese_weekday_name(target_date.weekday())
            display_time = f"{weekday_vn} ngày {target_date.strftime('%d/%m')}"
            parsed_text = re.sub(r'(?:ngày\s+)?\d{1,2}/\d{1,2}(?:/\d{4})?', '', text).strip()
        except ValueError:
            pass  # Invalid date
    
    # 4. Time patterns (5h, 14h30, 9h sáng)
    elif re.search(r'\d{1,2}h(?:\d{2})?', text_lower):
        time_match = re.search(r'(\d{1,2})h(\d{2})?(?:\s*(sáng|chiều|tối))?', text_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3)
            
            # Adjust hour based on period
            if period == 'chiều' and hour < 12:
                hour += 12
            elif period == 'tối' and hour < 12:
                hour += 12
            
            has_time = True
            datetime_str = current_date.strftime(f"%Y-%m-%d {hour:02d}:{minute:02d}")
            display_time = f"hôm nay {hour:02d}:{minute:02d}"
            parsed_text = re.sub(r'\d{1,2}h(?:\d{2})?(?:\s*(?:sáng|chiều|tối))?', '', text, flags=re.IGNORECASE).strip()
    
    # 5. Relative time (mai, ngày mai, hôm nay)
    elif re.search(r'(?:ngày\s+)?mai', text_lower):
        tomorrow = current_date + timedelta(days=1)
        has_time = True
        datetime_str = tomorrow.strftime("%Y-%m-%d 09:00")
        weekday_vn = get_vietnamese_weekday_name(tomorrow.weekday())
        display_time = f"{weekday_vn} ngày {tomorrow.strftime('%d/%m')} (mai)"
        parsed_text = re.sub(r'(?:ngày\s+)?mai', '', text, flags=re.IGNORECASE).strip()
    
    elif re.search(r'hôm\s+nay', text_lower):
        has_time = True
        datetime_str = current_date.strftime("%Y-%m-%d 09:00")
        display_time = "hôm nay"
        parsed_text = re.sub(r'hôm\s+nay', '', text, flags=re.IGNORECASE).strip()
    
    # Clean up parsed text
    parsed_text = re.sub(r'\s+', ' ', parsed_text).strip()
    
    return {
        "has_time": has_time,
        "datetime": datetime_str,
        "display_time": display_time,
        "parsed_text": parsed_text,
        "original_time_expression": ""
    }

def get_vietnamese_weekday_name(weekday_num):
    """Get Vietnamese weekday name from number (0=Monday)"""
    names = {
        0: "thứ 2",
        1: "thứ 3", 
        2: "thứ 4",
        3: "thứ 5",
        4: "thứ 6",
        5: "thứ 7",
        6: "chủ nhật"
    }
    return names.get(weekday_num, f"thứ {weekday_num + 2}")

def get_next_weekday(weekday):
    """Get next occurrence of a weekday (0=Monday, 6=Sunday)"""
    current = datetime.now()
    days_ahead = weekday - current.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return current + timedelta(days=days_ahead)

def classify_message_type(text):
    """
    Use Gemini to classify message type
    Returns: 'event', 'todo', 'idea'
    """
    prompt = f"""
Phân loại câu sau đây thuộc loại nào:
"{text}"

Loại:
- "event": Sự kiện, cuộc họp, lịch hẹn (có thời gian cụ thể)
- "todo": Công việc cần làm, nhiệm vụ
- "idea": Ý tưởng, ghi chú chung, không phải công việc cụ thể

Trả về chỉ một từ: event, todo, hoặc idea
"""

    try:
        response = model.generate_content(prompt)
        result = response.text.strip().lower()
        if result in ['event', 'todo', 'idea']:
            return result
        return 'idea'  # default
    except:
        # Simple fallback classification
        text_lower = text.lower()
        if any(word in text_lower for word in ['event', 'meeting', 'cuộc họp', 'hẹn']):
            return 'event'
        elif any(word in text_lower for word in ['todo', 'làm', 'dọn', 'mua', 'task']):
            return 'todo'
        else:
            return 'idea'