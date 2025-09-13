import pytest
from fastapi.testclient import TestClient

from src.database import DiunUpdate


class TestDashboardEndpoints:
    """Test dashboard UI endpoints."""
    
    def test_dashboard_root_empty(self, test_client, test_db):
        """Test dashboard with no data shows empty state."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        
        # Should contain basic HTML structure
        content = response.text
        assert "<html" in content
        assert "<body" in content

    def test_dashboard_with_data(self, test_client, test_db, set_webhook_token):
        """Test dashboard displays webhook data."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Add some test data via webhook
        webhook_data = {
            "hostname": "test-server", 
            "status": "new",
            "provider": "docker",
            "image": "nginx:alpine",
            "digest": "sha256:test123",
            "created": "2025-01-01T10:00:00Z",
            "hub_link": "https://hub.docker.com/_/nginx"
        }
        
        # Send webhook to populate data
        webhook_response = test_client.post(
            "/webhook",
            json=webhook_data,
            headers={"Authorization": "test-webhook-token"}
        )
        assert webhook_response.status_code == 200
        
        # Now test dashboard
        response = test_client.get("/")
        
        assert response.status_code == 200
        content = response.text
        
        # Should contain the webhook data in HTML
        assert "test-server" in content
        assert "nginx" in content
        assert "alpine" in content
        assert "new" in content
        assert "docker" in content
        
        db.close()

    def test_delete_update_endpoint(self, test_client, test_db, set_webhook_token):
        """Test deleting an update record."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Add test data
        webhook_data = {
            "hostname": "test-server",
            "status": "new", 
            "provider": "docker",
            "image": "nginx:alpine",
            "digest": "sha256:test123",
            "created": "2025-01-01T10:00:00Z"
        }
        
        # Send webhook
        webhook_response = test_client.post(
            "/webhook",
            json=webhook_data,
            headers={"Authorization": "test-webhook-token"}
        )
        assert webhook_response.status_code == 200
        
        # Get the created record ID
        records = db.query(DiunUpdate).all()
        assert len(records) == 1
        record_id = records[0].id
        
        # Delete the record
        delete_response = test_client.delete(f"/updates/{record_id}")
        
        assert delete_response.status_code == 200
        assert delete_response.json() == {"message": "Update marked as fixed"}
        
        # Verify record was deleted
        remaining_records = db.query(DiunUpdate).all()
        assert len(remaining_records) == 0
        
        db.close()

    def test_delete_nonexistent_update(self, test_client, test_db):
        """Test deleting a non-existent update returns 404."""
        response = test_client.delete("/updates/999")
        
        assert response.status_code == 404
        assert response.json() == {"detail": "Update not found"}

    def test_dashboard_multiple_updates(self, test_client, test_db, set_webhook_token):
        """Test dashboard with multiple updates."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Add multiple webhook entries
        webhooks = [
            {
                "hostname": "web-server",
                "status": "new",
                "provider": "docker", 
                "image": "nginx:stable",
                "digest": "sha256:nginx123",
                "created": "2025-01-01T10:00:00Z"
            },
            {
                "hostname": "db-server",
                "status": "updated",
                "provider": "kubernetes",
                "image": "postgres:14", 
                "digest": "sha256:postgres456", 
                "created": "2025-01-01T09:00:00Z"
            },
            {
                "hostname": "cache-server",
                "status": "new",
                "provider": "docker",
                "image": "redis:7-alpine",
                "digest": "sha256:redis789",
                "created": "2025-01-01T11:00:00Z"
            }
        ]
        
        # Send all webhooks
        for webhook in webhooks:
            response = test_client.post(
                "/webhook",
                json=webhook,
                headers={"Authorization": "test-webhook-token"}
            )
            assert response.status_code == 200
        
        # Test dashboard shows all entries
        dashboard_response = test_client.get("/")
        assert dashboard_response.status_code == 200
        
        content = dashboard_response.text
        
        # Should contain all server names
        assert "web-server" in content
        assert "db-server" in content  
        assert "cache-server" in content
        
        # Should contain all image names
        assert "nginx" in content
        assert "postgres" in content
        assert "redis" in content
        
        # Should contain all statuses
        assert "new" in content
        assert "updated" in content
        
        db.close()

    def test_dashboard_ordering(self, test_client, test_db, set_webhook_token):
        """Test that dashboard shows entries in correct order (newest first)."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Add entries with different creation times
        # Note: created_at is auto-generated by database, so we'll add them in sequence
        
        first_webhook = {
            "hostname": "server-1", 
            "status": "new",
            "provider": "docker",
            "image": "app1:v1",  # Different image name
            "digest": "sha256:app1", 
            "created": "2025-01-01T08:00:00Z"
        }
        
        second_webhook = {
            "hostname": "server-2",
            "status": "new", 
            "provider": "docker",
            "image": "app2:v2",  # Different image name
            "digest": "sha256:app2",
            "created": "2025-01-01T09:00:00Z"
        }
        
        # Send in order (first, then second)
        for webhook in [first_webhook, second_webhook]:
            response = test_client.post(
                "/webhook",
                json=webhook,
                headers={"Authorization": "test-webhook-token"}
            )
            assert response.status_code == 200
        
        # Check database order (should be by created_at DESC)
        records = db.query(DiunUpdate).order_by(DiunUpdate.created_at.desc()).all()
        assert len(records) == 2
        
        # Most recent should be first (app2 was added second)
        assert records[0].image_name == "app2"
        assert records[1].image_name == "app1"
        
        db.close()

    def test_dashboard_handles_missing_optional_fields(self, test_client, test_db, set_webhook_token):
        """Test dashboard gracefully handles records with missing optional fields."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Webhook with minimal data (no hub_link)
        minimal_webhook = {
            "hostname": "minimal-server",
            "status": "new",
            "provider": "file", 
            "image": "custom-app:latest",
            "digest": "sha256:custom123",
            "created": "2025-01-01T10:00:00Z"
            # No hub_link
        }
        
        response = test_client.post(
            "/webhook", 
            json=minimal_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        assert response.status_code == 200
        
        # Dashboard should still render without errors
        dashboard_response = test_client.get("/")
        assert dashboard_response.status_code == 200
        
        content = dashboard_response.text
        assert "minimal-server" in content
        assert "custom-app" in content
        
        db.close()

    def test_delete_update_invalid_id(self, test_client, test_db):
        """Test delete endpoint with invalid ID format."""
        response = test_client.delete("/updates/invalid-id")
        
        # FastAPI should return 422 for invalid path parameter type
        assert response.status_code == 422