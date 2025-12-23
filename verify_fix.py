
import sqlite3
import os
import sys

# Mock logger
class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def debug(self, msg): print(f"[DEBUG] {msg}")
    def warning(self, msg): print(f"[WARNING] {msg}")

# Mock db_manager module structure to allow importing DBManager if needed, 
# but here we will just copy the relevant methods or mock the class since importing the whole app might be complex.
# Actually, let's try to import the real class if possible, but it depends on other modules.
# Let's just test the logic by creating a minimal subclass or just testing the SQL logic if we can't import.

# Try to import real db_manager
sys.path.append(os.getcwd())
try:
    from db_manager import DBManager
    print("Successfully imported DBManager")
except Exception as e:
    print(f"Failed to import DBManager: {e}")
    sys.exit(1)

def test_whitespace_stripping():
    print("\n--- Testing Whitespace Stripping ---")
    db_path = "test_verify.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DBManager(db_path)
    db.init_db()
    
    cookie_id = "test_user"
    
    # 1. Save with whitespace
    settings = {
        "ai_enabled": True,
        "api_key": "  sk-123456  ",
        "base_url": "  https://api.example.com  ",
        "model_name": "  gpt-4  "
    }
    db.save_ai_reply_settings(cookie_id, settings)
    
    # 2. Retrieve and check if stripped
    saved = db.get_ai_reply_settings(cookie_id)
    print(f"Saved API Key: '{saved['api_key']}'")
    print(f"Saved Base URL: '{saved['base_url']}'")
    print(f"Saved Model: '{saved['model_name']}'")
    
    assert saved['api_key'] == "sk-123456", "API Key not stripped!"
    assert saved['base_url'] == "https://api.example.com", "Base URL not stripped!"
    assert saved['model_name'] == "gpt-4", "Model Name not stripped!"
    print("✅ Whitespace stripping passed")
    
    db.close()
    os.remove(db_path)

def test_partial_update():
    print("\n--- Testing Partial Update ---")
    db_path = "test_verify_partial.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DBManager(db_path)
    db.init_db()
    
    cookie_id = "test_user"
    
    # 1. Initial save
    initial_settings = {
        "ai_enabled": True,
        "api_key": "sk-initial",
        "base_url": "https://initial.com",
        "model_name": "initial-model"
    }
    db.save_ai_reply_settings(cookie_id, initial_settings)
    
    # 2. Partial update (simulate exclude_unset=True)
    # Only update ai_enabled, should NOT overwrite others with None/Default
    partial_settings = {
        "ai_enabled": False
    }
    db.save_ai_reply_settings(cookie_id, partial_settings)
    
    # 3. Verify
    current = db.get_ai_reply_settings(cookie_id)
    print(f"Current AI Enabled: {current['ai_enabled']}")
    print(f"Current API Key: '{current['api_key']}'")
    
    assert current['ai_enabled'] == False, "AI Enabled not updated!"
    assert current['api_key'] == "sk-initial", "API Key was overwritten!"
    assert current['base_url'] == "https://initial.com", "Base URL was overwritten!"
    
    print("✅ Partial update passed (fields preserved)")
    
    db.close()
    os.remove(db_path)

if __name__ == "__main__":
    try:
        test_whitespace_stripping()
        test_partial_update()
        print("\n🎉 All verification tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
