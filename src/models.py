from pydantic import BaseModel
from typing import Optional

class WebhookData(BaseModel):
    """API input validation model"""
    hostname: str  # Required - server hostname
    status: str    # Required - update status (e.g., "new")
    provider: str  # Required - provider type (e.g., "docker", "file")
    image: str     # Required - full image with tag
    digest: str    # Required - SHA256 digest
    hub_link: Optional[str] = None  # Optional - link to registry

class DiunUpdateData(BaseModel):
    """Database operation model with parsed image data"""
    hostname: str       # Required - server hostname
    status: str         # Required - update status
    provider: str       # Required - provider type
    image_name: str     # Required - parsed image name
    image_tag: str      # Required - parsed tag (defaults to "latest")
    digest: str         # Required - SHA256 digest
    hub_link: Optional[str] = None  # Optional - link to registry