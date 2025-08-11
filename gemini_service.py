import google.generativeai as genai
from config import GEMINI_API_KEY
from datetime import datetime, timedelta
import json
import re

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

def parse_vietnamese_time(text):
    """
    Parse Vietnamese time expressions using Gemini AI
    Returns parsed datetime and cleaned text in format "thứ x, ngày dd/mm"
    """
    current_date = datetime.now()
    current_weekday_vn = get_vietnamese_weekday_name(current_date.weekday())
    current_date_str = current_date.strftime("%d/%m/%Y")
    
    prompt = f"""
Phân tích thời gian trong câu tiếng Việt. Hôm nay là {current_weekday_vn} ngày {current_date_str}.

Câu: "{text}"

Quy tắc xử lý thời gian:
- "hôm nay" = hôm nay
- "mai", "ngày mai" = ngày mai
- "thứ X" = thứ X tuần này nếu chưa qua, nếu đã qua thì thứ X tuần sau
- "thứ X tuần sau" = thứ X của tuần sau
- "tuần sau" = tuần sau (thứ 2)
- "tháng sau" = ngày 1 tháng sau
- "dd/mm" hoặc "ngày dd/mm" = ngày dd/mm năm nay, nếu đã qua thì năm sau

Format JSON trả về:
{{
    "has_time": true/false,
    "datetime": "YYYY-MM-DD HH:MM",
    "display_time": "thứ X, ngày DD/MM",
    "parsed_text": "text sau khi bỏ thời gian"
}}

Ví dụ:
- "thứ 4 liên hệ gửi mèo" → {{"has_time": true, "datetime": "2025-08-13 09:00", "display_time": "thứ 4, ngày 13/08", "parsed_text": "liên hệ gửi mèo"}}
- "7/8 tiêm mèo" → {{"has_time": true, "datetime": "2025-08-07 09:00", "display_time": "thứ 4, ngày 07/08", "parsed_text": "tiêm mèo"}}
- "thứ 6 tuần sau đi chơi" → {{"has_time": true, "datetime": "2025-08-22 09:00", "display_time": "thứ 6, ngày 22/08", "parsed_text": "đi chơi"}}

QUAN TRỌNG: Chỉ trả về JSON hợp lệ, không giải thích gì thêm.
"""

    try:
        response = gemini_model.generate_content(prompt)
        clean_response = response.text.strip()
        
        # Remove markdown code blocks if present
        if clean_response.startswith('```'):
            lines = clean_response.split('\n')
            clean_response = '\n'.join(lines[1:-1]) if len(lines) > 2 else clean_response
        
        result = json.loads(clean_response)
        
        # Validate result structure
        if not isinstance(result, dict):
            raise ValueError("Invalid JSON structure")
        
        # Ensure required fields
        result.setdefault("has_time", False)
        result.setdefault("datetime", None)
        result.setdefault("display_time", "")
        result.setdefault("parsed_text", text)
        
        return result
    except Exception as e:
        print(f"Gemini parsing error: {e}")
        return fallback_time_parse(text)

