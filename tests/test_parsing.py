import pytest

from src.main import parse_image_data
from src.models import WebhookData, DiunUpdateData


class TestParseImageData:
    """Test the parse_image_data business logic function."""
    
    def test_parse_standard_image_with_tag(self):
        """Test parsing a standard image with explicit tag."""
        webhook_data = WebhookData(
            hostname="testserver",
            status="new",
            provider="docker",
            image="docker.io/nginx:alpine",
            digest="sha256:abcd1234",
            created="2025-01-01T10:00:00Z",
            hub_link="https://hub.docker.com/_/nginx"
        )
        
        result = parse_image_data(webhook_data)
        
        assert isinstance(result, DiunUpdateData)
        assert result.image_name == "docker.io/nginx"
        assert result.image_tag == "alpine"
        assert result.hostname == "testserver"
        assert result.image_created_at == "2025-01-01T10:00:00Z"

    def test_parse_image_without_tag_defaults_to_latest(self):
        """Test that images without explicit tag default to 'latest'."""
        webhook_data = WebhookData(
            hostname="testserver", 
            status="new",
            provider="docker",
            image="nginx",  # No tag specified
            digest="sha256:abcd1234",
            created="2025-01-01T10:00:00Z"
        )
        
        result = parse_image_data(webhook_data)
        
        assert result.image_name == "nginx"
        assert result.image_tag == "latest"

    def test_parse_registry_image_with_version_tag(self):
        """Test parsing registry images with version tags."""
        webhook_data = WebhookData(
            hostname="prodserver",
            status="new", 
            provider="kubernetes",
            image="registry.company.com/myapp:v1.2.3",
            digest="sha256:prod1234",
            created="2025-01-01T10:00:00Z",
            hub_link="https://registry.company.com/myapp"
        )
        
        result = parse_image_data(webhook_data)
        
        assert result.image_name == "registry.company.com/myapp"
        assert result.image_tag == "v1.2.3"
        assert result.provider == "kubernetes"

    def test_parse_image_with_port_in_registry(self):
        """Test parsing images from registries with port numbers."""
        webhook_data = WebhookData(
            hostname="testserver",
            status="new",
            provider="docker", 
            image="localhost:5000/myimage:dev",
            digest="sha256:local123",
            created="2025-01-01T10:00:00Z"
        )
        
        result = parse_image_data(webhook_data)
        
        assert result.image_name == "localhost:5000/myimage"
        assert result.image_tag == "dev"

    def test_parse_image_with_multiple_colons(self):
        """Test parsing images with multiple colons (registry:port/image:tag)."""
        webhook_data = WebhookData(
            hostname="testserver",
            status="new",
            provider="docker",
            image="registry.example.com:443/team/app:v2.1.0",
            digest="sha256:multi123",
            created="2025-01-01T10:00:00Z"
        )
        
        result = parse_image_data(webhook_data)
        
        # Should split on the rightmost colon
        assert result.image_name == "registry.example.com:443/team/app"
        assert result.image_tag == "v2.1.0"

    def test_preserve_all_webhook_fields(self, sample_diun_webhook):
        """Test that all webhook fields are preserved in the result."""
        webhook_data = WebhookData(**sample_diun_webhook)
        
        result = parse_image_data(webhook_data)
        
        # All original fields should be preserved
        assert result.hostname == webhook_data.hostname
        assert result.status == webhook_data.status
        assert result.provider == webhook_data.provider
        assert result.digest == webhook_data.digest
        assert result.image_created_at == webhook_data.created
        assert result.hub_link == webhook_data.hub_link
        
        # Image should be parsed correctly
        assert result.image_name == "docker.io/crazymax/diun"
        assert result.image_tag == "latest"

    def test_parse_with_optional_fields_none(self):
        """Test parsing when optional fields are None."""
        webhook_data = WebhookData(
            hostname="testserver",
            status="new",
            provider="docker",
            image="nginx:alpine", 
            digest="sha256:abcd1234",
            created="2025-01-01T10:00:00Z"
            # hub_link is None (not provided)
        )
        
        result = parse_image_data(webhook_data)
        
        assert result.hub_link is None
        assert result.image_name == "nginx"
        assert result.image_tag == "alpine"

    def test_parse_sha_tag(self):
        """Test parsing images with SHA-based tags.""" 
        webhook_data = WebhookData(
            hostname="testserver",
            status="new",
            provider="docker",
            image="myapp:sha-abc123def",
            digest="sha256:sha123",
            created="2025-01-01T10:00:00Z"
        )
        
        result = parse_image_data(webhook_data)
        
        assert result.image_name == "myapp"
        assert result.image_tag == "sha-abc123def"

    def test_parse_latest_explicit_tag(self):
        """Test parsing images with explicit 'latest' tag."""
        webhook_data = WebhookData(
            hostname="testserver", 
            status="new",
            provider="docker",
            image="ubuntu:latest",
            digest="sha256:ubuntu123",
            created="2025-01-01T10:00:00Z"
        )
        
        result = parse_image_data(webhook_data)
        
        assert result.image_name == "ubuntu"
        assert result.image_tag == "latest"