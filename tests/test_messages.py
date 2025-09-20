import pytest
from fastapi import status


class TestMessages:
    def test_send_message_without_document_or_conversation(self, client, auth_headers):
        message_data = {
            "message": "Hello, this is a test message"
        }
        
        response = client.post("/api/v1/messages/", json=message_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_send_message_unauthorized(self, client):
        message_data = {
            "message": "Hello, this is a test message",
            "document_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        
        response = client.post("/api/v1/messages/", json=message_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_send_message_with_invalid_document(self, client, auth_headers):
        message_data = {
            "message": "Hello, this is a test message",
            "document_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        
        response = client.post("/api/v1/messages/", json=message_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_conversations_success(self, client, auth_headers):
        response = client.get("/api/v1/messages/conversations", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "conversations" in data
        assert "total" in data
        assert isinstance(data["conversations"], list)

    def test_list_conversations_unauthorized(self, client):
        response = client.get("/api/v1/messages/conversations")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_conversation_not_found(self, client, auth_headers):
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/v1/messages/conversations/{fake_uuid}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_conversation_messages_not_found(self, client, auth_headers):
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/v1/messages/conversations/{fake_uuid}/messages", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_conversation_not_found(self, client, auth_headers):
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.delete(f"/api/v1/messages/conversations/{fake_uuid}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
