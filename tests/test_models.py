import pytest
from pydantic import ValidationError

from src.models import WebhookData, DiunUpdateData


class TestWebhookData:
    """Test WebhookData model validation."""
    
    def test_valid_webhook_data(self, sample_diun_webhook):
        """Test that valid DIUN webhook data is accepted."""
        webhook_data = WebhookData(**sample_diun_webhook)
        
        assert webhook_data.hostname == "myserver"
        assert webhook_data.status == "new"
        assert webhook_data.provider == "file"
        assert webhook_data.image == "docker.io/crazymax/diun:latest"
        assert webhook_data.digest == "sha256:216e3ae7de4ca8b553eb11ef7abda00651e79e537e85c46108284e5e91673e01"
        assert webhook_data.created == "2020-03-26T12:23:56Z"
        assert webhook_data.hub_link == "https://hub.docker.com/r/crazymax/diun"
        assert webhook_data.diun_version == "4.24.0"
        assert webhook_data.mime_type == "application/vnd.docker.distribution.manifest.list.v2+json"
        assert webhook_data.platform == "linux/amd64"
        assert webhook_data.metadata is not None

    def test_minimal_webhook_data(self):
        """Test webhook data with only required fields."""
        minimal_data = {
            "hostname": "testserver",
            "status": "new", 
            "provider": "docker",
            "image": "nginx:alpine",
            "digest": "sha256:abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
            "created": "2025-01-01T10:00:00Z"
        }
        
        webhook_data = WebhookData(**minimal_data)
        
        assert webhook_data.hostname == "testserver"
        assert webhook_data.hub_link is None
        assert webhook_data.diun_version is None
        assert webhook_data.metadata is None

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        incomplete_data = {
            "hostname": "testserver",
            "status": "new"
            # Missing provider, image, digest, created
        }
        
        with pytest.raises(ValidationError) as exc_info:
            WebhookData(**incomplete_data)
        
        error_fields = {error["loc"][0] for error in exc_info.value.errors()}
        expected_missing = {"provider", "image", "digest", "created"}
        assert expected_missing.issubset(error_fields)

    def test_empty_required_fields(self):
        """Test that empty strings in required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            WebhookData(
                hostname="",  # Empty hostname should fail
                status="new",
                provider="docker", 
                image="nginx:latest",
                digest="sha256:abc123",
                created="2025-01-01T10:00:00Z"
            )
        
        with pytest.raises(ValidationError):
            WebhookData(
                hostname="testserver",
                status="",  # Empty status should fail
                provider="docker",
                image="nginx:latest",
                digest="sha256:abc123", 
                created="2025-01-01T10:00:00Z"
            )


class TestDiunUpdateData:
    """Test DiunUpdateData model validation."""
    
    def test_valid_update_data(self):
        """Test that valid update data is accepted."""
        update_data = DiunUpdateData(
            hostname="myserver",
            status="new",
            provider="file",
            image_name="docker.io/crazymax/diun", 
            image_tag="latest",
            digest="sha256:216e3ae7de4ca8b553eb11ef7abda00651e79e537e85c46108284e5e91673e01",
            image_created_at="2020-03-26T12:23:56Z",
            hub_link="https://hub.docker.com/r/crazymax/diun"
        )
        
        assert update_data.hostname == "myserver"
        assert update_data.image_name == "docker.io/crazymax/diun"
        assert update_data.image_tag == "latest"
        assert update_data.image_created_at == "2020-03-26T12:23:56Z"

    def test_minimal_update_data(self):
        """Test update data with only required fields."""
        update_data = DiunUpdateData(
            hostname="testserver",
            status="new",
            provider="docker",
            image_name="nginx",
            image_tag="alpine", 
            digest="sha256:abcd1234",
            image_created_at="2025-01-01T10:00:00Z"
        )
        
        assert update_data.hub_link is None

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            DiunUpdateData(
                hostname="testserver",
                status="new"
                # Missing other required fields
            )
        
        error_fields = {error["loc"][0] for error in exc_info.value.errors()}
        expected_missing = {"provider", "image_name", "image_tag", "digest", "image_created_at"}
        assert expected_missing.issubset(error_fields)