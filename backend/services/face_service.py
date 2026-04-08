import httpx
import os
import json

ML_SERVICE_URL = os.environ.get("ML_SERVICE_URL", "https://mas00m-missing-tracker-ml.hf.space")


async def validate_photo(image_bytes: bytes) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/validate-photo",
            files={"file": ("photo.jpg", image_bytes, "image/jpeg")},
        )
        response.raise_for_status()
        return response.json()


async def extract_embedding(image_bytes: bytes) -> list:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/extract-embedding",
            files={"file": ("photo.jpg", image_bytes, "image/jpeg")},
        )
        response.raise_for_status()
        return response.json().get("embedding")


async def compare_faces(image_bytes: bytes, known_embedding: list) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ML_SERVICE_URL}/compare-faces",
            files={"file": ("photo.jpg", image_bytes, "image/jpeg")},
            data={"known_embedding": json.dumps(known_embedding)},
        )
        response.raise_for_status()
        return response.json()
