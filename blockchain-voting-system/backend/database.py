# database.py
import os
from supabase import create_client, Client

# These must match the ones your friend is using in his Node.js .env file
SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_FRIENDS_SUPABASE_URL_HERE")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_FRIENDS_SUPABASE_KEY_HERE")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_voter(voter_id, name, wallet_address, face_encoding):
    """
    Saves a new voter to the Supabase 'voters' table.
    face_encoding is a list of 128 floats.
    """
    try:
        data, count = supabase.table('voters').insert({
            "voter_id": voter_id,
            "name": name,
            "wallet_address": wallet_address,
            "face_encoding": face_encoding, 
            "has_voted": False
        }).execute()
        return True
    except Exception as e:
        print(f"Supabase Error: {e}")
        return False

def get_voter(voter_id):
    """
    Fetches a voter from Supabase by their voter_id.
    """
    try:
        response = supabase.table('voters').select("*").eq("voter_id", voter_id).execute()
        # response.data is a list of matching rows
        if len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Supabase Error: {e}")
        return None