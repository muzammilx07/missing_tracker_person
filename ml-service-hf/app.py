from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import dlib
import numpy as np
import io
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models once at startup/module import
detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
face_rec_model = dlib.face_recognition_model_v1("models/dlib_face_recognition_resnet_model_v1.dat")


def _to_rgb_array(image_bytes: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(image)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/validate-photo")
async def validate_photo(file: UploadFile = File(...)):
    image_bytes = await file.read()
    img = _to_rgb_array(image_bytes)
    dets = detector(img, 1)
    if len(dets) == 0:
        return {"is_person": False, "confidence": 0.0}
    return {"is_person": True, "confidence": 0.99}


@app.post("/extract-embedding")
async def extract_embedding(file: UploadFile = File(...)):
    image_bytes = await file.read()
    img = _to_rgb_array(image_bytes)
    dets = detector(img, 1)
    if len(dets) == 0:
        return {"embedding": None, "success": False}

    shape = shape_predictor(img, dets[0])
    descriptor = face_rec_model.compute_face_descriptor(img, shape)
    return {"embedding": list(descriptor), "success": True}


@app.post("/compare-faces")
async def compare_faces(file: UploadFile = File(...), known_embedding: str = Form(...)):
    image_bytes = await file.read()
    img = _to_rgb_array(image_bytes)
    dets = detector(img, 1)
    if len(dets) == 0:
        return {"match": False, "distance": None, "embedding": None}

    shape = shape_predictor(img, dets[0])
    new_embedding = list(face_rec_model.compute_face_descriptor(img, shape))

    known = json.loads(known_embedding)
    distance = np.linalg.norm(np.array(new_embedding) - np.array(known))
    is_match = bool(distance < 0.6)

    return {
        "match": is_match,
        "distance": round(float(distance), 4),
        "embedding": new_embedding,
    }
