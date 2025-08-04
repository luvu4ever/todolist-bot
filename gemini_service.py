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
    Parse Vietnamese time expressions using Gemini AI
    Returns parsed datetime and cleaned text
    """
    current_date = datetime.now()
    current_weekday = current_date.strftime("%A")
    current_date_str = current_date.strftime("%d/%m/%Y")
    
    prompt = f"""
Bạn là một AI chuyên phân tích thời gian trong tiếng Việt. Hôm nay là {current_weekday} ngày {current_date_str}.

Hãy phân tích câu sau và trích xuất thông tin thời gian:
"{text}"

Quy tắc:
- "thứ 2" = Monday, "thứ 3" = Tuesday, ..., "thứ 7" = Saturday, "chủ nhật" = Sunday
- "ngày 19/10" = ngày 19 tháng 10 năm hiện tại
- "5h", "17h30", "9h sáng" = giờ trong ngày hôm nay (nếu không có ngày cụ thể)
- "mai", "ngày mai" = tomorrow
- "hôm nay" = today
- Nếu chỉ có giờ không có ngày = hôm nay

Trả về JSON với format:
{{
    "has_time": true/false,
    "datetime": "YYYY-MM-DD HH:MM" (nếu có thời gian),
    "date_only": "YYYY-MM-DD" (nếu chỉ có ngày),
    "time_only": "HH:MM" (nếu chỉ có giờ),
    "parsed_text": "text đã được làm sạch (bỏ phần thời gian)",
    "original_time_expression": "phần thời gian gốc được tìm thấy",
    "display_time": "thứ X ngày DD/MM" hoặc "hôm nay HH:MM"
}}

Ví dụ:
- "event thứ 6 thợ lắp đồ" → has_time: true, tìm thứ 6 tiếp theo
- "todo dọn nhà 5h" → has_time: true, hôm nay 5h
- "meeting ngày 19/10 lúc 14h" → has_time: true, ngày 19/10 14h
- "ghi nhớ mua sữa" → has_time: false
"""

    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"Gemini parsing error: {e}")
        # Fallback simple parsing
        return fallback_time_parse(text)

def fallback_time_parse(text):
    """Simple fallback parser when Gemini fails"""
    has_time = False
    parsed_text = text
    display_time = "không xác định"
    
    # Simple regex patterns
    time_patterns = [
        r'(\d{1,2}h\d{0,2})',  # 5h, 17h30
        r'(thứ \d)',           # thứ 2, thứ 3
        r'(ngày \d{1,2}/\d{1,2})',  # ngày 19/10
        r'(hôm nay|mai|ngày mai)'   # hôm nay, mai
    ]
    
    for pattern in time_patterns:
        if re.search(pattern, text.lower()):
            has_time = True
            display_time = "được phát hiện"
            break
    
    return {
        "has_time": has_time,
        "datetime": None,
        "date_only": None,
        "time_only": None,
        "parsed_text": parsed_text,
        "original_time_expression": "",
        "display_time": display_time
    }

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