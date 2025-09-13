from pydantic import BaseModel, Field
from typing import Optional

class WebhookData(BaseModel):
    """API input validation model"""
    hostname: str = Field(min_length=1)  # Required - server hostname
    status: str = Field(min_length=1)    # Required - update status (e.g., "new")
    provider: str = Field(min_length=1)  # Required - provider type (e.g., "docker", "file")
    image: str = Field(min_length=1)     # Required - full image with tag
    digest: str = Field(min_length=1)    # Required - SHA256 digest
    created: str = Field(min_length=1)   # Required - ISO 8601 timestamp when image was created
    hub_link: Optional[str] = None  # Optional - link to registry
    # Optional extra fields DIUN might send
    diun_version: Optional[str] = None
    mime_type: Optional[str] = None
    platform: Optional[str] = None
    metadata: Optional[dict] = None

class DiunUpdateData(BaseModel):
    """Database operation model with parsed image data"""
    hostname: str       # Required - server hostname
    status: str         # Required - update status
    provider: str       # Required - provider type
    image_name: str     # Required - parsed image name
    image_tag: str      # Required - parsed tag (defaults to "latest")
    digest: str         # Required - SHA256 digest
    image_created_at: str  # Required - when the image was created
    hub_link: Optional[str] = None  # Optional - link to registry