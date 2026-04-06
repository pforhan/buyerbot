import os
import sys
from slack_sdk import WebClient
from slack_sdk.oauth.installation_store import Installation
from db import SQLModelInstallationStore, engine, install_engine, create_db_and_tables

def bootstrap():
    # Require interactive entry for the Bot Token
    token = input("Enter your Bot Token (xoxb-...): ").strip()

    if not token.startswith("xoxb-"):
        print("Error: Invalid token format. Must start with 'xoxb-'.")
        sys.exit(1)

    client = WebClient(token=token)
    
    try:
        print("Verifying token and fetching workspace metadata...")
        auth_test = client.auth_test()
        
        team_id = auth_test["team_id"]
        team_name = auth_test["team"]
        bot_user_id = auth_test["user_id"]
        # bot_id is provided directly in auth_test for bot tokens
        bot_id = auth_test.get("bot_id")
        
        if not bot_id:
            # Fallback if bot_id is missing for some reason
            print("Warning: bot_id not found in auth.test, using bot_user_id as fallback.")
            bot_id = bot_user_id
        
        print(f"Workspace: {team_name} ({team_id})")
        print(f"Bot User: {bot_user_id}")
        print(f"Bot ID: {bot_id}")
        
        installation = Installation(
            team_id=team_id,
            team_name=team_name,
            bot_token=token,
            bot_id=bot_id,
            bot_user_id=bot_user_id,
            user_id="BOOTSTRAP_USER", # Dummy installer ID
        )
        
        create_db_and_tables()
        store = SQLModelInstallationStore(install_engine)
        store.save(installation)
        
        print("\n✅ Workspace successfully registered in the database!")
        print("You can now run 'python app.py' and the bot will be active in this workspace.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    bootstrap()
