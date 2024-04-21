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
    print("User status updated successfully.")

