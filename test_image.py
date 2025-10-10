#!/usr/bin/env python3
"""
Test script với file ảnh thật
"""

import requests
import json

# URL của bạn trên Digital Ocean
BASE_URL = "https://digital-ocean-fast-api-h9zys.ondigitalocean.app"

# File ảnh của bạn
IMAGE_PATH = "Dai-tho-tra-kieu-bao-tang-dieu-khac-cham-danang-fantasticity-com-1.jpg"

def test_with_image():
    print("🚀 Testing backend với file ảnh thật")
    print(f"URL: {BASE_URL}")
    print(f"Image: {IMAGE_PATH}")
    print("-" * 50)
    
    try:
        # Test 1: Root endpoint
        print("1. Testing GET /")
        response = requests.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 2: Detect với ảnh thật
        print(f"\n2. Testing POST /detect with {IMAGE_PATH}")
        with open(IMAGE_PATH, 'rb') as f:
            files = {'image_file': f}
            response = requests.post(f"{BASE_URL}/detect", files=files)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Success!")
            print(f"   Name: {result.get('name', 'N/A')}")
            print(f"   Description: {result.get('description', 'N/A')[:1000]}...")
        else:
            print(f"   ❌ Error: {response.text}")
        
        # Test 3: Test endpoint
        print(f"\n3. Testing POST /detect/test")
        with open(IMAGE_PATH, 'rb') as f:
            files = {'image_file': f}
            response = requests.post(f"{BASE_URL}/detect/test", files=files)
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
    except FileNotFoundError:
        print(f"❌ File ảnh không tìm thấy: {IMAGE_PATH}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    test_with_image()
