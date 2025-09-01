import httpx
import time
from typing import List, Dict, Any
from config import GEMINI_API_KEY, GEMINI_API_URL

class GeminiClient:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.base_url = GEMINI_API_URL.rstrip('/')
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available Gemini models"""
        try:
            if not self.api_key:
                print("Warning: GEMINI_API_KEY not set")
                return []
            
            # API Key ile çalışan Gemini modelleri
            gemini_models = [
                {
                    'name': 'gemini-2.5-flash',
                    'display_name': 'Gemini 2.5 Flash',
                    'supports_embedding': True,
                    'supports_chat': True
                },
                {
                    'name': 'gemini-2.5-pro',
                    'display_name': 'Gemini 2.5 Pro',
                    'supports_embedding': True,
                    'supports_chat': True
                },
                {
                    'name': 'gemini-2.5-flash-lite',
                    'display_name': 'Gemini 2.5 Flash Lite',
                    'supports_embedding': True,
                    'supports_chat': True
                },
                {
                    'name': 'gemini-2.0-flash-001',
                    'display_name': 'Gemini 2.0 Flash',
                    'supports_embedding': True,
                    'supports_chat': True
                },
                {
                    'name': 'gemini-2.0-flash-lite-001',
                    'display_name': 'Gemini 2.0 Flash Lite',
                    'supports_embedding': True,
                    'supports_chat': True
                },
                {
                    'name': 'gemini-1.5-pro-002',
                    'display_name': 'Gemini 1.5 Pro',
                    'supports_embedding': True,
                    'supports_chat': True
                },
                {
                    'name': 'gemini-1.5-flash-002',
                    'display_name': 'Gemini 1.5 Flash',
                    'supports_embedding': True,
                    'supports_chat': True
                },
                {
                    'name': 'gemini-pro',
                    'display_name': 'Gemini Pro',
                    'supports_embedding': True,
                    'supports_chat': True
                }
            ]
            
            return gemini_models
        except Exception as e:
            print(f"Error getting Gemini models: {e}")
            return []
    
    async def generate_response(self, model_name: str, prompt: str, temperature: float = 0.7, top_p: float = 0.9, repetition_penalty: float = 1.2, system_prompt: str = "") -> Dict[str, Any]:
        """Generate response from Gemini model"""
        try:
            if not self.api_key:
                return {
                    'response_text': "Error: GEMINI_API_KEY not configured or invalid",
                    'latency_ms': 0,
                    'success': False
                }
            
            start_time = time.time()
            
            # Frontend'den gelen sistem promptunu kullan, yoksa varsayılanı kullan
            if system_prompt:
                final_system_prompt = system_prompt
            else:
                # Varsayılan sistem promptu
                final_system_prompt = """Bursa Nilüfer Belediyesi adına resmi yanıt hazırla.

Yanıt şablonu:
1. "Sayın," ile başla
2. Vatandaşın talebini özetle (1-2 cümle)
3. Personelin cevabını genişlet ve düzelt
4. Resmi, kibar dil kullan
5. "Saygılarımızla, Bursa Nilüfer Belediyesi" ile bitir

Uzunluk: 150-300 kelime"""

            full_prompt = f"{final_system_prompt}\n\n{prompt}"
            
            async with httpx.AsyncClient() as client:
                headers = {
                    "X-Goog-Api-Key": self.api_key,
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": full_prompt
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": temperature,
                        "topP": top_p,
                        "maxOutputTokens": 4000  # 2000'den 4000'e çıkarıldı
                    }
                }
                
                # Gemini API endpoint - gemini-pro için v1, diğerleri için v1beta
                if model_name == "gemini-pro":
                    api_version = "v1"
                else:
                    api_version = "v1beta"
                
                model_endpoint = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent"
                
                response = await client.post(model_endpoint, json=payload, headers=headers, timeout=300.0)
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    
                    response_text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    
                    return {
                        'response_text': response_text,
                        'latency_ms': latency_ms,
                        'success': True
                    }
                else:
                    error_text = f"HTTP {response.status_code}: {response.text}"
                    return {
                        'response_text': error_text,
                        'latency_ms': latency_ms,
                        'success': False
                    }
        except httpx.TimeoutException:
            return {
                'response_text': "Timeout: Request took too long (300 seconds). Model may be too slow or overloaded.",
                'latency_ms': 0,
                'success': False
            }
        except httpx.ConnectError:
            return {
                'response_text': "Connection Error: Could not connect to Gemini API. Please check your API key and internet connection.",
                'latency_ms': 0,
                'success': False
            }
        except Exception as e:
            return {
                'response_text': f"Error: {str(e)}",
                'latency_ms': 0,
                'success': False
            } 