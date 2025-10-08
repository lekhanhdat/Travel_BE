import base64
import os
import uuid
from os import path
from typing import Any

import firebase_admin
import requests
import serpapi
from dotenv import load_dotenv
from fastapi import UploadFile
from firebase_admin import credentials, storage
from openai import OpenAI

from data import available_objects

load_dotenv()

# Khởi tạo clients với error handling
try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    serp_client = serpapi.Client(api_key=os.environ.get("SERPAPI_KEY"))
except Exception as e:
    print(f"Error initializing API clients: {e}")
    client = None
    serp_client = None

available_object_titles = [
    "Đài thờ Trà Kiệu",
    "Đản sinh Brahma",
    "Phù điêu Apsara (Trà Kiệu)",
    "Tượng Phật Quan Âm 67m tại chùa Linh Ứng",
    "Tượng thần Shiva",
    "Lồng đèn Hội An",
    "Nón lá",
    "Vòng đá mỹ nghệ Non Nước",
    "Bánh khô mè Cẩm Lệ",
]


cred = credentials.Certificate("./privateKey.json")

firebase_app = firebase_admin.initialize_app(
    cred, {"storageBucket": "travel-app-backend-a9d5f.appspot.com"}
)

bucket = storage.bucket()


def upload_file(file: Any) -> str:
    try:
        print("Firebase: Initializing upload...")
        file_id = str(uuid.uuid4()) + path.splitext(file.filename)[1]
        blob = bucket.blob(file_id)
        print(f"Firebase: Created blob with ID: {file_id}")

        # blob.upload_from_string(content, content_type=file.content_type)
        blob.upload_from_file(file.file, content_type=file.content_type)
        print("Firebase: File uploaded successfully")
        
        blob.make_public()
        print("Firebase: File made public")
        
        url = blob.public_url
        print(f"Firebase: Public URL: {url}")
        return url
        
    except Exception as e:
        print(f"Firebase upload error: {e}")
        import traceback
        traceback.print_exc()
        return ""


def get_prompt_available_object_name(title: str):
    return f"""
\"\"\"
{", ".join(available_object_titles)}
\"\"\"

There are list of array of available objects in data. Check if the query is in the list and return correct title. Otherwise, return None

Query: {title}

Output:
"""


def get_prompt_name(titles: list[str]):
    return f"""
\"\"\"
{", ".join(titles)}
\"\"\"

There are article titles searched by google about a historical objects. Extract these and return one historical name. The name is in Vietnamese.

Output:
"""


def get_google_len_result(url: str) -> list[dict]:
    if not serp_client:
        print("SerpAPI client not initialized")
        return []
    
    try:
        params = {"engine": "google_lens", "url": url, "hl": "vi", "country": "vn"}
        s = serp_client.search(params=params)
        result = s.get("visual_matches", [])
        return result
    except Exception as e:
        print(f"Error calling SerpAPI: {e}")
        return []


def openai_get_object_name(titles: list[str]) -> str:
    if not client:
        print("OpenAI client not initialized")
        return "Unknown object"
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": get_prompt_name(titles)}],
            temperature=0.0,
        )
        return str(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return "Unknown object"


def openai_get_object_name_image(url: str) -> str:
    prompt = f"""
Image: {url}
Given an image of a historical object, extract the name of the object in Vietnamese.

Output:
    """
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return str(completion.choices[0].message.content)


def openai_get_available_object_name(title: str) -> str:
    if not client:
        print("OpenAI client not initialized")
        return "None"
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": get_prompt_available_object_name(title)}],
            temperature=0.0,
        )
        return str(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return "None"


def openai_get_full_description(title: str) -> str:
    if not client:
        print("OpenAI client not initialized")
        return f"# {title}\n\nKhông thể tạo mô tả do lỗi API."
    
    try:
        prompt = f"""
Tên hiện vật: {title}
Hãy viết một mô tả ngắn cho hiện vật với tên được cung cấp. Output ở dạng markdown
        """
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return str(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return f"# {title}\n\nKhông thể tạo mô tả do lỗi API."


def image_to_url(image_file: UploadFile) -> str:
    # image to url using imgbb api
    imgbb_api_key = os.environ.get("IMGBB_API_KEY")
    if not imgbb_api_key:
        print("IMGBB_API_KEY not found")
        return ""
    
    try:
        url = f"https://api.imgbb.com/1/upload?expiration=600&key={imgbb_api_key}"

        image = image_file.file.read()
        base64_image = base64.b64encode(image).decode("utf-8")

        payload = {"image": base64_image}

        response = requests.post(url, data=payload)
        response_data = response.json()

        return response_data["data"]["url"]
    except Exception as e:
        print(f"Error uploading to ImgBB: {e}")
        return ""


def get_object_name(image_file: UploadFile) -> Any:
    try:
        print("=== Starting image processing ===")
        
        # Upload image to ImgBB (thay vì Firebase)
        print("Step 1: Uploading to ImgBB...")
        url = image_to_url(image_file)
        if not url:
            print("❌ ImgBB upload failed, trying Firebase...")
            url = upload_file(image_file)
            if not url:
                print("❌ Both ImgBB and Firebase upload failed")
                return "Không thể upload hình ảnh"
        
        print("✅ Image upload successful:", url)

        # Get Google Lens results
        print("Step 2: Calling Google Lens API...")
        google_len_result = get_google_len_result(url)
        if not google_len_result:
            print("❌ Google Lens API failed or no results")
            return "Không tìm thấy thông tin về hiện vật từ Google Lens"
        
        google_len_titles = [x.get("title", "") for x in google_len_result if x.get("title")]
        print("✅ Google Lens results:", google_len_titles)

        # Get object name from OpenAI
        print("Step 3: Calling OpenAI for object name...")
        name = openai_get_object_name(google_len_titles)
        print("✅ OpenAI detected name:", name)
        
        # Check if it's in our database
        print("Step 4: Checking against database...")
        available_name = openai_get_available_object_name(name)
        print("✅ Database check result:", available_name)

        if available_name == "None":
            return name
        else:
            return available_name
            
    except Exception as e:
        print(f"❌ Error in get_object_name: {e}")
        import traceback
        traceback.print_exc()
        return "Lỗi khi xử lý hình ảnh"


def get_full_description(name: str):
    if name in available_object_titles:
        # find object in data
        for obj in available_objects:
            if obj["title"] == name:
                return obj["content"]
    else:
        return openai_get_full_description(name)


# image_file = request.files["image_file"]
# name = get_object_name()
# full_description = get_full_description(name)
#
# response = {
#     "name": name,
#     "description": full_description,
# }
# return response
