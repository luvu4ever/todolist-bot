import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# File-based storage (can be replaced with Supabase later)
DATA_DIR = "data"
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
TODOS_FILE = os.path.join(DATA_DIR, "todos.json")
IDEAS_FILE = os.path.join(DATA_DIR, "ideas.json")

def ensure_data_dir():
    """Create data directory if it doesn't exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_json_file(filepath: str) -> List[Dict]:
    """Load JSON file or return empty list"""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_json_file(filepath: str, data: List[Dict]):
    """Save data to JSON file"""
    ensure_data_dir()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class DataManager:
    def __init__(self):
        self.events = load_json_file(EVENTS_FILE)
        self.todos = load_json_file(TODOS_FILE)
        self.ideas = load_json_file(IDEAS_FILE)
    
    def add_event(self, user_id: int, text: str, time_info: Dict) -> Dict:
        """Add new event"""
        event = {
            "id": len(self.events) + 1,
            "user_id": user_id,
            "text": text,
            "time_info": time_info,
            "created_at": datetime.now().isoformat(),
            "type": "event"
        }
        self.events.append(event)
        save_json_file(EVENTS_FILE, self.events)
        return event
    
    def add_todo(self, user_id: int, text: str, time_info: Dict) -> Dict:
        """Add new todo"""
        todo = {
            "id": len(self.todos) + 1,
            "user_id": user_id,
            "text": text,
            "time_info": time_info,
            "created_at": datetime.now().isoformat(),
            "completed": False,
            "type": "todo"
        }
        self.todos.append(todo)
        save_json_file(TODOS_FILE, self.todos)
        return todo
    
    def add_idea(self, user_id: int, text: str, time_info: Dict) -> Dict:
        """Add new idea"""
        idea = {
            "id": len(self.ideas) + 1,
            "user_id": user_id,
            "text": text,
            "time_info": time_info,
            "created_at": datetime.now().isoformat(),
            "type": "idea"
        }
        self.ideas.append(idea)
        save_json_file(IDEAS_FILE, self.ideas)
        return idea
    
    def complete_todo(self, user_id: int, todo_id: int = None, description: str = None) -> bool:
        """Mark todo as completed"""
        if todo_id:
            # Complete by ID
            for todo in self.todos:
                if todo["id"] == todo_id and todo["user_id"] == user_id:
                    todo["completed"] = True
                    todo["completed_at"] = datetime.now().isoformat()
                    save_json_file(TODOS_FILE, self.todos)
                    return True
        elif description:
            # Complete by description match
            for todo in self.todos:
                if (todo["user_id"] == user_id and 
                    not todo["completed"] and 
                    description.lower() in todo["text"].lower()):
                    todo["completed"] = True
                    todo["completed_at"] = datetime.now().isoformat()
                    save_json_file(TODOS_FILE, self.todos)
                    return True
        return False
    
    def get_user_events(self, user_id: int) -> List[Dict]:
        """Get all events for user"""
        return [e for e in self.events if e["user_id"] == user_id]
    
    def get_user_todos(self, user_id: int, include_completed: bool = False) -> List[Dict]:
        """Get todos for user"""
        todos = [t for t in self.todos if t["user_id"] == user_id]
        if not include_completed:
            todos = [t for t in todos if not t["completed"]]
        return todos
    
    def get_user_ideas(self, user_id: int) -> List[Dict]:
        """Get all ideas for user"""
        return [i for i in self.ideas if i["user_id"] == user_id]
    
    def get_all_user_items(self, user_id: int) -> Dict[str, List[Dict]]:
        """Get all items for user organized by type"""
        return {
            "events": self.get_user_events(user_id),
            "todos": self.get_user_todos(user_id),
            "ideas": self.get_user_ideas(user_id)
        }

# Global instance
data_manager = DataManager()