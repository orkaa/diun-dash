import pytest
from sqlalchemy.orm import Session

from src.database import upsert_diun_update, delete_diun_update, DiunUpdate
from src.models import DiunUpdateData


class TestUpsertDiunUpdate:
    """Test the upsert_diun_update database function."""
    
    def test_insert_new_update(self, test_db):
        """Test inserting a new update record."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        update_data = DiunUpdateData(
            hostname="testserver",
            status="new",
            provider="docker",
            image_name="nginx",
            image_tag="alpine",
            digest="sha256:abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234",
            image_created_at="2025-01-01T10:00:00Z",
            hub_link="https://hub.docker.com/_/nginx"
        )
        
        result = upsert_diun_update(db, update_data)
        
        assert result.id is not None
        assert result.hostname == "testserver"
        assert result.status == "new"
        assert result.provider == "docker"
        assert result.image_name == "nginx"
        assert result.image_tag == "alpine"
        assert result.digest == "sha256:abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234"
        assert result.image_created_at == "2025-01-01T10:00:00Z"
        assert result.hub_link == "https://hub.docker.com/_/nginx"
        assert result.created_at is not None  # Auto-generated timestamp
        
        db.close()

    def test_upsert_replaces_existing_same_server(self, test_db):
        """Test that upsert replaces existing records for same hostname and image."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Insert first record
        update_data1 = DiunUpdateData(
            hostname="server1",
            status="new",
            provider="docker",
            image_name="nginx",
            image_tag="alpine", 
            digest="sha256:old_digest",
            image_created_at="2025-01-01T10:00:00Z"
        )
        result1 = upsert_diun_update(db, update_data1)
        first_id = result1.id
        
        # Insert second record with same hostname and image_name - should replace the first
        update_data2 = DiunUpdateData(
            hostname="server1",  # Same hostname now
            status="updated",
            provider="file",
            image_name="nginx", # Same image name
            image_tag="latest", # Different tag 
            digest="sha256:new_digest",
            image_created_at="2025-01-01T11:00:00Z"
        )
        result2 = upsert_diun_update(db, update_data2)
        
        # Should be a new record (different ID)
        assert result2.id != first_id
        
        # Verify only one nginx record exists for server1 (the new one)
        server1_nginx_records = db.query(DiunUpdate).filter(
            DiunUpdate.hostname == "server1",
            DiunUpdate.image_name == "nginx"
        ).all()
        assert len(server1_nginx_records) == 1
        assert server1_nginx_records[0].hostname == "server1"
        assert server1_nginx_records[0].digest == "sha256:new_digest"
        
        db.close()

    def test_upsert_different_servers_same_image_coexist(self, test_db):
        """Test that different servers can have the same image."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Insert record for server1
        update_data1 = DiunUpdateData(
            hostname="server1",
            status="new",
            provider="docker",
            image_name="nginx",
            image_tag="alpine", 
            digest="sha256:server1_digest",
            image_created_at="2025-01-01T10:00:00Z"
        )
        result1 = upsert_diun_update(db, update_data1)
        
        # Insert record for server2 with same image - should coexist
        update_data2 = DiunUpdateData(
            hostname="server2",  # Different hostname
            status="updated",
            provider="kubernetes",
            image_name="nginx", # Same image name
            image_tag="latest", # Different tag 
            digest="sha256:server2_digest",
            image_created_at="2025-01-01T11:00:00Z"
        )
        result2 = upsert_diun_update(db, update_data2)
        
        # Should be different records
        assert result2.id != result1.id
        
        # Verify both nginx records exist (one per server)
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

    def test_upsert_different_images_coexist(self, test_db):
        """Test that different image names can coexist."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Insert nginx record
        nginx_data = DiunUpdateData(
            hostname="server1",
            status="new",
            provider="docker",
            image_name="nginx",
            image_tag="alpine",
            digest="sha256:nginx_digest",
            image_created_at="2025-01-01T10:00:00Z"
        )
        nginx_result = upsert_diun_update(db, nginx_data)
        
        # Insert postgres record
        postgres_data = DiunUpdateData(
            hostname="server1", 
            status="new",
            provider="docker",
            image_name="postgres",
            image_tag="13",
            digest="sha256:postgres_digest",
            image_created_at="2025-01-01T10:00:00Z"
        )
        postgres_result = upsert_diun_update(db, postgres_data)
        
        # Both should exist
        all_records = db.query(DiunUpdate).all()
        assert len(all_records) == 2
        
        image_names = {record.image_name for record in all_records}
        assert image_names == {"nginx", "postgres"}
        
        db.close()

    def test_atomic_transaction(self, test_db):
        """Test that upsert operations are atomic - replace for same hostname and image."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Insert initial record
        initial_data = DiunUpdateData(
            hostname="server1",
            status="new",
            provider="docker", 
            image_name="nginx",
            image_tag="alpine",
            digest="sha256:initial_digest",
            image_created_at="2025-01-01T10:00:00Z"
        )
        upsert_diun_update(db, initial_data)
        
        # Verify record exists
        initial_count = db.query(DiunUpdate).count()
        assert initial_count == 1
        
        # Now test with valid upsert for same hostname and image - should replace atomically
        update_data = DiunUpdateData(
            hostname="server1",  # Same hostname
            status="updated", 
            provider="file",
            image_name="nginx",  # Same image
            image_tag="latest",
            digest="sha256:new_digest", 
            image_created_at="2025-01-01T11:00:00Z"
        )
        upsert_diun_update(db, update_data)
        
        # Should still have exactly 1 record (the new one replaced the old one)
        final_records = db.query(DiunUpdate).all()
        assert len(final_records) == 1
        assert final_records[0].hostname == "server1"  # Same hostname
        assert final_records[0].digest == "sha256:new_digest"
        assert final_records[0].image_tag == "latest"  # Updated tag
        
        db.close()

    def test_minimal_required_data(self, test_db):
        """Test with minimal required data (no optional fields)."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        update_data = DiunUpdateData(
            hostname="testserver",
            status="new",
            provider="docker",
            image_name="nginx", 
            image_tag="alpine",
            digest="sha256:abcd1234",
            image_created_at="2025-01-01T10:00:00Z"
            # No hub_link (optional field)
        )
        
        result = upsert_diun_update(db, update_data)
        
        assert result.hub_link is None
        assert result.hostname == "testserver"
        
        db.close()


class TestDeleteDiunUpdate:
    """Test the delete_diun_update database function."""
    
    def test_delete_existing_update(self, test_db):
        """Test deleting an existing update returns True."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Insert a test record first
        update_data = DiunUpdateData(
            hostname="testserver",
            status="new",
            provider="docker",
            image_name="nginx",
            image_tag="alpine",
            digest="sha256:test123",
            image_created_at="2025-01-01T10:00:00Z"
        )
        created_update = upsert_diun_update(db, update_data)
        update_id = created_update.id
        
        # Verify it exists
        assert db.query(DiunUpdate).filter(DiunUpdate.id == update_id).first() is not None
        
        # Delete it
        result = delete_diun_update(db, update_id)
        
        # Should return True for successful deletion
        assert result is True
        
        # Verify it's gone
        assert db.query(DiunUpdate).filter(DiunUpdate.id == update_id).first() is None
        
        db.close()

    def test_delete_nonexistent_update(self, test_db):
        """Test deleting a non-existent update returns False."""
        TestSessionLocal, test_engine = test_db
        db = TestSessionLocal()
        
        # Try to delete a non-existent update
        result = delete_diun_update(db, 999999)
        
        # Should return False for non-existent update
        assert result is False
        
        db.close()