from supabase import create_client, Client
from config import get_settings

# Supabase client initialization
url: str = get_settings().DATABASE_URL
key: str = get_settings().DATABASE_KEY  # Replace with your Supabase anon key
supabase: Client = create_client(url, key)

def is_user_active(chat_id):
    result = supabase.table("Users").select("is_active").eq("chat_id", chat_id).execute()
    if result.data and result.data[0]['is_active']:
        return True
    return False

def add_user(chat_id):
    # Check if a user already exists with the given chat_id
    exists_response = supabase.table("Users").select("chat_id").eq("chat_id", chat_id).execute()
    
    if exists_response.data:
        set_user_active(chat_id, active=True)
    else:
        # No user exists with this chat_id, insert a new record
        supabase.table("Users").insert({"chat_id": chat_id, "is_active": True}).execute()


def set_user_active(chat_id, active):
    supabase.table("Users").update({"is_active": active}).eq("chat_id", chat_id).execute()
    print(f"User status set to {active}")

# Load tasks from JSON file
def load_tasks(chat_id):
    result = supabase.table("Tasks").select("*").eq("chat_id", chat_id).execute()
    return result.data if result.data else []

def save_task(chat_id, task_name, due_date=None):
    task_data = {
        'chat_id': chat_id,
        'task_name': task_name,
        'due_date': str(due_date) if due_date else None
    }
    supabase.table("Tasks").insert(task_data).execute()

def fetch_active_users():
    """Fetches active users from the Users table."""
    response = supabase.table("Users").select("chat_id").eq("is_active", True).execute()
    if response.data:
        return {user['chat_id'] for user in response.data}
    return set()

def fetch_all_tasks():
    """Fetches all tasks from the Tasks table."""
    response = supabase.table("Tasks").select("*").execute()
    return response.data if response.data else []

def task_name_exists(chat_id, task_name):
    """Checks if a given task name already exists for a specific chat_id."""
    response = supabase.table("Tasks").select("task_name").eq("chat_id", chat_id).eq("task_name", task_name).execute()
    return bool(response.data)  # Returns True if any task exists, False otherwise

def update_task_due_date(chat_id, task_name, new_due_date):
    """Updates the due date of a specific task."""
    return supabase.table("Tasks").update({"due_date": new_due_date}).eq("chat_id", chat_id).eq("task_name", task_name).execute()

def delete_task(chat_id, task_name):
    """Deletes a specific task based on chat_id and task_name."""
    return supabase.table("Tasks").delete().eq("chat_id", chat_id).eq("task_name", task_name).execute()