from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
from typing import Dict, List, Optional
from fuzzywuzzy import fuzz, process

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class SupabaseManager:
    def __init__(self):
        self.supabase = supabase
    
    async def add_todo(self, user_id: int, text: str, time_info: Dict, priority: str = 'normal') -> Dict:
        """Add new todo to Supabase"""
        todo_data = {
            "user_id": str(user_id),
            "text": text,
            "time_info": time_info,
            "priority": priority,
            "completed": False,
            "type": "todo",
            "created_at": datetime.now().isoformat()
        }
        
        try:
            result = self.supabase.table("todos").insert(todo_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error adding todo: {e}")
            return None
    
    async def add_event(self, user_id: int, text: str, time_info: Dict) -> Dict:
        """Add new event to Supabase"""
        event_data = {
            "user_id": str(user_id),
            "text": text,
            "time_info": time_info,
            "type": "event",
            "created_at": datetime.now().isoformat()
        }
        
        try:
            result = self.supabase.table("events").insert(event_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error adding event: {e}")
            return None
    
    async def add_idea(self, user_id: int, text: str) -> Dict:
        """Add new idea to Supabase"""
        idea_data = {
            "user_id": str(user_id),
            "text": text,
            "type": "idea",
            "created_at": datetime.now().isoformat()
        }
        
        try:
            result = self.supabase.table("ideas").insert(idea_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error adding idea: {e}")
            return None
    
    async def get_todos(self, user_id: int, include_completed: bool = False) -> List[Dict]:
        """Get todos for user, sorted by time and priority"""
        try:
            query = self.supabase.table("todos").select("*").eq("user_id", str(user_id))
            
            if not include_completed:
                query = query.eq("completed", False)
            
            result = query.execute()
            todos = result.data if result.data else []
            
            # Sort by priority and time
            def sort_key(todo):
                priority_order = {"urgent": 0, "normal": 1, "chill": 2}
                priority_score = priority_order.get(todo.get("priority", "normal"), 1)
                
                # Get datetime for sorting
                time_info = todo.get("time_info", {})
                if time_info.get("has_time") and time_info.get("datetime"):
                    try:
                        dt = datetime.fromisoformat(time_info["datetime"])
                        return (priority_score, dt)
                    except:
                        pass
                
                # Items without time go to end
                return (priority_score, datetime.max)
            
            return sorted(todos, key=sort_key)
        except Exception as e:
            print(f"Error getting todos: {e}")
            return []
    
    async def get_events(self, user_id: int) -> List[Dict]:
        """Get events for user, sorted by time"""
        try:
            result = self.supabase.table("events").select("*").eq("user_id", str(user_id)).execute()
            events = result.data if result.data else []
            
            # Sort by time
            def sort_key(event):
                time_info = event.get("time_info", {})
                if time_info.get("has_time") and time_info.get("datetime"):
                    try:
                        return datetime.fromisoformat(time_info["datetime"])
                    except:
                        pass
                return datetime.max
            
            return sorted(events, key=sort_key)
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
    
    async def get_ideas(self, user_id: int) -> List[Dict]:
        """Get ideas for user, sorted by creation time"""
        try:
            result = self.supabase.table("ideas").select("*").eq("user_id", str(user_id)).order("created_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting ideas: {e}")
            return []
    
    async def complete_todo_fuzzy(self, user_id: int, search_text: str) -> bool:
        """Complete todo using fuzzy search"""
        try:
            # Get all incomplete todos
            todos = await self.get_todos(user_id, include_completed=False)
            
            if not todos:
                return False
            
            # Create list of todo texts for fuzzy matching
            todo_texts = [todo["text"] for todo in todos]
            
            # Find best match using fuzzy search
            best_match = process.extractOne(search_text, todo_texts, scorer=fuzz.partial_ratio)
            
            if best_match and best_match[1] >= 60:  # 60% similarity threshold
                # Find the todo with matching text
                for todo in todos:
                    if todo["text"] == best_match[0]:
                        # Mark as completed
                        update_data = {
                            "completed": True,
                            "completed_at": datetime.now().isoformat()
                        }
                        
                        result = self.supabase.table("todos").update(update_data).eq("id", todo["id"]).execute()
                        return bool(result.data)
            
            return False
        except Exception as e:
            print(f"Error completing todo: {e}")
            return False
    
    async def delete_event_fuzzy(self, user_id: int, search_text: str) -> bool:
        """Delete event using fuzzy search"""
        try:
            events = await self.get_events(user_id)
            
            if not events:
                return False
            
            event_texts = [event["text"] for event in events]
            best_match = process.extractOne(search_text, event_texts, scorer=fuzz.partial_ratio)
            
            if best_match and best_match[1] >= 60:
                for event in events:
                    if event["text"] == best_match[0]:
                        result = self.supabase.table("events").delete().eq("id", event["id"]).execute()
                        return bool(result.data)
            
            return False
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False
    
    async def delete_idea_fuzzy(self, user_id: int, search_text: str) -> bool:
        """Delete idea using fuzzy search"""
        try:
            ideas = await self.get_ideas(user_id)
            
            if not ideas:
                return False
            
            idea_texts = [idea["text"] for idea in ideas]
            best_match = process.extractOne(search_text, idea_texts, scorer=fuzz.partial_ratio)
            
            if best_match and best_match[1] >= 60:
                for idea in ideas:
                    if idea["text"] == best_match[0]:
                        result = self.supabase.table("ideas").delete().eq("id", idea["id"]).execute()
                        return bool(result.data)
            
            return False
        except Exception as e:
            print(f"Error deleting idea: {e}")
            return False

# Global instance
db_manager = SupabaseManager()