// MongoDB initialization script for development
// Simple setup without authentication

db = db.getSiblingDB('document_chat');

// Only create chunks collection for text storage
db.createCollection('chunks');

// GridFS collections (fs.files, fs.chunks) are created automatically

// Indexes for chunks collection
db.chunks.createIndex({ "document_id": 1 });
db.chunks.createIndex({ "chunk_index": 1 });
db.chunks.createIndex({ "document_id": 1, "chunk_index": 1 });

print('MongoDB initialization completed successfully!');
