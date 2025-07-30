import streamlit as st
import requests
import json
from datetime import datetime

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="AI Helper",
    page_icon="🤖",
    layout="centered"
)

# CSS stilleri - toolbar'ı eski haline getir
st.markdown("""
<style>
    .main {
        max-width: 800px;
        margin: 0 auto;
    }
    .stTextArea {
        font-size: 16px;
    }
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 18px;
    }
    .response-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .stats-container {
        display: flex;
        justify-content: space-between;
        margin-top: 20px;
        padding-top: 15px;
        border-top: 1px solid #ddd;
    }
    .stat-item {
        text-align: center;
        flex: 1;
    }
    
    /* Debug paneli stilleri */
    .debug-panel {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Başlık
st.title("🤖 AI Helper")
st.markdown("**Vatandaş taleplerine cevaplarınızı hazırlayın**")
st.caption("İstek ve önerilere uygun, resmi ve anlaşılır cevaplar oluşturun")

# Backend URL
BACKEND_URL = "http://localhost:3200/api/v1"

# Debug paneli
with st.expander("🔧 Debug Paneli", expanded=False):
    st.write("**Backend Durumu:**")
    try:
        response = requests.get(f"{BACKEND_URL.replace('/api/v1', '')}")
        st.success(f"✅ Backend çalışıyor: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Backend hatası: {e}")
    
    st.write("**Modeller:**")
    try:
        models_response = requests.get(f"{BACKEND_URL}/models")
        if models_response.status_code == 200:
            models = models_response.json()
            st.success(f"✅ {len(models)} model yüklendi")
            for model in models[:3]:  # İlk 3 modeli göster
                st.write(f"- {model['name']}")
        else:
            st.error(f"❌ Modeller yüklenemedi: {models_response.status_code}")
    except Exception as e:
        st.error(f"❌ Model hatası: {e}")
    
    st.write("**Son Hata:**")
    if 'last_error' in st.session_state:
        st.error(st.session_state.last_error)
    else:
        st.info("Henüz hata yok")

# Modelleri getir
@st.cache_data(ttl=300)  # 5 dakika cache
def get_models():
    try:
        response = requests.get(f"{BACKEND_URL}/models")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Modeller yüklenemedi")
            return []
    except Exception as e:
        st.error(f"Backend bağlantı hatası: {e}")
        return []

# Ana fonksiyon
def main():
    # Modelleri al
    models = get_models()
    
    st.header("📝 Vatandaş Talebi ve Cevap Hazırlama")
    
    # Ad Soyad girişi
    col1, col2 = st.columns(2)
    with col1:
        citizen_name = st.text_input(
            "Vatandaşın Adı Soyadı:",
            placeholder="Adı Soyadı (boş bırakılırsa 'Değerli Vatandaşımız' kullanılır)"
        )
    
    with col2:
        # Geri dönüş tipi
        response_type = st.selectbox(
            "Geri Dönüş Tipi:",
            ["positive", "negative", "informative", "other"],
            format_func=lambda x: {
                "positive": "Pozitif",
                "negative": "Negatif", 
                "informative": "Bilgilendirici",
                "other": "Diğer"
            }[x]
        )
    
    # Model seçimi
    if models:
        model_names = [model["name"] for model in models]
        selected_model = st.selectbox(
            "Model:",
            model_names,
            format_func=lambda x: next((m["display_name"] for m in models if m["name"] == x), x)
        )
    else:
        selected_model = st.selectbox(
            "Model:",
            ["llama3:latest", "mistral:latest", "gemma:latest"],
            disabled=True
        )
    
    # Sistem promptu düzenlenebilir alan
    st.subheader("🔧 Sistem Promptu (Debug)")
    default_system_prompt = """Sen Bursa Nilüfer Belediyesi çalışanısın. Vatandaşlara resmi, kibar ve anlaşılır yanıtlar veriyorsun.
Sen Bursa Nilüfer Belediyesi'nde çalışan bir memursun.

Görevin, vatandaşlardan gelen talepleri dikkatle okuyarak onlara resmi, anlaşılır, kibar ve Türkçe bir dille yazılı yanıtlar oluşturmaktır.

Yanıtın yapısı şu şekilde olmalıdır:
1. "Sayın Ad Soyad," ifadesiyle başlamalıdır. Eğer ad girilmemişse "Değerli vatandaşımız," olarak başlamalıdır.
2. Vatandaşın ilettiği konuyu resmi bir şekilde özetlemelisin.
3. Personelin hazırladığı cevabı daha uygun, nezaketli ve açıklayıcı bir dile dönüştürmelisin.
4. Geri dönüş tipi (olumlu, olumsuz, bilgilendirici vb.) ifadesine göre tonlama yapmalısın.
5. Metni "Saygılarımızla, Bursa Nilüfer Belediyesi" ifadesiyle bitirmelisin."""

    # Kaydedilmiş prompt dosyasını kontrol et
    import os
    prompt_file = "saved_system_prompt.txt"
    
    # Session state'den sistem promptunu al veya dosyadan oku
    if 'system_prompt' not in st.session_state:
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    st.session_state.system_prompt = f.read()
            except:
                st.session_state.system_prompt = default_system_prompt
        else:
            st.session_state.system_prompt = default_system_prompt

    system_prompt = st.text_area(
        "Sistem Promptu (LLM'e gönderilen talimat):",
        value=st.session_state.system_prompt,
        height=100,
        help="Bu prompt LLM'e gönderilir. Değiştirerek farklı yanıt stilleri deneyebilirsiniz. Ctrl+Enter ile kaydedin."
    )
    
    # Prompt değiştiğinde session state'i ve dosyayı güncelle
    if system_prompt != st.session_state.system_prompt:
        st.session_state.system_prompt = system_prompt
        try:
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(system_prompt)
            st.success("✅ Sistem promptu kalıcı olarak kaydedildi!")
        except Exception as e:
            st.error(f"❌ Kaydetme hatası: {e}")
    
    # LLM Ayar Slider'ları
    with st.expander("🎚️ Yanıt Ayarları", expanded=False):
        st.subheader("LLM Parametreleri")
        
        # LLM parametrelerini kaydetme dosyası
        llm_params_file = "saved_llm_params.json"
        
        # Varsayılan değerler
        default_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.2
        }
        
        # Kaydedilmiş parametreleri yükle
        import json
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
        
        col_temp, col_top, col_rep = st.columns(3)
        
        with col_temp:
            temperature = st.slider(
                "🔥 Temperature",
                min_value=0.1,
                max_value=1.5,
                value=saved_params["temperature"],
                step=0.1,
                help="Yaratıcılık seviyesi. Düşük değerler daha tutarlı, yüksek değerler daha yaratıcı yanıtlar üretir."
            )
        
        with col_top:
            top_p = st.slider(
                "🎯 Top-p",
                min_value=0.1,
                max_value=1.0,
                value=saved_params["top_p"],
                step=0.05,
                help="Kelime seçimi çeşitliliği. Düşük değerler daha odaklı, yüksek değerler daha çeşitli yanıtlar üretir."
            )
        
        with col_rep:
            repetition_penalty = st.slider(
                "🚫 Repetition Penalty",
                min_value=1.0,
                max_value=2.0,
                value=saved_params["repetition_penalty"],
                step=0.1,
                help="Tekrar cezası. Yüksek değerler tekrarları azaltır."
            )
        
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
                st.success("✅ LLM parametreleri kalıcı olarak kaydedildi!")
            except Exception as e:
                st.error(f"❌ Parametre kaydetme hatası: {e}")
    
    # İki sütunlu layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Gelen İstek/Öneri")
        
        # Debug için varsayılan değer
        default_citizen_request = """Bursa Nilüfer'de bir dükkanım var ve yönetim planından tahsisli otoparkımda bulunan dubaları, belediye ekipleri mafyavari şekilde tahsisli alanımdan alıp götürebiliyor. Geri aradığımda ise belediye zabıtası, görevliyi mahkemeye vermemi söylüyor. Bu nasıl bir hizmet anlayışı? Benim tahsisli alanımdan eşyamı alıyorsunuz, buna ne denir? Herkes biliyordur. Bir yeri koruduğunu zannedip başka bir yeri mağdur etmek mi belediyecilik?"""
        
        # Vatandaş isteği metni
        citizen_request = st.text_area(
            "Gelen istek/öneri metnini buraya yapıştırın:",
            value=default_citizen_request,
            height=200,
            placeholder="Vatandaşın gönderdiği şikayet, istek veya öneri metnini buraya yapıştırın..."
        )
    
    with col2:
        st.subheader("✍️ Hazırladığınız Cevap")
        
        # Debug için varsayılan değer
        default_prepared_response = """Orası size tahsis edilmiş bir yer değil. Nilüfer halkının ortak kullanım alanı. Kaldırımlar da öyle."""
        
        # Kendi hazırladığı cevap
        prepared_response = st.text_area(
            "Hazırladığınız cevabı buraya yazın:",
            value=default_prepared_response,
            height=200,
            placeholder="Vatandaşa vereceğiniz cevabı buraya yazın..."
        )
    
    # Yanıt üret butonu
    if st.button("🤖 Yanıt Üret", type="primary", use_container_width=True):
        if not citizen_request.strip():
            st.error("Lütfen vatandaşın istek/öneri metnini girin")
        elif not prepared_response.strip():
            st.error("Lütfen hazırladığınız cevabı girin")
        else:
            with st.spinner("Yanıt üretiliyor..."):
                try:
                    # Prompt oluştur - Sistem promptu backend'de dinamik olarak oluşturulacak
                    prompt = f"""VATANDAŞ BİLGİLERİ:
- Vatandaşın isteği/önerisi: {citizen_request}

PERSONEL CEVABI:
- Hazırladığınız cevabı: {prepared_response}

DİĞER BİLGİLER:
- Geri dönüş tipi: {response_type}

Lütfen bu bilgileri kullanarak resmi, kibar ve anlaşılır bir yanıt oluşturun. 
Yanıt Türkçe olarak, resmi bir dille yazılmalı ve "Saygılarımızla, Bursa Nilüfer Belediyesi" ile bitmelidir."""
                    
                    # Debug için prompt'u göster
                    with st.expander("🔍 Gönderilen Prompt", expanded=False):
                        st.code(prompt, language="text")
                    
                    # İstek oluştur
                    request_data = {
                        "original_text": f"Vatandaş İsteği: {citizen_request}\n\nHazırlanan Cevap: {prepared_response}",
                        "response_type": response_type
                    }
                    
                    # Debug için request data'yı göster
                    with st.expander("📤 Gönderilen Request Data", expanded=False):
                        st.json(request_data)
                    
                    request_response = requests.post(f"{BACKEND_URL}/requests", json=request_data)
                    
                    if request_response.status_code == 200:
                        request_id = request_response.json()["id"]
                        st.success(f"✅ İstek oluşturuldu (ID: {request_id})")
                        
                        # Yanıt üret
                        generate_data = {
                            "request_id": request_id,
                            "model_name": selected_model,
                            "custom_input": prompt,
                            "citizen_name": citizen_name.strip() if citizen_name else None,
                            "temperature": temperature,
                            "top_p": top_p,
                            "repetition_penalty": repetition_penalty
                        }
                        
                        # Debug: citizen_name kontrolü
                        st.write(f"🔍 DEBUG: citizen_name = '{citizen_name}'")
                        st.write(f"🔍 DEBUG: citizen_name.strip() = '{citizen_name.strip() if citizen_name else 'None'}'")
                        st.write(f"🔍 DEBUG: generate_data['citizen_name'] = '{generate_data['citizen_name']}'")
                        
                        # Debug için generate data'yı göster
                        with st.expander("🤖 Gönderilen Generate Data", expanded=False):
                            st.json(generate_data)
                        
                        generate_response = requests.post(f"{BACKEND_URL}/generate", json=generate_data)
                        
                        # Debug için response'u göster
                        with st.expander("📥 Gelen Response", expanded=False):
                            st.write(f"Status Code: {generate_response.status_code}")
                            st.write(f"Response Text: {generate_response.text}")
                        
                        if generate_response.status_code == 200:
                            response_data = generate_response.json()
                            st.session_state.ai_response = response_data
                            st.success("Yanıt başarıyla üretildi!")
                            st.session_state.last_error = None
                        else:
                            error_msg = f"Yanıt üretilirken hata oluştu: {generate_response.status_code} - {generate_response.text}"
                            st.error(error_msg)
                            st.session_state.last_error = error_msg
                    else:
                        error_msg = f"İstek oluşturulurken hata oluştu: {request_response.status_code} - {request_response.text}"
                        st.error(error_msg)
                        st.session_state.last_error = error_msg
                except Exception as e:
                    error_msg = f"Hata: {e}"
                    st.error(error_msg)
                    st.session_state.last_error = error_msg
    
    # Yanıtları göster
    st.markdown("---")
    
    # AI Yanıtı
    if hasattr(st.session_state, 'ai_response') and st.session_state.ai_response:
        st.header("🤖 Oluşturulan Yanıt")
        
        response_data = st.session_state.ai_response
        
        # Yanıt metni
        st.markdown(f"""
        <div class="response-box">
            {response_data['response_text']}
        </div>
        """, unsafe_allow_html=True)
        
        # İstatistikler
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Süre", f"{response_data['latency_ms']:.0f}ms")
        with col2:
            st.metric("Model", response_data['model_name'])
        with col3:
            st.metric("Karakter", len(response_data['response_text']))
        with col4:
            created_at = datetime.fromisoformat(response_data['created_at'].replace('Z', '+00:00'))
            st.metric("Tarih", created_at.strftime("%d.%m.%Y"))
        
        # Butonlar
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Kopyala", use_container_width=True):
                st.write("Kopyalandı!")
        with col2:
            if st.button("✅ Seç", use_container_width=True):
                st.write("Seçildi!")
        with col3:
            if st.button("🔄 Alternatif", use_container_width=True):
                st.rerun()

if __name__ == "__main__":
    main() 