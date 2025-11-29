#!/usr/bin/env python3
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

NOCODB_BASE_URL = os.environ.get("NOCODB_BASE_URL", "https://app.nocodb.com")
NOCODB_API_TOKEN = os.environ.get("NOCODB_API_TOKEN")
NOCODB_BASE_ID = os.environ.get("NOCODB_BASE_ID", "")

HEADERS = {
    "xc-token": NOCODB_API_TOKEN,
    "Content-Type": "application/json"
}

EMBEDDINGS_TABLE = {
    "table_name": "Embeddings",
    "title": "Embeddings",
    "columns": [
        {"column_name": "entity_type", "title": "entity_type", "uidt": "SingleLineText"},
        {"column_name": "entity_id", "title": "entity_id", "uidt": "Number"},
        {"column_name": "embedding_type", "title": "embedding_type", "uidt": "SingleLineText"},
        {"column_name": "embedding_vector", "title": "embedding_vector", "uidt": "LongText"},
        {"column_name": "embedding_model", "title": "embedding_model", "uidt": "SingleLineText"},
        {"column_name": "content_hash", "title": "content_hash", "uidt": "SingleLineText"},
    ]
}

USER_MEMORY_TABLE = {
    "table_name": "UserMemory",
    "title": "UserMemory",
    "columns": [
        {"column_name": "user_id", "title": "user_id", "uidt": "Number"},
        {"column_name": "memory_type", "title": "memory_type", "uidt": "SingleLineText"},
        {"column_name": "content", "title": "content", "uidt": "LongText"},
        {"column_name": "importance_score", "title": "importance_score", "uidt": "Decimal"},
        {"column_name": "embedding_vector", "title": "embedding_vector", "uidt": "LongText"},
        {"column_name": "metadata", "title": "metadata", "uidt": "LongText"},
        {"column_name": "last_accessed", "title": "last_accessed", "uidt": "DateTime"},
    ]
}

CONVERSATION_HISTORY_TABLE = {
    "table_name": "ConversationHistory",
    "title": "ConversationHistory",
    "columns": [
        {"column_name": "conversation_id", "title": "conversation_id", "uidt": "SingleLineText"},
        {"column_name": "user_id", "title": "user_id", "uidt": "Number"},
        {"column_name": "messages", "title": "messages", "uidt": "LongText"},
        {"column_name": "summary", "title": "summary", "uidt": "LongText"},
        {"column_name": "is_active", "title": "is_active", "uidt": "Checkbox"},
    ]
}

def create_table(table_def):
    url = f"{NOCODB_BASE_URL}/api/v2/meta/bases/{NOCODB_BASE_ID}/tables"
    response = requests.post(url, headers=HEADERS, json=table_def)
    response.raise_for_status()
    result = response.json()
    print(f"[OK] Created table: {table_def['table_name']} (ID: {result.get('id')})")
    return result

def main():
    if not NOCODB_API_TOKEN:
        print("[ERROR] NOCODB_API_TOKEN not set")
        return
    if not NOCODB_BASE_ID:
        print("[ERROR] NOCODB_BASE_ID not set")
        return
    
    print("Creating NocoDB tables for Semantic Search System...")
    
    tables = [EMBEDDINGS_TABLE, USER_MEMORY_TABLE, CONVERSATION_HISTORY_TABLE]
    created_tables = {}
    
    for table_def in tables:
        try:
            result = create_table(table_def)
            created_tables[table_def["table_name"]] = result.get("id")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                print(f"[WARN] Table {table_def['table_name']} may already exist")
            else:
                print(f"[ERROR] Error creating {table_def['table_name']}: {e}")
                print(f"Response: {e.response.text}")
    
    if created_tables:
        print("\nAdd these to your .env file:")
        for name, table_id in created_tables.items():
            env_var = f"NOCODB_{name.upper()}_TABLE_ID"
            print(f"{env_var}={table_id}")

if __name__ == "__main__":
    main()

