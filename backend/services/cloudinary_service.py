"""
Cloudinary photo upload service.
Handles uploading photos for missing persons and sightings.
"""

import cloudinary
import cloudinary.uploader
from config import settings


def upload_photo(file_bytes: bytes, folder: str, filename: str) -> str:
    """
    Upload photo bytes to Cloudinary.
    
    Args:
        file_bytes: Image file content as bytes
        folder: Cloudinary folder path (e.g., "missing_persons", "sightings")
        filename: Original filename (used in Cloudinary)
    
    Returns:
        secure_url: Public secure URL of uploaded image
    
    Raises:
        Exception: If Cloudinary credentials not configured or upload fails
    """
    
    # Configure Cloudinary
    if not settings.CLOUDINARY_CLOUD_NAME:
        raise CloudinaryConfigError("CLOUDINARY_CLOUD_NAME not configured")
    if not settings.CLOUDINARY_API_KEY:
        raise CloudinaryConfigError("CLOUDINARY_API_KEY not configured")
    if not settings.CLOUDINARY_API_SECRET:
        raise CloudinaryConfigError("CLOUDINARY_API_SECRET not configured")
    
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET
    )
    
    try:
        # Upload file
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=f"missing-tracker/{folder}",
            public_id=filename.split('.')[0],  # Remove extension
            resource_type="auto",
            overwrite=True,
            quality="auto"
        )
        
        return result["secure_url"]
    
    except Exception as e:
        raise CloudinaryUploadError(f"Cloudinary upload failed: {str(e)}")


class CloudinaryConfigError(Exception):
    """Raised when Cloudinary is not properly configured."""
    pass


class CloudinaryUploadError(Exception):
    """Raised when Cloudinary upload fails."""
    pass
