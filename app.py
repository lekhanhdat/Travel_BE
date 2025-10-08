from fastapi import FastAPI, UploadFile

# from service import get_full_description, get_object_name
from service import get_full_description, get_object_name

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/detect")
def detect(image_file: UploadFile):
    name = get_object_name(image_file)
    full_description = get_full_description(name)

    # return full_description
    return {
        "name": name,
        "description": full_description,
    }

@app.post('/detect/test')
def test_detect(image_file: UploadFile):
    return {"name": "test", "description": "# test description"}
