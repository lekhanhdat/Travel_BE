import uuid
from os import path

import firebase_admin
from fastapi import UploadFile
from firebase_admin import credentials, storage

cred = credentials.Certificate("./privateKey.json")

app = firebase_admin.initialize_app(cred, {"storageBucket": "test-ae08e.appspot.com"})

bucket = storage.bucket()


class FileUploadService:
    def upload(self, file: UploadFile):
        file_id = str(uuid.uuid4()) + path.splitext(file.filename)[1]
        blob = bucket.blob(file_id)

        # blob.upload_from_string(content, content_type=file.content_type)
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()

        return blob.public_url
