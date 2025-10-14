import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class NocoDBService:
    def __init__(self):
        self.base_url = os.environ.get("NOCODB_BASE_URL", "https://app.nocodb.com")
        self.api_token = os.environ.get("NOCODB_API_TOKEN")
        self.table_id = os.environ.get("NOCODB_TABLE_ID", "mj77cy6909ll2wc")
        
        if not self.api_token:
            raise ValueError("NOCODB_API_TOKEN is required in environment variables")
        
        self.headers = {
            "xc-token": self.api_token,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[Any, Any]:
        url = f"{self.base_url}/api/v2/tables/{self.table_id}/records"
        if endpoint:
            url += f"/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"NocoDB API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            raise
    
    def get_all_objects(self) -> List[Dict[str, Any]]:
        try:
            response = self._make_request("GET", "")
            return response.get("list", [])
        except Exception as e:
            print(f"Error fetching objects from NocoDB: {e}")
            return []
    
    def get_object_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/api/v2/tables/{self.table_id}/records"
            params = {
                "where": f"(title,eq,{title})"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            objects = data.get("list", [])
            return objects[0] if objects else None
        
        except Exception as e:
            print(f"Error fetching object by title from NocoDB: {e}")
            return None
    
    def create_object(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        try:
            data = {
                "title": title,
                "content": content
            }
            
            response = self._make_request("POST", "", data)
            return response
        
        except Exception as e:
            print(f"Error creating object in NocoDB: {e}")
            return None
    
    def update_object(self, record_id: str, title: str = None, content: str = None) -> Optional[Dict[str, Any]]:
        try:
            data = {}
            if title is not None:
                data["title"] = title
            if content is not None:
                data["content"] = content
            
            if not data:
                print("No data to update")
                return None
            
            response = self._make_request("PUT", record_id, data)
            return response
        
        except Exception as e:
            print(f"Error updating object in NocoDB: {e}")
            return None
    
    def delete_object(self, record_id: str) -> bool:
        try:
            self._make_request("DELETE", record_id)
            return True
        
        except Exception as e:
            print(f"Error deleting object from NocoDB: {e}")
            return False
    
    def get_object_titles(self) -> List[str]:
        try:
            objects = self.get_all_objects()
            return [obj.get("title", "") for obj in objects if obj.get("title")]
        except Exception as e:
            print(f"Error fetching object titles from NocoDB: {e}")
            return []


nocodb_service = None

def get_nocodb_service() -> NocoDBService:
    global nocodb_service
    if nocodb_service is None:
        try:
            nocodb_service = NocoDBService()
        except Exception as e:
            print(f"Failed to initialize NocoDB service: {e}")
            nocodb_service = None
    return nocodb_service
