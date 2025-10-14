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

from data import available_objects  # Fallback data
from nocodb_service import get_nocodb_service

load_dotenv()

try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    serp_client = serpapi.Client(api_key=os.environ.get("SERPAPI_KEY"))
except Exception as e:
    print(f"Error initializing API clients: {e}")
    client = None
    serp_client = None
available_object_titles_fallback = [
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


def get_available_object_titles():
    try:
        service = get_nocodb_service()
        if service:
            titles = service.get_object_titles()
            if titles:
                return titles
        return available_object_titles_fallback
    except Exception as e:
        return available_object_titles_fallback


available_object_titles = get_available_object_titles()
firebase_config = {
    "type": "service_account",
    "project_id": os.environ.get("FIREBASE_PROJECT_ID", "travel-app-backend-a9d5f"),
    "private_key_id": "d078b3dcfc465cae4785c5dc877e96c9fab5613d",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCZ8hhM+t481we5\nqhJbtE6urx72KC5hKQwaxRMIPfoweqsxg6Tu2OK3tCSnFYuMTs2eUabePBpfNsI9\nyje8KRmXZ0HZOVkxNafejMYP0gjW5MwTiTaPCBh285yWIjJXg36fFCe1r5Hg7Xz4\n+Emp5XEtEvs7lQoCRAXcw+YfIMzpXgMBfeNyjQSafwpSQNIxFdoDdQP7OWZ02/le\nAAZV/f1AXfm61FWqT5OWr0+yHGYSwQZ2Vn1anoDax46935RjS8AK9FO8dBJdLAyM\nHdRExaKDVI43+uWy32H+seMizsO/4uKoE+dT+YEkTwRv6mUcwWnz5y+x606AUCwR\nCqdue8pDAgMBAAECggEAHOeAuotryL6S+8A7/C3pjBDjXlKDCskbNbeE8Eo6vHl7\nxSszf4kHYHiZXSnFbs2o+63XB+j/BpuQcuuR9Wk+HdhMW83RulSZtUZ3Nac486g3\nzP85WDer6EGrR+EZ1Kai0pmFLy7M1A+jJFfx9M1Yp57lvvUn0O8WrrG1dmjBMJuk\no7lbe5WW83bU7HNjGdMY7deZPtCGFLZilUYXBr8zTOSfFiIjKOatkUOlGKHvGUmS\nRx95fJduFepuqxISaFD/l2wQiHNrK6z3e/1y66+t9fF3sPm9N+mzehj19/P/2JC2\nDolB6wjhWaz9eWnqfz7aPqhx8HcDcTL8tqszDMkEuQKBgQDJ+t/J04CUy4R7EKbK\nUM5CcVgAmJowwhWFv8rGSbQRY7KnRgIjFZrGWF4hFXzWyWNp0nZwdLEFmR83fHtI\naWWUHb+7Q7T8HnMqQRvpEXdfLC6/NJjmOJ73rkZftr1bh+Dl7WstjYREnG5xlki4\nmAbp0Uq3W91G1lGXCy04AJyp9wKBgQDDHmsFRpC4xNn4ur14YfiaMYG/PeLI/VmN\n8V7ftJ0Y0ZT/zhFlTTRS6fNDSSegh2llc7fClTqBst17/F4g8bw7RYcmI9LBTE4B\n9VtGsi4gmsuQ7Ffcsxdhb049b/rb8VgK7vnanpnC3/+MacHhlme1glGPrkRflGPx\nluqG9Z6vFQKBgGgoGyd1DiWtHdBosdo6+WKCGKOWDk1+iKLEWMkQUO92vjZMf+Wf\nyoTmJQRilFIe4Ek94x3yzybX46U1aE3bLCrJfIoRTE+HVFRB5ya1fx1xJ1oqwX5X\nTILlOB07m0KMO4nWeSKwi7jmAn5IxY+LtmT1LNaJZP6WntSJSvRKPH/ZAoGAN/ve\nUSEyHRG+SPOrsYLKxdM2mxyymWC39VYwFpfIC3r2+X6y1xIT1UZzGfc/e3ve7dEK\nBLa0lsovaoe6qlEx5P/KC1N0ASpXp5AypFIzkf9YMTje7OAl8TryhAZBQCI7VMfE\nwMmI7LVAqZUeoA97qkS+Ci/CRnpZQtQ+boLDCRECgYA4F2gXYkGSJO5Z5dpZajs/\nZ98afTFXESC096OIyZfJJnzLBmxtwiLTu99q16/iuy7T76K/7lTqF/MdwMDrNNSQ\nNA7Niwt8TqgLhpYusWyFFNumUlNci9gYbUCAyi+30pQmWgOB5JXldGxMtUmY0Qpe\nxEJqRfOu2ob+pGf7WgFOIg==\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@travel-app-backend-a9d5f.iam.gserviceaccount.com",
    "client_id": "109334951653923558638",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40travel-app-backend-a9d5f.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

cred = credentials.Certificate(firebase_config)

firebase_app = firebase_admin.initialize_app(
    cred, {"storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "travel-app-backend-a9d5f.appspot.com")}
)

bucket = storage.bucket()


def upload_file(file: Any) -> str:
    try:
        file_id = str(uuid.uuid4()) + path.splitext(file.filename)[1]
        blob = bucket.blob(file_id)
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()
        return blob.public_url
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
        url = image_to_url(image_file)
        if not url:
            url = upload_file(image_file)
            if not url:
                return "Không thể upload hình ảnh"

        google_len_result = get_google_len_result(url)
        if not google_len_result:
            return "Không tìm thấy thông tin về hiện vật từ Google Lens"

        google_len_titles = [x.get("title", "") for x in google_len_result if x.get("title")]

        name = openai_get_object_name(google_len_titles)
        available_name = openai_get_available_object_name(name)

        if available_name == "None":
            return name
        else:
            return available_name

    except Exception as e:
        print(f"Error in get_object_name: {e}")
        return "Lỗi khi xử lý hình ảnh"


def get_full_description(name: str):
    try:
        service = get_nocodb_service()
        if service:
            nocodb_obj = service.get_object_by_title(name)
            if nocodb_obj and nocodb_obj.get("content"):
                return nocodb_obj["content"]

        if name in available_object_titles_fallback:
            for obj in available_objects:
                if obj["title"] == name:
                    return obj["content"]

        return openai_get_full_description(name)

    except Exception as e:
        print(f"Error getting description for '{name}': {e}")
        return openai_get_full_description(name)
