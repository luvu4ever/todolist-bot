import uuid
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

class SupabaseManager:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.table = "todo_items"
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the todo_items table exists with proper schema"""
        # Note: You need to create this table in Supabase dashboard first
        # SQL to create table:
        """
        CREATE TABLE IF NOT EXISTS todo_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id BIGINT NOT NULL,
            type VARCHAR(20) NOT NULL CHECK (type IN ('event', 'todo', 'idea')),
            text TEXT NOT NULL,
            time_info JSONB,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_todo_items_user_id ON todo_items(user_id);
        CREATE INDEX IF NOT EXISTS idx_todo_items_type ON todo_items(type);
        CREATE INDEX IF NOT EXISTS idx_todo_items_completed ON todo_items(completed);
        CREATE INDEX IF NOT EXISTS idx_todo_items_created_at ON todo_items(created_at);
        
        -- Enable Row Level Security (optional but recommended)
        ALTER TABLE todo_items ENABLE ROW LEVEL SECURITY;
        """
        pass
    
    def add_event(self, user_id: int, text: str, time_info: Dict) -> Dict:
        """Add new event to Supabase"""
        try:
            data = {
                "user_id": user_id,
                "type": "event",
                "text": text,
                "time_info": time_info,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table(self.table).insert(data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                raise Exception("Failed to insert event")
                
        except Exception as e:
            print(f"Error adding event: {e}")
            raise
    
    def add_todo(self, user_id: int, text: str, time_info: Dict) -> Dict:
        """Add new todo to Supabase"""
        try:
            data = {
                "user_id": user_id,
                "type": "todo",
                "text": text,
                "time_info": time_info,
                "completed": False,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table(self.table).insert(data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                raise Exception("Failed to insert todo")
                
        except Exception as e:
            print(f"Error adding todo: {e}")
            raise
    
    def add_idea(self, user_id: int, text: str, time_info: Dict) -> Dict:
        """Add new idea to Supabase"""
        try:
            data = {
                "user_id": user_id,
                "type": "idea",
                "text": text,
                "time_info": time_info,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table(self.table).insert(data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                raise Exception("Failed to insert idea")
                
        except Exception as e:
            print(f"Error adding idea: {e}")
            raise
    
    def complete_todo(self, user_id: int, todo_id: str = None, description: str = None) -> bool:
        """Mark todo as completed"""
        try:
            update_data = {
                "completed": True,
                "completed_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            query = self.client.table(self.table).update(update_data).eq("user_id", user_id).eq("type", "todo").eq("completed", False)
            
            if todo_id:
                # Complete by ID
                result = query.eq("id", todo_id).execute()
            elif description:
                # Complete by description match (case insensitive)
                result = query.ilike("text", f"%{description}%").execute()
            else:
                return False
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error completing todo: {e}")
            return False
    
    def remove_event(self, user_id: int, event_id: str = None, description: str = None) -> bool:
        """Remove event by ID or description"""
        try:
            query = self.client.table(self.table).delete().eq("user_id", user_id).eq("type", "event")
            
            if event_id:
                result = query.eq("id", event_id).execute()
            elif description:
                result = query.ilike("text", f"%{description}%").execute()
            else:
                return False
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error removing event: {e}")
            return False
    
    def remove_idea(self, user_id: int, idea_id: str = None, description: str = None) -> bool:
        """Remove idea by ID or description"""
        try:
            query = self.client.table(self.table).delete().eq("user_id", user_id).eq("type", "idea")
            
            if idea_id:
                result = query.eq("id", idea_id).execute()
            elif description:
                result = query.ilike("text", f"%{description}%").execute()
            else:
                return False
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error removing idea: {e}")
            return False
    
    def get_user_events(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all events for user"""
        try:
            result = self.client.table(self.table)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("type", "event")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
    
    def get_user_todos(self, user_id: int, include_completed: bool = False, limit: int = 50) -> List[Dict]:
        """Get todos for user"""
        try:
            query = self.client.table(self.table)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("type", "todo")
            
            if not include_completed:
                query = query.eq("completed", False)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting todos: {e}")
            return []
    
    def get_user_ideas(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all ideas for user"""
        try:
            result = self.client.table(self.table)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("type", "idea")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting ideas: {e}")
            return []
    
    def get_all_user_items(self, user_id: int, limit_per_type: int = 50) -> Dict[str, List[Dict]]:
        """Get all items for user organized by type"""
        return {
            "events": self.get_user_events(user_id, limit_per_type),
            "todos": self.get_user_todos(user_id, limit=limit_per_type),
            "ideas": self.get_user_ideas(user_id, limit_per_type)
        }
    
    def get_upcoming_items(self, user_id: int, days_ahead: int = 7) -> List[Dict]:
        """Get items with upcoming deadlines"""
        try:
            from datetime import timedelta
            future_limit = datetime.now() + timedelta(days=days_ahead)
            
            # Query items with time_info containing datetime
            result = self.client.table(self.table)\
                .select("*")\
                .eq("user_id", user_id)\
                .not_.is_("time_info", "null")\
                .order("created_at", desc=True)\
                .execute()
            
            upcoming = []
            now = datetime.now()
            
            for item in result.data:
                time_info = item.get("time_info", {})
                if not time_info or not time_info.get("has_time"):
                    continue
                
                try:
                    if time_info.get("datetime"):
                        item_time = datetime.fromisoformat(time_info["datetime"])
                        if now <= item_time <= future_limit:
                            upcoming.append(item)
                except:
                    continue
            
            return sorted(upcoming, key=lambda x: x.get("time_info", {}).get("datetime", ""))
            
        except Exception as e:
            print(f"Error getting upcoming items: {e}")
            return []
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        try:
            # Count by type
            result = self.client.table(self.table)\
                .select("type", count="exact")\
                .eq("user_id", user_id)\
                .execute()
            
            stats = {
                "events_count": 0,
                "todos_total": 0,
                "todos_completed": 0,
                "todos_pending": 0,
                "ideas_count": 0
            }
            
            # Get counts by type
            events_result = self.client.table(self.table).select("*", count="exact").eq("user_id", user_id).eq("type", "event").execute()
            stats["events_count"] = events_result.count or 0
            
            ideas_result = self.client.table(self.table).select("*", count="exact").eq("user_id", user_id).eq("type", "idea").execute()
            stats["ideas_count"] = ideas_result.count or 0
            
            todos_result = self.client.table(self.table).select("*", count="exact").eq("user_id", user_id).eq("type", "todo").execute()
            stats["todos_total"] = todos_result.count or 0
            
            completed_todos = self.client.table(self.table).select("*", count="exact").eq("user_id", user_id).eq("type", "todo").eq("completed", True).execute()
            stats["todos_completed"] = completed_todos.count or 0
            
            stats["todos_pending"] = stats["todos_total"] - stats["todos_completed"]
            
            return stats
            
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {
                "events_count": 0,
                "todos_total": 0,
                "todos_completed": 0,
                "todos_pending": 0,
                "ideas_count": 0
            }

# Global instance
try:
    data_manager = SupabaseManager()
    print("✅ Connected to Supabase successfully")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    raise