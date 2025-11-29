#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOCODB_BASE_URL = os.environ.get("NOCODB_BASE_URL", "https://app.nocodb.com")
NOCODB_API_TOKEN = os.environ.get("NOCODB_API_TOKEN")
NOCODB_BASE_ID = os.environ.get("NOCODB_BASE_ID", "")

HEADERS = {
    "xc-token": NOCODB_API_TOKEN,
    "Content-Type": "application/json"
}

def list_tables():
    url = f"{NOCODB_BASE_URL}/api/v2/meta/bases/{NOCODB_BASE_ID}/tables"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    
    print("Tables in NocoDB base:\n")
    
    semantic_tables = {}
    for table in data.get("list", []):
        table_name = table.get("title", "")
        table_id = table.get("id", "")
        print(f"  {table_name}: {table_id}")
        
        if table_name in ["Embeddings", "UserMemory", "ConversationHistory"]:
            semantic_tables[table_name] = table_id
    
    print("\n--- Semantic Search Table IDs ---")
    print("Add these to your .env file:\n")
    
    if "Embeddings" in semantic_tables:
        print(f"NOCODB_EMBEDDINGS_TABLE_ID={semantic_tables['Embeddings']}")
    if "UserMemory" in semantic_tables:
        print(f"NOCODB_USERMEMORY_TABLE_ID={semantic_tables['UserMemory']}")
    if "ConversationHistory" in semantic_tables:
        print(f"NOCODB_CONVERSATIONHISTORY_TABLE_ID={semantic_tables['ConversationHistory']}")

if __name__ == "__main__":
    list_tables()

