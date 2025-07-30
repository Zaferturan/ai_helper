import streamlit as st
import requests
import json
import os
from datetime import datetime

# Backend URL
BACKEND_URL = "http://localhost:3200/api/v1"

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
    /* Tüm elementlere gölge */
    .stTextInput > div > div > input {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        border-radius: 4px !important;
    }
    .stTextArea > div > div > textarea {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        border-radius: 4px !important;
    }
    .stSelectbox > div > div > div {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        border-radius: 4px !important;
    }
    .stSlider > div > div > div {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    .stExpander > div > div {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        border-radius: 4px !important;
    }
    /* Textbox'lar için özel gölge */
    .stTextInput > div, .stTextArea > div, .stSelectbox > div {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        border-radius: 4px !important;
    }
    /* Yanıt ayarları expander için özel gölge */
    .stExpander > div {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        border-radius: 8px !important;
    }
    /* Text area'lar için daha güçlü gölge */
    .stTextArea > div > div > textarea {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        border-radius: 6px !important;
    }
    /* Text area container'ları için gölge */
    .stTextArea > div {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        border-radius: 6px !important;
    }
    /* Expander için daha spesifik gölge */
    .stExpander > div > div {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        border-radius: 8px !important;
    }
    /* Başlık ve alt başlıklara gölge */
    h1, h2, h3 {
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Logo gölgesi */
    .stImage > img {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
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

def create_request(original_text, response_type):
    """Create a new request"""
    try:
        data = {
            "original_text": original_text,
            "response_type": response_type
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

def generate_response(request_id, custom_input, citizen_name, temperature, top_p, repetition_penalty):
    """Generate response using LLM"""
    try:
        data = {
            "request_id": request_id,
            "model_name": "gemini-2.5-flash-lite",  # Sabit model
            "custom_input": custom_input,
            "citizen_name": citizen_name,
            "temperature": temperature,
            "top_p": top_p,
            "repetition_penalty": repetition_penalty
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
    col_logo, col_title = st.columns([1, 4])
    
    with col_logo:
        st.image("logo.png", width=60)
    
    with col_title:
        st.title("AI Yardımcı - Bursa Nilüfer Belediyesi")
    
    # Açıklama yazısı başlığın altında
    st.markdown("<div style='text-align: center; color: #333; font-size: 16px; font-weight: bold; margin: 10px 0;'>Vatandaş taleplerine resmi yanıtlar hazırlayın</div>", unsafe_allow_html=True)
    
    # Session state başlatma
    if 'responses' not in st.session_state:
        st.session_state.responses = []
    if 'current_response' not in st.session_state:
        st.session_state.current_response = None
    
    # Son üretilen yanıt gösterimi (başlığın hemen altında)
    if 'generated_response' in st.session_state and st.session_state.generated_response:
        st.markdown("---")
        st.subheader("✅ Son Üretilen Yanıt")
        
        response = st.session_state.generated_response
        response_text = response.get('response_text', '')
        latency_ms = response.get('latency_ms', 0)
        created_at = response.get('created_at', '')
        
        # Yanıt kutusu
        st.markdown(f"""
        <div class="response-box">
            <p>{response_text.replace(chr(10), '<br>')}</p>
            <small>⏱️ Süre: {latency_ms:.0f}ms | 📅 {created_at}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Alternatif yanıtlar ve aksiyonlar (üstte)
        if st.session_state.current_response:
            st.markdown("---")
            st.subheader("🔄 Alternatif Yanıtlar")
            
            # Aksiyon butonları
            col_alt, col_select = st.columns(2)
            
            with col_alt:
                if st.button("🔄 Alternatif Üret") and len(st.session_state.responses) < 5:
                    st.info("Alternatif yanıt üretiliyor...")
                    # Yeni alternatif üret - tüm değişkenleri session_state'den al
                    if ('last_custom_input' in st.session_state and 
                        'last_citizen_name' in st.session_state and
                        'last_temperature' in st.session_state and
                        'last_top_p' in st.session_state and
                        'last_repetition_penalty' in st.session_state):
                        
                        new_response = generate_response(
                            st.session_state.current_response['request_id'], 
                            st.session_state.last_custom_input, 
                            st.session_state.last_citizen_name,
                            st.session_state.last_temperature,
                            st.session_state.last_top_p,
                            st.session_state.last_repetition_penalty
                        )
                        if new_response:
                            st.session_state.responses.append(new_response)
                            st.session_state.current_response = new_response
                            st.session_state.generated_response = new_response
                            st.rerun()
                    else:
                        st.error("Önce bir yanıt üretin")
                elif len(st.session_state.responses) >= 5:
                    st.warning("Maksimum 5 alternatif üretildi")
            
            with col_select:
                if st.button("✅ Seç ve Kopyala"):
                    # Yanıtı panoya kopyala
                    st.write("Yanıt panoya kopyalandı ve seçildi!")
                    update_response_feedback(st.session_state.current_response['id'], is_selected=True, copied=True)
                    st.success("Yanıt seçildi ve kopyalandı!")
        
        # Önceki yanıtlar (alternatif yanıtların altında)
        if len(st.session_state.responses) > 1:
            st.markdown("---")
            st.subheader("📚 Önceki Yanıtlar")
            
            for i, resp in enumerate(st.session_state.responses[:-1]):  # Son yanıt hariç
                with st.expander(f"Yanıt #{i+1} - {resp.get('created_at', '')}"):
                    st.write(resp.get('response_text', ''))
                    st.caption(f"⏱️ {resp.get('latency_ms', 0):.0f}ms")
                    
                    # Eski yanıtlar için de seç butonu
                    if st.button(f"✅ Seç ve Kopyala #{i+1}", key=f"select_old_{i}"):
                        st.write("Yanıt panoya kopyalandı ve seçildi!")
                        update_response_feedback(resp['id'], is_selected=True, copied=True)
                        st.success(f"Yanıt #{i+1} seçildi ve kopyalandı!")
    
    # İki sütunlu layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Gelen İstek/Öneri")
        original_text = st.text_area(
            "Gelen istek/öneri metnini buraya yapıştırın:",
            value="Bursa Nilüfer'de bir dükkanım var ve yönetim planından tahsisli otoparkımda bulunan dubaları, belediye ekipleri mafyavari şekilde tahsisli alanımdan alıp götürebiliyor. Geri aradığımda ise belediye zabıtası, görevliyi mahkemeye vermemi söylüyor. Bu nasıl bir hizmet anlayışı? Benim tahsisli alanımdan eşyamı alıyorsunuz, buna ne denir? Herkes biliyordur. Bir yeri koruduğunu zannedip başka bir yeri mağdur etmek mi belediyecilik?",
            height=200
        )
        
        st.subheader("👤 Adı Soyadı")
        citizen_name = st.text_input("Vatandaşın adı ve soyadını girin:", value="Zafer Turan")
    
    with col2:
        st.subheader("✍️ Hazırladığınız Cevap")
        custom_input = st.text_area(
            "Hazırladığınız cevap taslağını buraya yazın:",
            value="Orası size tahsis edilmiş bir yer değil. Nilüfer halkının ortak kullanım alanı. Kaldırımlar da öyle.",
            height=200
        )
        
        st.subheader("📋 Geri Dönüş Tipi")
        response_type = st.selectbox(
            "Yanıt tipini seçin:",
            ["positive", "negative", "informative", "other"],
            format_func=lambda x: {
                "positive": "Olumlu",
                "negative": "Olumsuz", 
                "informative": "Bilgilendirici",
                "other": "Diğer"
            }[x]
        )
    
    # LLM parametreleri - tam genişlik (kolonların dışında)
    st.markdown("---")
    with st.expander("🎚️ Yanıt Ayarları", expanded=False):
        # LLM parametrelerini kaydetme dosyası
        llm_params_file = "saved_llm_params.json"
        
        # Varsayılan değerler
        default_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.2
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
        
        col_temp, col_topp, col_rep = st.columns(3)
        
        with col_temp:
            temperature = st.slider("Temperature", 0.1, 1.5, saved_params["temperature"], 0.1)
        with col_topp:
            top_p = st.slider("Top-p", 0.1, 1.0, saved_params["top_p"], 0.05)
        with col_rep:
            repetition_penalty = st.slider("Repetition Penalty", 1.0, 2.0, saved_params["repetition_penalty"], 0.1)
        
        # Parametreler değiştiğinde kaydet
        current_params = {
            "temperature": temperature,
            "top_p": top_p,
            "repetition_penalty": repetition_penalty
        }
        
        if current_params != saved_params:
            try:
                with open(llm_params_file, 'w', encoding='utf-8') as f:
                    json.dump(current_params, f, indent=2)
                st.success("✅ Ayarlar kaydedildi!")
            except Exception as e:
                st.error(f"❌ Kaydetme hatası: {e}")
    
    # Yanıt üret butonu
    if st.button("🚀 Yanıt Üret", type="primary"):
        if original_text and custom_input:
            with st.spinner("Yanıt üretiliyor..."):
                # Request oluştur
                request_id = create_request(original_text, response_type)
                
                if request_id:
                    # Değişkenleri session_state'e kaydet
                    st.session_state.last_custom_input = custom_input
                    st.session_state.last_citizen_name = citizen_name
                    st.session_state.last_temperature = temperature
                    st.session_state.last_top_p = top_p
                    st.session_state.last_repetition_penalty = repetition_penalty
                    
                    # Yanıt üret
                    response_data = generate_response(
                        request_id, custom_input, citizen_name, 
                        temperature, top_p, repetition_penalty
                    )
                    
                    if response_data:
                        st.session_state.current_response = response_data
                        st.session_state.responses.append(response_data)
                        st.session_state.generated_response = response_data
                        st.success("✅ Yanıt başarıyla üretildi!")
                        st.rerun()
                    else:
                        st.error("❌ Yanıt üretilemedi")
                else:
                    st.error("❌ Request oluşturulamadı")
        else:
            st.warning("⚠️ Lütfen gerekli alanları doldurun")

if __name__ == "__main__":
    main() 