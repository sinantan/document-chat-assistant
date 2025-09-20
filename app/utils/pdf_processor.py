import io
from typing import List, Dict, Any

from pypdf import PdfReader

from app.core.config import settings


class PDFProcessor:
    @staticmethod
    def extract_text_from_pdf(pdf_content: bytes) -> str:
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    @staticmethod
    def get_pdf_page_count(pdf_content: bytes) -> int:
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            return len(pdf_reader.pages)
            
        except Exception as e:
            raise ValueError(f"Failed to get page count from PDF: {str(e)}")
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        if chunk_size is None:
            chunk_size = settings.PDF_CHUNK_SIZE
        if overlap is None:
            overlap = settings.PDF_CHUNK_OVERLAP
        
        if not text.strip():
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunk = {
                "content": chunk_text,
                "metadata": {
                    "chunk_index": len(chunks),
                    "word_count": len(chunk_words),
                    "char_count": len(chunk_text),
                    "start_word": i,
                    "end_word": min(i + chunk_size, len(words))
                }
            }
            chunks.append(chunk)
            
            if i + chunk_size >= len(words):
                break
        
        return chunks
    
    @staticmethod
    def process_pdf(pdf_content: bytes) -> Dict[str, Any]:
        try:
            text = PDFProcessor.extract_text_from_pdf(pdf_content)
            page_count = PDFProcessor.get_pdf_page_count(pdf_content)
            chunks = PDFProcessor.chunk_text(text)
            
            return {
                "text": text,
                "page_count": page_count,
                "chunks": chunks,
                "word_count": len(text.split()),
                "char_count": len(text),
                "chunk_count": len(chunks)
            }
            
        except Exception as e:
            raise ValueError(f"Failed to process PDF: {str(e)}")
