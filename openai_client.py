import httpx
import time
from typing import List, Dict, Any, Optional
from config import OPENAI_API_KEY, OPENAI_API_URL


class OpenAIClient:
    """OpenAI-compatible chat completions client (gateway /v1)."""

    def __init__(self):
        self.api_key = (OPENAI_API_KEY or "").strip()
        self.base_url = (OPENAI_API_URL or "").rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def get_models(self) -> List[Dict[str, Any]]:
        """List chat-capable models from OpenAI-compatible /models endpoint."""
        if not self.enabled:
            print("Warning: OPENAI_API_KEY / OPENAI_API_URL not set")
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/models", headers=self._headers())

            if response.status_code != 200:
                print(f"Error getting OpenAI models: {response.status_code} {response.text[:300]}")
                return self._fallback_models()

            data = response.json()
            raw_models = data.get("data") or data.get("models") or []
            models = []
            for item in raw_models:
                name = item.get("id") if isinstance(item, dict) else str(item)
                if not name:
                    continue
                # Embedding modellerini liste dışı bırak
                lower = name.lower()
                if "embed" in lower or "embedding" in lower:
                    continue
                models.append(
                    {
                        "name": name,
                        "display_name": name,
                        "supports_embedding": False,
                        "supports_chat": True,
                        "provider": "openai",
                    }
                )

            # Gemini listesinin üstünde gösterilsin diye isim sırasını koru (gateway sırası)
            return models or self._fallback_models()
        except Exception as e:
            print(f"Error connecting to OpenAI-compatible API: {e}")
            return self._fallback_models()

    def _fallback_models(self) -> List[Dict[str, Any]]:
        """Gateway geçici down olsa bile bilinen chat modellerini göster."""
        names = [
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-5.4-mini",
            "gurubase-siper",
        ]
        return [
            {
                "name": n,
                "display_name": n,
                "supports_embedding": False,
                "supports_chat": True,
                "provider": "openai",
            }
            for n in names
        ]

    def is_openai_model(self, model_name: str) -> bool:
        if not model_name:
            return False
        # Ollama etiketleri (gpt-oss:latest) OpenAI değildir
        if ":" in model_name:
            return False
        lower = model_name.lower()
        return (
            lower.startswith("gpt-")
            or lower.startswith("o1")
            or lower.startswith("o3")
            or lower.startswith("o4")
            or lower.startswith("gurubase-")
            or lower.startswith("chatgpt-")
        )

    async def generate_response(
        self,
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        repetition_penalty: float = 1.2,
        system_prompt: str = "",
        max_tokens: Optional[int] = 4000,
    ) -> Dict[str, Any]:
        """Generate response via OpenAI-compatible chat/completions."""
        if not self.enabled:
            return {
                "response_text": "Error: OPENAI_API_KEY / OPENAI_API_URL not configured",
                "latency_ms": 0,
                "success": False,
            }

        try:
            start_time = time.time()

            if system_prompt:
                final_system_prompt = system_prompt
            else:
                final_system_prompt = """Bursa Nilüfer Belediyesi adına resmi yanıt hazırla.

Yanıt şablonu:
1. "Sayın," ile başla
2. Vatandaşın talebini özetle (1-2 cümle)
3. Personelin cevabını genişlet ve düzelt
4. Resmi, kibar dil kullan
5. "Saygılarımızla, Bursa Nilüfer Belediyesi" ile bitir

Uzunluk: 150-300 kelime"""

            messages = [
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": prompt},
            ]

            payload: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens

            # Not: Bu gateway top_p / frequency_penalty için 415 (PII policy) döndürüyor;
            # bu yüzden gönderilmiyor. repetition_penalty / top_p parametreleri yok sayılıyor.

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                )

            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices") or []
                response_text = ""
                if choices:
                    message = choices[0].get("message") or {}
                    response_text = message.get("content") or choices[0].get("text") or ""
                return {
                    "response_text": response_text,
                    "latency_ms": latency_ms,
                    "success": True,
                }

            return {
                "response_text": f"HTTP {response.status_code}: {response.text}",
                "latency_ms": latency_ms,
                "success": False,
            }
        except httpx.TimeoutException:
            return {
                "response_text": "Timeout: OpenAI-compatible API request took too long (300 seconds).",
                "latency_ms": 0,
                "success": False,
            }
        except httpx.ConnectError:
            return {
                "response_text": "Connection Error: Could not connect to OpenAI-compatible API.",
                "latency_ms": 0,
                "success": False,
            }
        except Exception as e:
            return {
                "response_text": f"Error: {str(e)}",
                "latency_ms": 0,
                "success": False,
            }
