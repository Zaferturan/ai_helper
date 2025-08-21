import streamlit as st
import requests
import json
import os
from datetime import datetime

# Backend URL
BACKEND_URL = "http://localhost:8000/api/v1"

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="AI Helper - Bursa Nilüfer Belediyesi",
    page_icon="icon.ico",
    layout="wide"
)

# CSS stilleri
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        margin-top: 1rem;
        background-color: #50c2eb !important;
        border-color: #50c2eb !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    .stButton > button:hover {
        background-color: #3ba8d1 !important;
        border-color: #3ba8d1 !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
    }
    .response-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .alternative-response {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
        cursor: pointer;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .selected-response {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .logo-image {
        width: 60px;
        height: 60px;
        object-fit: contain;
    }
    /* Text input gölgeleri */
    .stTextInput > div > div > input {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        border-radius: 4px !important;
    }
    /* Text area gölgeleri - daha spesifik */
    .stTextArea textarea {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        border-radius: 6px !important;
        padding: 12px !important;
    }
    /* Text area container'ları için gölge */
    .stTextArea > div {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        border-radius: 6px !important;
    }
    /* Text area'lar için ek gölge */
    .stTextArea > div > div > textarea {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        border-radius: 6px !important;
    }
    /* Selectbox gölgeleri */
    .stSelectbox > div > div > div {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        border-radius: 4px !important;
    }
    /* Slider gölgeleri */
    .stSlider > div > div > div {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    /* Expander gölgeleri - daha spesifik */
    .stExpander {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
    }
    .response-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

def get_models():
    """Get available models from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/models")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Modeller yüklenemedi")
            return []
    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        return []

def create_request(original_text):
    """Create a new request"""
    try:
        data = {
            "original_text": original_text,
            "response_type": "informative"  # Sabit değer
        }
        response = requests.post(f"{BACKEND_URL}/requests", json=data)
        if response.status_code == 200:
            return response.json()["id"]
        else:
            st.error("Request oluşturulamadı")
            return None
    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        return None

def generate_response(request_id, custom_input, temperature, top_p, repetition_penalty, model_name):
    """Generate response using LLM"""
    try:
        # Sistem promptunu session state'den al
        system_prompt = st.session_state.get('system_prompt', '')
        
        data = {
            "request_id": request_id,
            "model_name": model_name,
            "custom_input": custom_input,
            "citizen_name": "",  # Boş bırakılıyor, sadece "Sayın" yazacak
            "temperature": temperature,
            "top_p": top_p,
            "repetition_penalty": repetition_penalty,
            "system_prompt": system_prompt  # Sistem promptunu ekle
        }
        response = requests.post(f"{BACKEND_URL}/generate", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Yanıt üretilirken hata oluştu")
            return None
    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        return None

def update_response_feedback(response_id, is_selected=False, copied=False):
    """Update response feedback"""
    try:
        data = {
            "response_id": response_id,
            "is_selected": is_selected,
            "copied": copied
        }
        response = requests.post(f"{BACKEND_URL}/responses/feedback", json=data)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Geri bildirim güncellenemedi: {e}")
        return False

# Ana uygulama
def main():
    # Logo ve başlık
    col_logo, col_title, col_desc = st.columns([1, 3, 2])
    
    with col_logo:
        st.image("logo.png", width=60)
    
    with col_title:
        st.title("AI Yardımcı - Bursa Nilüfer Belediyesi")
    
    with col_desc:
        st.markdown("<div style='text-align: left; color: #333; font-size: 16px; font-weight: bold; margin: 10px 0; padding-top: 20px;'>Vatandaş taleplerine resmi yanıtlar hazırlayın</div>", unsafe_allow_html=True)
    
    # Açıklama yazısı kaldırıldı - daha temiz arayüz
    
    # Session state başlatma
    if 'responses' not in st.session_state:
        st.session_state.responses = []
    if 'current_response' not in st.session_state:
        st.session_state.current_response = None
    if 'generated_response' not in st.session_state:
        st.session_state.generated_response = None
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    # Modelleri al
    models = get_models()
    
    # Sistem promptu gizli - varsayılan değer kullanılıyor
    default_system_prompt = """Sen Bursa Nilüfer Belediyesi çalışanısın. Vatandaşlara resmi, kibar ve anlaşılır yanıtlar veriyorsun.

Sen Bursa Nilüfer Belediyesi'nde çalışan bir memursun.

Görevin, vatandaşlardan gelen talepleri dikkatle okuyarak onlara resmi, anlaşılır, kibar ve Türkçe bir dille yazılı yanıtlar oluşturmaktır.

Yanıtın yapısı şu şekilde olmalıdır:
1. "Sayın" ifadesiyle başlamalıdır.
2. Vatandaşın ilettiği konuyu resmi bir şekilde özetlemelisin.
3. Personelin hazırladığı cevabı daha uygun, nezaketli ve açıklayıcı bir dile dönüştürmelisin.
4. Metni "Saygılarımızla, Bursa Nilüfer Belediyesi" ifadesiyle bitirmelisin."""

    # Kaydedilmiş prompt dosyasını kontrol et (gizli)
    prompt_file = "saved_system_prompt.txt"
    
    # Session state'den sistem promptunu al veya dosyadan oku (gizli)
    if 'system_prompt' not in st.session_state:
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    st.session_state.system_prompt = f.read()
            except:
                st.session_state.system_prompt = default_system_prompt
        else:
            st.session_state.system_prompt = default_system_prompt
    
    # Sistem promptu gizli olarak kullanılıyor
    system_prompt = st.session_state.system_prompt
    
    # Model seçimi yanıt ayarları içinde olacak
    selected_model = "gemini-2.5-flash"  # Varsayılan model
    
    # İki sütunlu layout
    col_left, col_right = st.columns([1, 1])
    
    # Sol sütun - Giriş ve ayarlar
    with col_left:
        # Gelen istek/öneri
        st.subheader("📝 Gelen İstek/Öneri")
        original_text = st.text_area(
            "Gelen istek/öneri metnini buraya yapıştırın:",
            value="Bursa Nilüfer'de bir dükkanım var ve yönetim planından tahsisli otoparkımda bulunan dubaları, belediye ekipleri mafyavari şekilde tahsisli alanımdan alıp götürebiliyor. Geri aradığımda ise belediye zabıtası, görevliyi mahkemeye vermemi söylüyor. Bu nasıl bir hizmet anlayışı? Benim tahsisli alanımdan eşyamı alıyorsunuz, buna ne denir? Herkes biliyordur. Bir yeri koruduğunu zannedip başka bir yeri mağdur etmek mi belediyecilik?",
            height=150
        )
        
        # Hazırladığınız cevap
        st.subheader("✍️ Hazırladığınız Cevap")
        custom_input = st.text_area(
            "Hazırladığınız cevap taslağını buraya yazın:",
            value="Orası size tahsis edilmiş bir yer değil. Nilüfer halkının ortak kullanım alanı. Kaldırımlar da öyle.",
            height=100
        )
        
        # Yanıt ayarları
        with st.expander("🔧 Yanıt Ayarları", expanded=False):
            # Model seçimi (üstte)
            if models:
                # Sadece belirli modelleri göster
                allowed_models = [
                    "gemini-2.5-flash",
                    "gemini-1.5-flash-002", 
                    "gemini-2.0-flash-001",
                    "gpt-oss:latest"
                ]
                
                # Mevcut modellerden sadece izin verilenleri filtrele
                filtered_models = [model for model in models if model["name"] in allowed_models]
                
                if filtered_models:
                    model_names = [model["name"] for model in filtered_models]
                    selected_model = st.selectbox(
                        "🤖 Model Seçimi:",
                        model_names,
                        index=0,  # İlk model (gemini-2.5-flash) varsayılan olarak seçili
                        format_func=lambda x: next((m["display_name"] for m in filtered_models if m["name"] == x), x),
                        help="Kullanmak istediğiniz AI modelini seçin"
                    )
                else:
                    selected_model = "gemini-2.5-flash"  # Fallback
                    st.warning("⚠️ İzin verilen modeller bulunamadı, varsayılan model kullanılıyor")
            else:
                selected_model = "gemini-2.5-flash"  # Fallback
                st.warning("⚠️ Modeller yüklenemedi, varsayılan model kullanılıyor")
            
            # Ayırıcı çizgi kaldırıldı - daha temiz arayüz
            
            # LLM parametreleri
            col1, col2, col3 = st.columns(3)
            
            with col1:
                temperature = st.slider(
                    "🌡️ Temperature", 
                    min_value=0.0, 
                    max_value=2.0, 
                    value=st.session_state.get('last_temperature', 0.5), 
                    step=0.1,
                    help="Düşük değerler daha tutarlı, yüksek değerler daha yaratıcı yanıtlar üretir"
                )
            
            with col2:
                top_p = st.slider(
                    "🎯 Top-p", 
                    min_value=0.0, 
                    max_value=1.0, 
                    value=st.session_state.get('last_top_p', 0.4), 
                    step=0.1,
                    help="Kelime seçiminde çeşitliliği kontrol eder. Düşük değerler daha odaklı yanıtlar üretir"
                )
            
            with col3:
                repetition_penalty = st.slider(
                    "🔄 Repetition Penalty", 
                    min_value=0.0, 
                    max_value=3.0, 
                    value=st.session_state.get('last_repetition_penalty', 2.0), 
                    step=0.1,
                    help="Tekrarlanan kelimeleri azaltır. Yüksek değerler daha çeşitli kelime kullanımını sağlar"
                )
            
            # Parametreleri kaydetme dosyası
            llm_params_file = "saved_llm_params.json"
            
            # Varsayılan değerler
            default_params = {
                "temperature": 0.5,
                "top_p": 0.4,
                "repetition_penalty": 2.0
            }
            
            # Kaydedilmiş parametreleri yükle
            if os.path.exists(llm_params_file):
                try:
                    with open(llm_params_file, 'r', encoding='utf-8') as f:
                        saved_params = json.load(f)
                        # Eksik parametreler için varsayılan değerleri kullan
                        for key, default_value in default_params.items():
                            if key not in saved_params:
                                saved_params[key] = default_value
                except:
                    saved_params = default_params
            else:
                saved_params = default_params
            
            # Parametreler değiştiğinde kaydet
            current_params = {
                "temperature": temperature,
                "top_p": top_p,
                "repetition_penalty": repetition_penalty
            }
            
            if current_params != saved_params:
                try:
                    with open(llm_params_file, 'w', encoding='utf-8') as f:
                        json.dump(current_params, f, indent=2, ensure_ascii=False)
                    st.success("✅ LLM parametreleri kaydedildi!")
                except Exception as e:
                    st.error(f"❌ Kaydetme hatası: {e}")
        
        # Yanıt üret butonu
        if st.button("🚀 Yanıt Üret", type="primary", use_container_width=True):
            if original_text and custom_input:
                with st.spinner("Yanıt üretiliyor..."):
                    # Request oluştur
                    request_id = create_request(original_text)
                    
                    if request_id:
                        # Değişkenleri session_state'e kaydet
                        st.session_state.last_custom_input = custom_input
                        st.session_state.last_temperature = temperature
                        st.session_state.last_top_p = top_p
                        st.session_state.last_repetition_penalty = repetition_penalty
                        st.session_state.last_model_name = selected_model
                        
                        # Yanıt üret
                        response_data = generate_response(
                            request_id, custom_input, 
                            temperature, top_p, repetition_penalty, selected_model
                        )
                        
                        if response_data:
                            st.session_state.current_response = response_data
                            st.session_state.responses.append(response_data)
                            st.session_state.generated_response = response_data
                            
                            # History'ye en başa ekle
                            st.session_state.history.insert(0, response_data)
                            
                            st.success("✅ Yanıt başarıyla üretildi!")
                            st.rerun()
                        else:
                            st.error("❌ Yanıt üretilemedi")
                    else:
                        st.error("❌ Request oluşturulamadı")
            else:
                st.warning("⚠️ Lütfen gelen istek ve cevap alanlarını doldurun")
    
    # Sağ sütun - Yanıtlar paneli (sticky)
    with col_right:
        # Yanıt üretildikten sonra burada görünecek
        if st.session_state.generated_response:
            st.subheader("✅ Son Yanıt")
            
            response = st.session_state.generated_response
            response_text = response.get('response_text', '')
            latency_ms = response.get('latency_ms', 0)
            created_at = response.get('created_at', '')
            
            # Yanıt kartı
            st.markdown(f"""
            <div class="response-card">
                <p>{response_text.replace(chr(10), '<br>')}</p>
                <small>⏱️ Süre: {latency_ms:.0f}ms | 📅 {created_at}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Kopyala butonu
            if st.button("📋 Seç ve Kopyala", key="copy_latest", use_container_width=True):
                # JavaScript ile kopyalama
                st.markdown(f"""
                <script>
                navigator.clipboard.writeText(`{response_text}`).then(function() {{
                    console.log('Yanıt kopyalandı!');
                }});
                </script>
                """, unsafe_allow_html=True)
                st.success("✅ Yanıt panoya kopyalandı!")
                update_response_feedback(response['id'], is_selected=True, copied=True)
        
        # Önceki yanıtlar
        if len(st.session_state.history) > 1:
            st.subheader("📚 Önceki Yanıtlar")
            
            for i, resp in enumerate(st.session_state.history[1:], 1):  # İlk yanıt hariç
                with st.expander(f"Yanıt #{i} - {resp.get('created_at', '')}"):
                    st.markdown(f"""
                    <div class="response-card">
                        <p>{resp.get('response_text', '').replace(chr(10), '<br>')}</p>
                        <small>⏱️ {resp.get('latency_ms', 0):.0f}ms</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Her yanıt için "Seç ve Kopyala" butonu
                    if st.button(f"📋 Seç ve Kopyala #{i}", key=f"copy_old_{i}", use_container_width=True):
                        # JavaScript ile kopyalama
                        st.markdown(f"""
                        <script>
                        navigator.clipboard.writeText(`{resp.get('response_text', '')}`).then(function() {{
                            console.log('Yanıt #{i} kopyalandı!');
                        }});
                        </script>
                        """, unsafe_allow_html=True)
                        st.success(f"✅ Yanıt #{i} panoya kopyalandı ve seçildi!")
                        update_response_feedback(resp['id'], is_selected=True, copied=True)

if __name__ == "__main__":
    main() 