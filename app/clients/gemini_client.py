import json
from typing import Dict, List, Optional

import google.generativeai as genai
import structlog

from app.core.config import settings
from app.core.errors import ExternalServiceError

logger = structlog.get_logger()


class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.generation_config = genai.GenerationConfig(
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            temperature=settings.GEMINI_TEMPERATURE,
        )

    async def chat(
        self,
        message: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, any]:
        try:
            prompt_parts = []
            
            if context:
                prompt_parts.append(f"Context: {context}\n")
            
            if conversation_history:
                prompt_parts.append("Conversation History:")
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    role = "Human" if msg["role"] == "user" else "Assistant"
                    prompt_parts.append(f"{role}: {msg['content']}")
                prompt_parts.append("")
            
            prompt_parts.append(f"Human: {message}")
            prompt_parts.append("Assistant:")
            
            full_prompt = "\n".join(prompt_parts)
            
            logger.info("Sending request to Gemini", 
                       model=settings.GEMINI_MODEL,
                       prompt_length=len(full_prompt))
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.generation_config
            )
            
            if not response.text:
                raise ExternalServiceError("Empty response from Gemini", "gemini")
            
            input_tokens = len(full_prompt.split())
            output_tokens = len(response.text.split())
            
            result = {
                "content": response.text.strip(),
                "model": settings.GEMINI_MODEL,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                "finish_reason": "completed"
            }
            
            logger.info("Gemini response received",
                       output_tokens=output_tokens,
                       total_tokens=result["usage"]["total_tokens"])
            
            return result
            
        except Exception as e:
            logger.error("Gemini API error", error=str(e))
            if "API_KEY" in str(e).upper():
                raise ExternalServiceError("Invalid Gemini API key", "gemini")
            elif "QUOTA" in str(e).upper() or "LIMIT" in str(e).upper():
                raise ExternalServiceError("Gemini API quota exceeded", "gemini")
            else:
                raise ExternalServiceError(f"Gemini API error: {str(e)}", "gemini")

    async def chat_with_document(
        self,
        message: str,
        document_chunks: List[Dict[str, any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, any]:
        context_parts = []
        for i, chunk in enumerate(document_chunks):
            context_parts.append(f"Document Section {i+1}:")
            context_parts.append(chunk.get("content", ""))
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        enhanced_message = f"""Based on the provided document context, please answer the following question. 
If the answer is not found in the document, please say so clearly.

Question: {message}"""
        
        return await self.chat(
            message=enhanced_message,
            context=context,
            conversation_history=conversation_history
        )

    async def test_connection(self) -> bool:
        try:
            response = await self.chat("Hey gemini kardeş")
            return bool(response.get("content"))
        except Exception as e:
            logger.error("Gemini connection test failed", error=str(e))
            return False
