from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

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

    def to_update_data(self) -> "DiunUpdateData":
        """Parse webhook payload into a DiunUpdateData ready for the database."""
        # Strip digest suffix (e.g. "image:tag@sha256:abc..." -> "image:tag")
        image_full = self.image.split('@')[0]
        image_parts = image_full.rsplit(':', 1)
        image_name = image_parts[0] if len(image_parts) > 1 else image_full
        image_tag = image_parts[1] if len(image_parts) > 1 else "latest"

        try:
            image_created_at = datetime.fromisoformat(self.created.replace('Z', '+00:00')).replace(tzinfo=None)
        except (ValueError, AttributeError):
            image_created_at = None

        return DiunUpdateData(
            hostname=self.hostname,
            status=self.status,
            provider=self.provider,
            image_name=image_name,
            image_tag=image_tag,
            digest=self.digest,
            image_created_at=image_created_at,
            hub_link=self.hub_link,
        )

class DiunUpdateData(BaseModel):
    """Database operation model with parsed image data"""
    hostname: str       # Required - server hostname
    status: str         # Required - update status
    provider: str       # Required - provider type
    image_name: str     # Required - parsed image name
    image_tag: str      # Required - parsed tag (defaults to "latest")
    digest: str         # Required - SHA256 digest
    image_created_at: Optional[datetime] = None  # When the image was created
    hub_link: Optional[str] = None  # Optional - link to registry