def fallback_time_parse(text):
    """Enhanced fallback parser for Vietnamese time"""
    has_time = False
    parsed_text = text
    display_time = ""
    datetime_str = None
    
    current_date = datetime.now()
    text_lower = text.lower().strip()
    
    # 1. Today patterns
    if re.search(r'hôm\s+nay', text_lower):
        has_time = True
        datetime_str = current_date.strftime("%Y-%m-%d 09:00")
        display_time = f"{get_vietnamese_weekday_name(current_date.weekday())}, ngày {current_date.strftime('%d/%m')}"
        parsed_text = re.sub(r'hôm\s+nay', '', text, flags=re.IGNORECASE).strip()
    
    # 2. Tomorrow patterns
    elif re.search(r'(?:ngày\s+)?mai', text_lower):
        tomorrow = current_date + timedelta(days=1)
        has_time = True
        datetime_str = tomorrow.strftime("%Y-%m-%d 09:00")
        display_time = f"{get_vietnamese_weekday_name(tomorrow.weekday())}, ngày {tomorrow.strftime('%d/%m')}"
        parsed_text = re.sub(r'(?:ngày\s+)?mai', '', text, flags=re.IGNORECASE).strip()
    
    # 3. Weekday patterns with "tuần sau"
    elif re.search(r'thứ\s+([2-7])\s+tuần\s+sau', text_lower):
        weekday_match = re.search(r'thứ\s+([2-7])\s+tuần\s+sau', text_lower)
        weekday_num = int(weekday_match.group(1)) - 2  # Convert to 0-6
        next_week_date = get_next_weekday(weekday_num, weeks_ahead=1)
        
        has_time = True
        datetime_str = next_week_date.strftime("%Y-%m-%d 09:00")
        display_time = f"{get_vietnamese_weekday_name(weekday_num)}, ngày {next_week_date.strftime('%d/%m')}"
        parsed_text = re.sub(r'thứ\s+[2-7]\s+tuần\s+sau', '', text, flags=re.IGNORECASE).strip()
    
    # 4. Regular weekday patterns
    elif re.search(r'thứ\s+([2-7])', text_lower):
        weekday_match = re.search(r'thứ\s+([2-7])', text_lower)
        weekday_num = int(weekday_match.group(1)) - 2  # Convert to 0-6
        next_date = get_next_weekday(weekday_num)
        
        has_time = True
        datetime_str = next_date.strftime("%Y-%m-%d 09:00")
        display_time = f"{get_vietnamese_weekday_name(weekday_num)}, ngày {next_date.strftime('%d/%m')}"
        parsed_text = re.sub(r'thứ\s+[2-7]', '', text, flags=re.IGNORECASE).strip()
    
    # 5. Sunday patterns
    elif re.search(r'chủ\s*nhật', text_lower):
        next_date = get_next_weekday(6)  # Sunday = 6
        has_time = True
        datetime_str = next_date.strftime("%Y-%m-%d 09:00")
        display_time = f"chủ nhật, ngày {next_date.strftime('%d/%m')}"
        parsed_text = re.sub(r'chủ\s*nhật', '', text, flags=re.IGNORECASE).strip()
    
    # 6. Date patterns (7/8, ngày 7/8, 19/10)
    elif re.search(r'(?:ngày\s+)?(\d{1,2})/(\d{1,2})(?:/(\d{4}))?', text):
        date_match = re.search(r'(?:ngày\s+)?(\d{1,2})/(\d{1,2})(?:/(\d{4}))?', text)
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
            display_time = f"{weekday_vn}, ngày {target_date.strftime('%d/%m')}"
            parsed_text = re.sub(r'(?:ngày\s+)?\d{1,2}/\d{1,2}(?:/\d{4})?', '', text).strip()
        except ValueError:
            pass  # Invalid date
    
    # Clean up parsed text
    parsed_text = re.sub(r'\s+', ' ', parsed_text).strip()
    
    return {
        "has_time": has_time,
        "datetime": datetime_str,
        "display_time": display_time,
        "parsed_text": parsed_text
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

def get_next_weekday(weekday, weeks_ahead=0):
    """Get next occurrence of a weekday (0=Monday, 6=Sunday)"""
    current = datetime.now()
    days_ahead = weekday - current.weekday() + (weeks_ahead * 7)
    if days_ahead <= 0 and weeks_ahead == 0:  # Target day already happened this week
        days_ahead += 7
    return current + timedelta(days=days_ahead)

def parse_priority(text):
    """
    Parse priority from text using Gemini AI
    Returns: 'urgent', 'normal', 'chill'
    """
    prompt = f"""
Phân tích mức độ ưu tiên trong câu tiếng Việt:
"{text}"

Mức độ ưu tiên:
- "urgent": gấp, khẩn cấp, cần làm ngay, quan trọng, deadline gần
- "normal": bình thường, không có từ khóa đặc biệt
- "chill": không gấp, rảnh rỗi, khi nào có thời gian, thảnh thơi

Trả về chỉ một từ: urgent, normal, hoặc chill
"""

    try:
        response = gemini_model.generate_content(prompt)
        result = response.text.strip().lower()
        if result in ['urgent', 'normal', 'chill']:
            return result
        return 'normal'  # default
    except:
        # Simple fallback priority detection
        text_lower = text.lower()
        if any(word in text_lower for word in ['gấp', 'khẩn cấp', 'ngay', 'quan trọng', 'deadline']):
            return 'urgent'
        elif any(word in text_lower for word in ['rảnh', 'thảnh thơi', 'không gấp', 'khi nào']):
            return 'chill'
        else:
            return 'normal'