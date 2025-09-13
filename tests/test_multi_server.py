import pytest

from src.database import DiunUpdate


class TestMultiServerScenarios:
    """Test multi-server scenarios as mentioned in README TODOs."""
    
    def test_same_image_different_servers(self, test_client, test_db, set_webhook_token):
        """Test that same image from different servers creates separate records."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Webhook from server1
        server1_webhook = {
            "hostname": "production-server-1",
            "status": "new",
            "provider": "docker",
            "image": "nginx:alpine",
            "digest": "sha256:nginx123",
            "created": "2025-01-01T10:00:00Z",
            "hub_link": "https://hub.docker.com/_/nginx"
        }
        
        response1 = test_client.post(
            "/webhook",
            json=server1_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        assert response1.status_code == 200
        
        # Webhook from server2 - same image
        server2_webhook = {
            "hostname": "production-server-2", 
            "status": "new",
            "provider": "kubernetes",
            "image": "nginx:alpine",
            "digest": "sha256:nginx123",  # Different digest (different build)
            "created": "2025-01-01T11:00:00Z",
            "hub_link": "https://hub.docker.com/_/nginx"
        }
        
        response2 = test_client.post(
            "/webhook", 
            json=server2_webhook,
            headers={"Authorization": "test-webhook-token"}
        )
        assert response2.status_code == 200
        
        # Fixed behavior: two nginx records should exist (one per server)
        nginx_records = db.query(DiunUpdate).filter(DiunUpdate.image_name == "nginx").all()
        
        # Should now have 2 records (one per server)
        assert len(nginx_records) == 2
        
        # Check server1 record
        server1_records = [r for r in nginx_records if r.hostname == "production-server-1"]
        assert len(server1_records) == 1
        assert server1_records[0].digest == "sha256:nginx123"
        assert server1_records[0].provider == "docker"
        
        # Check server2 record  
        server2_records = [r for r in nginx_records if r.hostname == "production-server-2"]
        assert len(server2_records) == 1
        assert server2_records[0].digest == "sha256:nginx123"
        assert server2_records[0].provider == "kubernetes"
        
        db.close()

    def test_different_images_different_servers(self, test_client, test_db, set_webhook_token):
        """Test different images on different servers."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # nginx on server1
        nginx_webhook = {
            "hostname": "web-server",
            "status": "new", 
            "provider": "docker",
            "image": "nginx:stable",
            "digest": "sha256:nginx_stable",
            "created": "2025-01-01T10:00:00Z"
        }
        
        # postgres on server2
        postgres_webhook = {
            "hostname": "database-server",
            "status": "new",
            "provider": "docker", 
            "image": "postgres:14",
            "digest": "sha256:postgres_14",
            "created": "2025-01-01T10:00:00Z"
        }
        
        # redis on server3
        redis_webhook = {
            "hostname": "cache-server", 
            "status": "new",
            "provider": "kubernetes",
            "image": "redis:7-alpine",
            "digest": "sha256:redis_7",
            "created": "2025-01-01T10:00:00Z"
        }
        
        # Send all webhooks
        for webhook in [nginx_webhook, postgres_webhook, redis_webhook]:
            response = test_client.post(
                "/webhook",
                json=webhook,
                headers={"Authorization": "test-webhook-token"}
            )
            assert response.status_code == 200
        
        # Should have 3 records - all different images
        all_records = db.query(DiunUpdate).all()
        assert len(all_records) == 3
        
        # Verify each server has its image
        records_by_hostname = {r.hostname: r for r in all_records}
        
        assert "web-server" in records_by_hostname
        assert records_by_hostname["web-server"].image_name == "nginx"
        
        assert "database-server" in records_by_hostname
        assert records_by_hostname["database-server"].image_name == "postgres"
        
        assert "cache-server" in records_by_hostname  
        assert records_by_hostname["cache-server"].image_name == "redis"
        
        db.close()

    def test_multiple_updates_same_server(self, test_client, test_db, set_webhook_token):
        """Test multiple image updates from the same server."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        server_name = "multi-app-server"
        
        # First image update
        app1_webhook = {
            "hostname": server_name,
            "status": "new",
            "provider": "docker",
            "image": "myapp:v1.0.0", 
            "digest": "sha256:app1_v1",
            "created": "2025-01-01T10:00:00Z"
        }
        
        # Second image update (different app)
        app2_webhook = {
            "hostname": server_name,
            "status": "new",
            "provider": "docker", 
            "image": "myapi:v2.1.0",
            "digest": "sha256:api_v2", 
            "created": "2025-01-01T10:30:00Z"
        }
        
        # Third image update (update to first app)
        app1_updated_webhook = {
            "hostname": server_name,
            "status": "updated",
            "provider": "docker",
            "image": "myapp:v1.1.0",  # Same app, new version
            "digest": "sha256:app1_v1_1",
            "created": "2025-01-01T11:00:00Z"
        }
        
        # Send webhooks
        for webhook in [app1_webhook, app2_webhook, app1_updated_webhook]:
            response = test_client.post(
                "/webhook", 
                json=webhook,
                headers={"Authorization": "test-webhook-token"}
            )
            assert response.status_code == 200
        
        # Should have 2 records: myapi and myapp (latest version)
        server_records = db.query(DiunUpdate).filter(DiunUpdate.hostname == server_name).all()
        assert len(server_records) == 2
        
        records_by_image = {r.image_name: r for r in server_records}
        
        # myapi should be unchanged
        assert "myapi" in records_by_image
        assert records_by_image["myapi"].image_tag == "v2.1.0"
        
        # myapp should be updated to v1.1.0
        assert "myapp" in records_by_image
        assert records_by_image["myapp"].image_tag == "v1.1.0"
        assert records_by_image["myapp"].status == "updated"
        
        db.close()

    def test_server_hostname_variations(self, test_client, test_db, set_webhook_token):
        """Test various hostname formats from different server types."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        webhooks = [
            {
                "hostname": "prod-k8s-node-01.company.com",
                "image": "app:prod", 
                "provider": "kubernetes"
            },
            {
                "hostname": "docker-swarm-manager",
                "image": "worker:latest",
                "provider": "docker"
            },
            {
                "hostname": "bare-metal-server-123", 
                "image": "database:stable",
                "provider": "file"
            },
            {
                "hostname": "ec2-instance-i-abc123",
                "image": "microservice:v1",
                "provider": "docker"
            }
        ]
        
        # Send all webhooks with common required fields
        for i, webhook in enumerate(webhooks):
            webhook.update({
                "status": "new",
                "digest": f"sha256:digest{i}", 
                "created": "2025-01-01T10:00:00Z"
            })
            
            response = test_client.post(
                "/webhook",
                json=webhook, 
                headers={"Authorization": "test-webhook-token"}
            )
            assert response.status_code == 200
        
        # Should have 4 records from different servers
        all_records = db.query(DiunUpdate).all()
        assert len(all_records) == 4
        
        hostnames = {r.hostname for r in all_records}
        expected_hostnames = {
            "prod-k8s-node-01.company.com",
            "docker-swarm-manager", 
            "bare-metal-server-123",
            "ec2-instance-i-abc123"
        }
        assert hostnames == expected_hostnames
        
        db.close()

    def test_future_multi_server_behavior_comment(self, test_client, test_db, set_webhook_token):
        """
        This test documents the current behavior and desired future behavior.
        
        Current: Same image_name from different servers overwrites each other.
        Future TODO: Should track per image per server combination.
        """
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Same image from two different servers
        webhooks = [
            {
                "hostname": "server-east",
                "status": "new",
                "provider": "docker",
                "image": "nginx:latest",
                "digest": "sha256:east_build",
                "created": "2025-01-01T10:00:00Z"
            },
            {
                "hostname": "server-west", 
                "status": "new",
                "provider": "docker",
                "image": "nginx:latest",
                "digest": "sha256:west_build", 
                "created": "2025-01-01T10:05:00Z"
            }
        ]
        
        for webhook in webhooks:
            response = test_client.post(
                "/webhook",
                json=webhook,
                headers={"Authorization": "test-webhook-token"}
            )
            assert response.status_code == 200
        
        nginx_records = db.query(DiunUpdate).filter(DiunUpdate.image_name == "nginx").all()
        
        # FIXED BEHAVIOR: Should now have 2 records, one per server
        assert len(nginx_records) == 2
        
        # Check server-east record
        east_records = [r for r in nginx_records if r.hostname == "server-east"]
        assert len(east_records) == 1
        assert east_records[0].digest == "sha256:east_build"
        
        # Check server-west record
        west_records = [r for r in nginx_records if r.hostname == "server-west"]
        assert len(west_records) == 1
        assert west_records[0].digest == "sha256:west_build"
        
        db.close()