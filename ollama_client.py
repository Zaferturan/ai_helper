import httpx
import time
from typing import List, Dict, Any
from config import OLLAMA_HOST

class OllamaClient:
    def __init__(self):
        self.base_url = OLLAMA_HOST.rstrip('/')
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from Ollama"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags")
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
    
    async def generate_response(self, model_name: str, prompt: str, temperature: float = 0.7, top_p: float = 0.9, repetition_penalty: float = 1.2, system_prompt: str = "") -> Dict[str, Any]:
        """Generate response from Ollama model"""
        try:
            start_time = time.time()
            
            # Frontend'den gelen sistem promptunu kullan, yoksa varsayılanı kullan
            if system_prompt:
                final_system_prompt = system_prompt
            else:
                # Varsayılan sistem promptu
                final_system_prompt = """Bursa Nilüfer Belediyesi adına resmi yanıt hazırla.

ZORUNLU YANIT ŞABLONU:
1. "Sayın," ile başla
2. Vatandaşın talebini özetle (1-2 cümle)
3. Personelin cevabını genişlet ve düzelt
4. Resmi, kibar dil kullan
5. "Saygılarımızla, Bursa Nilüfer Belediyesi" ile bitir

Uzunluk: 150-300 kelime, 3-4 paragraf"""
            
            full_prompt = f"{final_system_prompt}\n\n{prompt}"
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                        "repetition_penalty": repetition_penalty,
                        "num_predict": 4000  # Token limiti eklendi
                    }
                }
                
                # Timeout süresini 300 saniyeye çıkar
                response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=300.0)
                
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '')
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