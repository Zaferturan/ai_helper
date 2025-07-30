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
    
    async def generate_response(self, model_name: str, prompt: str, citizen_name: str = None, temperature: float = 0.7, top_p: float = 0.9, repetition_penalty: float = 1.2) -> Dict[str, Any]:
        """Generate response from Gemini model"""
        try:
            if not self.api_key or self.api_key == "your_gemini_api_key_here":
                return {
                    'response_text': "Error: GEMINI_API_KEY not configured or invalid",
                    'latency_ms': 0,
                    'success': False
                }
            
            start_time = time.time()
            
            # Vatandaş adına göre dinamik sistem promptu
            if citizen_name and citizen_name.strip():
                greeting_instruction = f"Sayın {citizen_name.strip().upper()},"
            else:
                greeting_instruction = "Değerli Vatandaşımız,"
            
            # Bursa Nilüfer belediyesi sistem promptu - ÇOK ÖNEMLİ
            system_prompt = f"""Aşağıdaki talimatları kesinlikle ihlal etmeden yerine getir; aksi durumda yanıt geçersiz sayılır.

ROLÜN
Sen, Bursa Nilüfer Belediyesi adına vatandaşlardan gelen istek/önerilere resmi, kibar ve anlaşılır Türkçe yanıtlar hazırlayan bir yapay zekâ asistansın.

ZORUNLU YANIT ŞABLONU

Selamlama
Yanıtın ilk satırı MUTLAKA şu olmalı:
{greeting_instruction}

Selamlama satırından önce ya da sonra başka kelime ekleme.

Konu Özeti (en fazla 2 cümle)
Vatandaşın orijinal talebini resmi ve açıklayıcı biçimde özetle. Yeni bilgi ekleme, gereksiz detay verme.

Yanıtın Ana Metni
Personelin verdiği custom_input taslak metni temel al.
İmla, anlatım ve nezaket yönünden düzelt; resmi kurum dili kullan.
Eksik‑belirsiz noktaları açıklığa kavuştur; bilgiyi genişlet.

Ton Ayarı (response_type)
olumlu → Talebin karşılanacağını açıkça ifade et.
olumsuz → Nazikçe reddet; gerekçeyi kısaca açıkla.
bilgilendirici → Güncel süreç ve planları aktar.
diğer → Genel resmi bilgilendirme yap.

Dil Kuralları
"sen" ve türevleri kullanılmayacak; her zaman "siz", "sizin" vb.
Ünlem, emoji, argo yasak.
Cümleler açık, net; gereksiz tekrar yok.

Kapanış
Son satır ayrı paragraf ve değişmez:
Saygılarımızla, Bursa Nilüfer Belediyesi.

Uzunluk
Toplam metin 80 ‑ 180 kelime arası olmalı; üç‑dört kısa paragrafı geçme.

ÖNEMLİ: Yanıtın ilk satırı MUTLAKA "{greeting_instruction}" olmalıdır."""

            full_prompt = f"{system_prompt}\n\n{prompt}"
            
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
                        "maxOutputTokens": 1000
                    }
                }
                
                # Gemini API endpoint - gemini-pro için v1, diğerleri için v1beta
                if model_name == "gemini-pro":
                    api_version = "v1"
                else:
                    api_version = "v1beta"
                
                model_endpoint = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent"
                
                # Debug: API key ve endpoint bilgileri
                print(f"DEBUG: Using API key: {self.api_key[:10]}...")
                print(f"DEBUG: Model endpoint: {model_endpoint}")
                print(f"DEBUG: Headers: {headers}")
                
                response = await client.post(model_endpoint, json=payload, headers=headers, timeout=300.0)
                
                # Debug: Response bilgileri
                print(f"DEBUG: Response status: {response.status_code}")
                print(f"DEBUG: Response text: {response.text[:200]}...")
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"DEBUG: Response data: {data}")
                    
                    response_text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    print(f"DEBUG: Extracted response text: '{response_text}'")
                    
                    return {
                        'response_text': response_text,
                        'latency_ms': latency_ms,
                        'success': True
                    }
                else:
                    error_text = f"HTTP {response.status_code}: {response.text}"
                    print(f"DEBUG: Error response: {error_text}")
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