import io
import pytest
from fastapi import status


class TestDocuments:
    def test_upload_document_success(self, client, auth_headers):
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        response = client.post("/api/v1/documents/", files=files, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["original_filename"] == "test.pdf"
        assert data["mime_type"] == "application/pdf"
        assert data["status"] == "UPLOADING"

    def test_upload_document_unauthorized(self, client):
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        response = client.post("/api/v1/documents/", files=files)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_upload_invalid_file_type(self, client, auth_headers):
        txt_content = b"This is a text file"
        
        files = {"file": ("test.txt", io.BytesIO(txt_content), "text/plain")}
        response = client.post("/api/v1/documents/", files=files, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_documents_success(self, client, auth_headers):
        response = client.get("/api/v1/documents/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)

    def test_list_documents_unauthorized(self, client):
        response = client.get("/api/v1/documents/")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_document_not_found(self, client, auth_headers):
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.get(f"/api/v1/documents/{fake_uuid}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_document_not_found(self, client, auth_headers):
        fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
        response = client.delete(f"/api/v1/documents/{fake_uuid}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
