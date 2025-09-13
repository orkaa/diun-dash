import pytest
from fastapi.testclient import TestClient

from src.database import DiunUpdate


class TestWebhookWorkflow:
    """Test complete webhook workflow including authentication."""
    
    def test_successful_webhook_flow(self, test_client, set_webhook_token, sample_diun_webhook):
        """Test complete successful webhook processing."""
        token = "test-webhook-token"
        
        response = test_client.post(
            "/webhook",
            json=sample_diun_webhook,
            headers={"Authorization": token}
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Webhook received"}

    def test_webhook_unauthorized_missing_header(self, test_client, set_webhook_token, sample_diun_webhook):
        """Test webhook rejection when Authorization header is missing."""
        response = test_client.post(
            "/webhook", 
            json=sample_diun_webhook
            # No Authorization header
        )
        
        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    def test_webhook_unauthorized_wrong_token(self, test_client, set_webhook_token, sample_diun_webhook):
        """Test webhook rejection with wrong token."""
        response = test_client.post(
            "/webhook",
            json=sample_diun_webhook, 
            headers={"Authorization": "wrong-token"}
        )
        
        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    def test_webhook_data_validation_error(self, test_client, set_webhook_token):
        """Test webhook rejection with invalid data."""
        invalid_data = {
            "hostname": "testserver",
            "status": "new"
            # Missing required fields: provider, image, digest, created
        }
        
        response = test_client.post(
            "/webhook",
            json=invalid_data,
            headers={"Authorization": "test-webhook-token"}
        )
        
        assert response.status_code == 400
        assert "Invalid webhook data" in response.json()["detail"]

    def test_webhook_data_stored_correctly(self, test_client, test_db, set_webhook_token, sample_diun_webhook):
        """Test that webhook data is stored correctly in database."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Ensure database is empty initially
        initial_count = db.query(DiunUpdate).count()
        assert initial_count == 0
        
        # Send webhook
        response = test_client.post(
            "/webhook",
            json=sample_diun_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        
        assert response.status_code == 200
        
        # Check data was stored
        stored_records = db.query(DiunUpdate).all()
        assert len(stored_records) == 1
        
        record = stored_records[0]
        assert record.hostname == "myserver"
        assert record.status == "new"
        assert record.provider == "file"
        assert record.image_name == "docker.io/crazymax/diun"
        assert record.image_tag == "latest" 
        assert record.digest == "sha256:216e3ae7de4ca8b553eb11ef7abda00651e79e537e85c46108284e5e91673e01"
        assert record.image_created_at == "2020-03-26T12:23:56Z"
        assert record.hub_link == "https://hub.docker.com/r/crazymax/diun"
        assert record.created_at is not None  # Auto-generated
        
        db.close()

    def test_webhook_minimal_data(self, test_client, test_db, set_webhook_token):
        """Test webhook with minimal required data."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        minimal_webhook = {
            "hostname": "minimal-server",
            "status": "new",
            "provider": "docker", 
            "image": "nginx:alpine",
            "digest": "sha256:minimal123",
            "created": "2025-01-01T10:00:00Z"
            # No optional fields
        }
        
        response = test_client.post(
            "/webhook",
            json=minimal_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        
        assert response.status_code == 200
        
        # Check data was stored
        records = db.query(DiunUpdate).all()
        assert len(records) == 1
        
        record = records[0]
        assert record.hostname == "minimal-server"
        assert record.image_name == "nginx"
        assert record.image_tag == "alpine"
        assert record.hub_link is None  # Optional field not provided
        
        db.close()

    def test_webhook_replaces_existing_record_same_server(self, test_client, test_db, set_webhook_token):
        """Test that new webhook replaces existing record for same hostname and image."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Send first webhook
        first_webhook = {
            "hostname": "server1",
            "status": "new",
            "provider": "docker",
            "image": "nginx:alpine",
            "digest": "sha256:first123", 
            "created": "2025-01-01T10:00:00Z"
        }
        
        response1 = test_client.post(
            "/webhook",
            json=first_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        assert response1.status_code == 200
        
        # Send second webhook for same hostname and image - should replace
        second_webhook = {
            "hostname": "server1",  # Same hostname
            "status": "updated", 
            "provider": "kubernetes",
            "image": "nginx:latest", # Same image_name, different tag
            "digest": "sha256:second456",
            "created": "2025-01-01T11:00:00Z"
        }
        
        response2 = test_client.post(
            "/webhook", 
            json=second_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        assert response2.status_code == 200
        
        # Should have only one nginx record for server1 (the latest)
        server1_nginx_records = db.query(DiunUpdate).filter(
            DiunUpdate.hostname == "server1",
            DiunUpdate.image_name == "nginx"
        ).all()
        assert len(server1_nginx_records) == 1
        
        record = server1_nginx_records[0]
        assert record.hostname == "server1"  # Same server
        assert record.image_tag == "latest"
        assert record.digest == "sha256:second456"
        
        db.close()

    def test_webhook_different_servers_same_image_coexist(self, test_client, test_db, set_webhook_token):
        """Test that different servers can have the same image."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Send webhook for server1
        first_webhook = {
            "hostname": "server1",
            "status": "new",
            "provider": "docker",
            "image": "nginx:alpine",
            "digest": "sha256:server1_digest", 
            "created": "2025-01-01T10:00:00Z"
        }
        
        response1 = test_client.post(
            "/webhook",
            json=first_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        assert response1.status_code == 200
        
        # Send webhook for server2 with same image - should coexist
        second_webhook = {
            "hostname": "server2",  # Different hostname
            "status": "updated", 
            "provider": "kubernetes",
            "image": "nginx:latest", # Same image_name, different tag
            "digest": "sha256:server2_digest",
            "created": "2025-01-01T11:00:00Z"
        }
        
        response2 = test_client.post(
            "/webhook", 
            json=second_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        assert response2.status_code == 200
        
        # Should have both nginx records (one per server)
        all_nginx_records = db.query(DiunUpdate).filter(DiunUpdate.image_name == "nginx").all()
        assert len(all_nginx_records) == 2
        
        # Check server1 record
        server1_records = [r for r in all_nginx_records if r.hostname == "server1"]
        assert len(server1_records) == 1
        assert server1_records[0].digest == "sha256:server1_digest"
        assert server1_records[0].image_tag == "alpine"
        
        # Check server2 record  
        server2_records = [r for r in all_nginx_records if r.hostname == "server2"]
        assert len(server2_records) == 1
        assert server2_records[0].digest == "sha256:server2_digest"
        assert server2_records[0].image_tag == "latest"
        
        db.close()

    def test_webhook_different_images_coexist(self, test_client, test_db, set_webhook_token):
        """Test that webhooks for different images can coexist."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Send webhook for nginx
        nginx_webhook = {
            "hostname": "server1",
            "status": "new",
            "provider": "docker",
            "image": "nginx:alpine",
            "digest": "sha256:nginx123",
            "created": "2025-01-01T10:00:00Z"
        }
        
        response1 = test_client.post(
            "/webhook",
            json=nginx_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        assert response1.status_code == 200
        
        # Send webhook for postgres
        postgres_webhook = {
            "hostname": "server1",
            "status": "new", 
            "provider": "docker",
            "image": "postgres:13",
            "digest": "sha256:postgres456",
            "created": "2025-01-01T10:00:00Z"
        }
        
        response2 = test_client.post(
            "/webhook",
            json=postgres_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        assert response2.status_code == 200
        
        # Should have both records
        all_records = db.query(DiunUpdate).all()
        assert len(all_records) == 2
        
        image_names = {record.image_name for record in all_records}
        assert image_names == {"nginx", "postgres"}
        
        db.close()

    def test_webhook_content_type_missing(self, test_client, set_webhook_token):
        """Test webhook without Content-Type header."""
        response = test_client.post(
            "/webhook",
            json={"invalid": "data"},  # Valid JSON but invalid webhook data  
            headers={"Authorization": "test-webhook-token"}
            # No Content-Type header
        )
        
        # Should still process but fail validation
        assert response.status_code == 400
        assert "Invalid webhook data" in response.json()["detail"]