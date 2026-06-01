"""
LLM Service
============
Abstraction layer for Large Language Model interactions.
Supports OpenAI API with fallback to mock responses for development.
"""

import time
from typing import List, Optional

from loguru import logger

from app.core.config import get_settings
from app.schemas.chat import ChatMessage, MessageRole


# System prompt tailored for the Nestra wind energy dashboard
SYSTEM_PROMPT = """Kamu adalah Mahi AI, asisten cerdas untuk Dashboard Nestra — platform analisis dan prediksi potensi angin untuk Pembangkit Listrik Tenaga Bayu (PLTB) di Indonesia.

Keahlianmu meliputi:
- Analisis data kecepatan dan arah angin
- Prediksi potensi energi angin berdasarkan data historis
- Penilaian kelayakan lokasi PLTB (site assessment)
- Interpretasi wind rose, distribusi Weibull, dan statistik angin
- Rekomendasi teknis untuk pengembangan PLTB
- Pengetahuan tentang energi terbarukan di Indonesia

Pedoman:
1. Jawab dalam Bahasa Indonesia yang profesional namun mudah dipahami
2. Berikan analisis berbasis data jika konteks data tersedia
3. Sertakan insight dan rekomendasi yang actionable
4. Gunakan terminologi teknis energi angin yang tepat
5. Jika tidak yakin, sampaikan keterbatasan dan saran untuk investigasi lebih lanjut

Kamu sedang membantu pengguna yang menggunakan dashboard Nestra untuk menganalisis potensi PLTB di berbagai lokasi di Indonesia."""


class LLMService:
    """Service for LLM interactions — production-ready with fallback."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None

    def _get_client(self):
        """Lazy-initialize the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"OpenAI client initialization failed: {e}")
                self._client = None
        return self._client

    def _build_messages(
        self,
        user_message: str,
        conversation_history: List[ChatMessage],
        context: Optional[dict] = None,
    ) -> list:
        """Build the messages array for the OpenAI API."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Inject dashboard context if available
        if context:
            context_str = f"\n\n[Konteks Dashboard]\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            messages[0]["content"] += context_str

        # Add conversation history (last 20 messages max)
        for msg in conversation_history[-20:]:
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[ChatMessage],
        context: Optional[dict] = None,
    ) -> dict:
        """
        Generate an AI response.
        Falls back to mock response if OpenAI is not configured.
        """
        start_time = time.time()

        client = self._get_client()

        # Check if OpenAI is properly configured
        if client and self.settings.OPENAI_API_KEY and not self.settings.OPENAI_API_KEY.startswith("sk-your"):
            return await self._call_openai(user_message, conversation_history, context, start_time)
        else:
            logger.info("Using mock LLM response (OpenAI not configured)")
            return self._mock_response(user_message, start_time)

    async def _call_openai(
        self,
        user_message: str,
        conversation_history: List[ChatMessage],
        context: Optional[dict],
        start_time: float,
    ) -> dict:
        """Call the OpenAI API for a real response."""
        try:
            messages = self._build_messages(user_message, conversation_history, context)

            response = self._client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=messages,
                temperature=self.settings.OPENAI_TEMPERATURE,
                max_tokens=self.settings.OPENAI_MAX_TOKENS,
            )

            elapsed_ms = (time.time() - start_time) * 1000
            result = response.choices[0].message.content

            logger.info(
                f"OpenAI response generated — model={self.settings.OPENAI_MODEL}, "
                f"tokens={response.usage.total_tokens}, time={elapsed_ms:.1f}ms"
            )

            return {
                "reply": result,
                "model": self.settings.OPENAI_MODEL,
                "tokens_used": response.usage.total_tokens,
                "processing_time_ms": round(elapsed_ms, 2),
            }

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return self._mock_response(user_message, start_time, error=str(e))

    def _mock_response(
        self,
        user_message: str,
        start_time: float,
        error: Optional[str] = None,
    ) -> dict:
        """Generate a mock response for development/demo purposes."""
        elapsed_ms = (time.time() - start_time) * 1000

        if error:
            reply = (
                f"⚠️ Maaf, terjadi kesalahan saat memproses permintaan Anda.\n\n"
                f"**Error:** {error}\n\n"
                f"Silakan pastikan API key OpenAI telah dikonfigurasi dengan benar di file `.env`."
            )
        else:
            reply = (
                f"🤖 **Mahi AI — Mode Demo**\n\n"
                f"Terima kasih atas pertanyaan Anda:\n"
                f"> *\"{user_message[:200]}\"*\n\n"
                f"Saat ini saya beroperasi dalam **mode demo** karena API key OpenAI belum dikonfigurasi.\n\n"
                f"### Untuk mengaktifkan AI penuh:\n"
                f"1. Buka file `backend/.env`\n"
                f"2. Isi `OPENAI_API_KEY` dengan API key Anda\n"
                f"3. Restart server backend\n\n"
                f"### Kemampuan yang akan tersedia:\n"
                f"- 📊 Analisis data angin real-time\n"
                f"- 🌬️ Prediksi potensi energi angin\n"
                f"- 📍 Penilaian kelayakan lokasi PLTB\n"
                f"- 📈 Interpretasi grafik dan statistik\n"
                f"- 💡 Rekomendasi teknis berbasis AI\n\n"
                f"*Powered by Dashboard Mahi AI Backend v0.1.0*"
            )

        return {
            "reply": reply,
            "model": "mock-demo",
            "tokens_used": None,
            "processing_time_ms": round(elapsed_ms, 2),
        }


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
