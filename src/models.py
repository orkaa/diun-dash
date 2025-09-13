from pydantic import BaseModel
from typing import Optional

class WebhookData(BaseModel):
    """API input validation model"""
    hostname: Optional[str] = None
    status: Optional[str] = None  
    provider: Optional[str] = None
    image: str  # Required field - full image with tag
    hub_link: Optional[str] = None
    digest: Optional[str] = None

class DiunUpdateData(BaseModel):
    """Database operation model with parsed image data"""
    hostname: Optional[str] = None
    status: Optional[str] = None
    provider: Optional[str] = None
    image_name: str  # Parsed image name
    image_tag: str   # Parsed tag (defaults to "latest")
    hub_link: Optional[str] = None
    digest: Optional[str] = None