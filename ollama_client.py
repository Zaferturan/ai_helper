import httpx
import time
from typing import List, Dict, Any
from config import OLLAMA_HOST

class OllamaClient:
    def __init__(self):
        self.base_url = OLLAMA_HOST.rstrip('/')
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get('models', []):
                        model_info = {
                            'name': model.get('name', ''),
                            'display_name': model.get('name', '').replace(':', ' ').title(),
                            'supports_embedding': True,  # Default assumption
                            'supports_chat': True,       # Default assumption
                            'size': model.get('size', 0),
                            'modified_at': model.get('modified_at', '')
                        }
                        models.append(model_info)
                    return models
                else:
                    print(f"Error getting models: {response.status_code}")
                    return []
        except Exception as e:
            print(f"Error connecting to Ollama: {e}")
            return []
    
    async def generate_response(self, model_name: str, prompt: str, citizen_name: str = None, temperature: float = 0.7, top_p: float = 0.9, repetition_penalty: float = 1.2) -> Dict[str, Any]:
        """Generate response from Ollama model"""
        try:
            start_time = time.time()
            
            # Vatandaş adına göre hitap belirleme
            print(f"DEBUG: citizen_name = '{citizen_name}' (type: {type(citizen_name)})")
            
            if citizen_name and citizen_name.strip():
                hitap = f"Sayın {citizen_name.strip().upper()},"
                print(f"DEBUG: Using personalized greeting: '{hitap}'")
            else:
                hitap = "Değerli Vatandaşımız,"
                print(f"DEBUG: Using default greeting: '{hitap}'")
            
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
            
            print(f"DEBUG: Final system prompt starts with: '{system_prompt[:100]}...'")
            
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "repetition_penalty": repetition_penalty,
                        "num_predict": 500  # Maksimum token sayısını sınırla
                    }
                }
                
                # Timeout süresini 300 saniyeye çıkar
                response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=300.0)
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'response_text': data.get('response', ''),
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
                'response_text': "Connection Error: Could not connect to Ollama. Please check if Ollama is running.",
                'latency_ms': 0,
                'success': False
            }
        except Exception as e:
            return {
                'response_text': f"Error: {str(e)}",
                'latency_ms': 0,
                'success': False
            } 