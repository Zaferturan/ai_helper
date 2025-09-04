import streamlit as st
import requests
import json
import os
from datetime import datetime
import urllib.parse
import time
import pyperclip

# Backend URL - Lokalde test için localhost kullan
BACKEND_URL = "http://localhost:8000/api/v1"

# Debug için localhost'u da destekle
if os.getenv("DEBUG_MODE") == "true":
    BACKEND_URL = "http://localhost:8000/api/v1"

# Müdürlük listesi
DEPARTMENTS = [
    "Özel Kalem Müdürlüğü",
    "Afet İşleri Müdürlüğü",
    "Basın ve Yayın Müdürlüğü",
    "Belediye Tiyatro Müdürlüğü",
    "Bilgi İşlem Müdürlüğü",
    "Destek Hizmetleri Müdürlüğü",
    "Emlak ve İstimlak Müdürlüğü",
    "Fen İşleri Müdürlüğü",
    "Gençlik ve Spor Hizmetleri Müdürlüğü",
    "Halkla İlişkiler Müdürlüğü",
    "Hukuk İşleri Müdürlüğü",
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü",
    "İmar ve Şehircilik Müdürlüğü",
    "İnsan Kaynakları ve Eğitim Müdürlüğü",
    "Kentsel Tasarım Müdürlüğü",
    "Kırsal Hizmetler Müdürlüğü",
    "Kültür ve Sosyal İşler Müdürlüğü",
    "Kütüphane Müdürlüğü",
    "Makine İkmal ve Bakım Onarım Müdürlüğü",
    "Mali Hizmetler Müdürlüğü",
    "Park ve Bahçeler Müdürlüğü",
    "Plan ve Proje Müdürlüğü",
    "Ruhsat ve Denetim Müdürlüğü",
    "Sosyal Destek Hizmetleri Müdürlüğü",
    "Strateji Geliştirme Müdürlüğü",
    "Teftiş Kurulu Müdürlüğü",
    "Temizlik İşleri Müdürlüğü",
    "Ulaşım Hizmetleri Müdürlüğü",
    "Veteriner İşleri Müdürlüğü",
    "Yapı Kontrol Müdürlüğü",
    "Yazı İşleri Müdürlüğü",
    "Zabıta Müdürlüğü",
    "Koordinasyon İşleri Müdürlüğü"
]

# Authentication fonksiyonları
def check_authentication():
    """Kullanıcının authentication durumunu kontrol et"""
    # URL'den token parametresini kontrol et
    query_params = st.query_params
    if 'token' in query_params:
        token = query_params['token']
        
        # Token'ı backend'e gönderip doğrula
        try:
            response = requests.post(
                f"{BACKEND_URL}/auth/consume-token",
                json={"code": token},  # code field'ını token olarak kullan
                timeout=30
            )
            if response.status_code == 200:
                user_data = response.json()
                
                # Session state'i set et
                st.session_state.authenticated = True
                st.session_state.access_token = user_data["access_token"]
                st.session_state.user_email = user_data["email"]
                st.session_state.user_full_name = user_data.get("full_name", "")
                st.session_state.user_department = user_data.get("department", "")
                st.session_state.profile_completed = user_data.get("profile_completed", False)
                
                # localStorage'a token'ı kaydet
                st.markdown(f"""
                <script>
                localStorage.setItem('ai_helper_token', '{user_data["access_token"]}');
                </script>
                """, unsafe_allow_html=True)
                
                # URL'den token'ı temizle
                st.query_params.clear()
                return True
            else:
                st.error("Geçersiz veya süresi dolmuş bağlantı")
                st.session_state.authenticated = False
                st.session_state.access_token = None
                return False
        except Exception as e:
            st.error(f"Token doğrulanamadı: {str(e)}")
            st.session_state.authenticated = False
            st.session_state.access_token = None
            return False
    
    # Session state kontrolü - daha kalıcı hale getir
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    
    # Eğer session state'de authentication bilgisi varsa, önce onu kontrol et
    if st.session_state.authenticated and st.session_state.access_token:
        # Kullanıcı bilgilerini güncelle
        try:
            response = requests.get(
                f"{BACKEND_URL}/auth/profile",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                timeout=30
            )
            if response.status_code == 200:
                user_data = response.json()
                st.session_state.user_email = user_data["email"]
                st.session_state.user_full_name = user_data.get("full_name", "")
                st.session_state.user_department = user_data.get("department", "")
                st.session_state.profile_completed = user_data.get("profile_completed", False)
                return True
            elif response.status_code == 401:
                # Token süresi dolmuş - session state'i temizle
                st.session_state.authenticated = False
                st.session_state.access_token = None
                st.session_state.user_email = None
                st.session_state.user_full_name = None
                st.session_state.user_department = None
                st.session_state.profile_completed = None
                return False
        except Exception as e:
            # Bağlantı hatası - session state'i temizle
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.user_email = None
            st.session_state.user_full_name = None
            st.session_state.user_department = None
            st.session_state.profile_completed = None
            return False
    
    # localStorage'dan token'ı oku (eğer session state'de yoksa)
    # Not: JavaScript ile localStorage okumak Streamlit'te karmaşık
    # Bu yüzden session state'i daha kalıcı hale getiriyoruz
    
    # Eğer authenticated ise, her zaman backend'e profil isteği gönder (token süresi kontrolü için)
    if st.session_state.authenticated and st.session_state.access_token:
        try:
            response = requests.get(
                f"{BACKEND_URL}/auth/profile",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                timeout=30
            )
            if response.status_code == 200:
                user_data = response.json()
                st.session_state.user_email = user_data["email"]
                st.session_state.user_full_name = user_data.get("full_name", "")
                st.session_state.user_department = user_data.get("department", "")
                st.session_state.profile_completed = user_data.get("profile_completed", False)
            elif response.status_code == 401:
                # Token süresi dolmuş - session state'i temizle
                st.session_state.authenticated = False
                st.session_state.access_token = None
                st.session_state.user_email = None
                st.session_state.user_full_name = None
                st.session_state.user_department = None
                st.session_state.profile_completed = None
                return False
        except Exception as e:
            # Bağlantı hatası - session state'i temizle
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.user_email = None
            st.session_state.user_full_name = None
            st.session_state.user_department = None
            st.session_state.profile_completed = None
            return False
    
    return st.session_state.authenticated

def login_page():
    """Login sayfasını göster - Giriş için gerekli link ve kodu gönder"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🔐 AI Helper - Giriş</h1>
        <p>Bursa Nilüfer Belediyesi AI Yardımcı sistemine hoş geldiniz</p>
        <p style="color: #666; font-size: 14px;">E-posta adresinizi girin, giriş için gerekli link ve kodu gönderelim</p>
    </div>
    """, unsafe_allow_html=True)
    
    # E-posta geçmişi butonları
    if st.session_state.get('email_history'):
        st.write("**Son kullanılan e-posta adresleri:**")
        cols = st.columns(3)
        for i, email in enumerate(st.session_state.email_history[:6]):  # En fazla 6 tane göster
            col_idx = i % 3
            if cols[col_idx].button(email, key=f"hist_{i}", use_container_width=True):
                st.session_state.email_input = email
                st.rerun()
    
    with st.form("login_form"):
        email = st.text_input(
            "E-posta Adresi", 
            placeholder="ornek@nilufer.bel.tr",
            key="email_input",
            value=st.session_state.get("email_input", "")
        )
        
        submitted = st.form_submit_button("📧 Bağlantı ve Kod Gönder")
        
        if submitted:
            if not email:
                st.error("E-posta adresi gerekli!")
                return
            
            if not email.endswith("@nilufer.bel.tr"):
                st.error("Sadece @nilufer.bel.tr alan adına sahip e-posta adresleri kullanılabilir!")
                return
            
            # Giriş bilgilerini gönder
            try:
                with st.spinner("🔄 Giriş bilgileri gönderiliyor..."):
                    response = requests.post(
                        f"{BACKEND_URL}/auth/send",
                        json={"email": email},
                        timeout=30
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # E-posta geçmişine ekle (en fazla 10 tane)
                    if email not in st.session_state.email_history:
                        st.session_state.email_history.insert(0, email)
                        if len(st.session_state.email_history) > 10:
                            st.session_state.email_history = st.session_state.email_history[:10]
                    
                    # Gönderim sonrası ekranı göster
                    st.session_state.login_sent = True
                    st.session_state.login_email = email
                    st.session_state.login_sent_time = datetime.now()
                    st.rerun()
                                
                else:
                    error_data = response.json()
                    st.error(f"❌ Hata: {error_data.get('detail', 'Bilinmeyen hata')}")
                    
            except Exception as e:
                st.error(f"❌ Bağlantı hatası: {str(e)}")
                st.info("Backend servisine bağlanılamıyor. Lütfen daha sonra tekrar deneyin.")


def login_sent_page():
    """Giriş bilgileri gönderildikten sonraki ekran"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>📧 Giriş için gerekli link ve kodu gönderdik</h1>
        <p>E-postandaki bağlantıya tıkla ya da aşağıya 6 haneli giriş kodunu yaz</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Kod giriş alanı
    with st.form("code_form"):
        code = st.text_input(
            "6 Haneli Giriş Kodu",
            placeholder="000000",
            max_chars=6,
            key="code_input"
        )
        
        verify_submitted = st.form_submit_button("✅ Doğrula", use_container_width=True)
        
        if verify_submitted:
            if not code or len(code) != 6:
                st.error("6 haneli kod gerekli!")
                return
            
            # Kodu doğrula
            try:
                with st.spinner("🔄 Kod doğrulanıyor..."):
                    response = requests.post(
                        f"{BACKEND_URL}/auth/verify-code",
                        json={"email": st.session_state.login_email, "code": code},
                        timeout=30
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Session state'i set et
                    st.session_state.authenticated = True
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user_email = data["email"]
                    st.session_state.user_full_name = data.get("full_name", "")
                    st.session_state.user_department = data.get("department", "")
                    st.session_state.profile_completed = data["profile_completed"]
                    
                    # Login state'leri temizle
                    st.session_state.login_sent = False
                    st.session_state.login_email = None
                    st.session_state.login_sent_time = None
                    
                    st.success("✅ Giriş başarılı!")
                    st.rerun()
                    
                else:
                    error_data = response.json()
                    st.error(f"❌ Hata: {error_data.get('detail', 'Bilinmeyen hata')}")
                    
            except Exception as e:
                st.error(f"❌ Bağlantı hatası: {str(e)}")
    
    # Tekrar gönder butonu (30 saniye cooldown)
    if st.session_state.login_sent_time:
        elapsed = (datetime.now() - st.session_state.login_sent_time).total_seconds()
        if elapsed < 30:
            remaining = int(30 - elapsed)
            st.button(f"⏳ Tekrar gönder ({remaining:02d})", disabled=True, use_container_width=True)
        else:
            if st.button("📧 Tekrar gönder", use_container_width=True):
                # Tekrar gönder
                try:
                    with st.spinner("🔄 Giriş bilgileri tekrar gönderiliyor..."):
                        response = requests.post(
                            f"{BACKEND_URL}/auth/send",
                            json={"email": st.session_state.login_email},
                            timeout=30
                        )
                    
                    if response.status_code == 200:
                        st.session_state.login_sent_time = datetime.now()
                        st.success("✅ Giriş bilgileri tekrar gönderildi!")
                        st.rerun()
                    else:
                        error_data = response.json()
                        st.error(f"❌ Hata: {error_data.get('detail', 'Bilinmeyen hata')}")
                        
                except Exception as e:
                    st.error(f"❌ Bağlantı hatası: {str(e)}")
    
    # Geri dön butonu
    if st.button("⬅️ Geri Dön", use_container_width=True):
        st.session_state.login_sent = False
        st.session_state.login_email = None
        st.session_state.login_sent_time = None
        st.rerun()


def profile_completion_page():
    """Profil tamamlama sayfası"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>👤 Profil Bilgilerini Tamamlayın</h1>
        <p>Lütfen aşağıdaki bilgileri doldurun</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("profile_form"):
        full_name = st.text_input("Ad Soyad", placeholder="Adınız Soyadınız")
        department = st.selectbox("Müdürlük", DEPARTMENTS, placeholder="Müdürlüğünüzü seçin")
        
        submitted = st.form_submit_button("✅ Profili Tamamla")
        
        if submitted:
            if not full_name or not department:
                st.error("Lütfen tüm alanları doldurun!")
                return
            
            try:
                with st.spinner("🔄 Profil güncelleniyor..."):
                    # Profil bilgilerini backend'e gönder
                    response = requests.post(
                        f"{BACKEND_URL}/auth/complete-profile",
                        json={"full_name": full_name, "department": department},
                        headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                        timeout=30
                    )
                
                if response.status_code == 200:
                    st.session_state.user_full_name = full_name
                    st.session_state.user_department = department
                    st.session_state.profile_completed = True
                    st.success("✅ Profil başarıyla tamamlandı!")
                    st.rerun()
                else:
                    error_data = response.json()
                    st.error(f"❌ Hata: {error_data.get('detail', 'Bilinmeyen hata')}")
                    
            except Exception as e:
                st.error(f"❌ Bağlantı hatası: {str(e)}")

def logout():
    """Kullanıcıyı çıkış yaptır"""
    # localStorage'dan token'ı temizle
    st.markdown("""
    <script>
    localStorage.removeItem('ai_helper_token');
    </script>
    """, unsafe_allow_html=True)
    
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.access_token = None
    st.session_state.user_full_name = None
    st.session_state.user_department = None
    st.session_state.profile_completed = None
    st.rerun()

def verify_page():
    """Token doğrulama sayfası"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1 style="color: #2c5aa0; margin-bottom: 1rem;">
            🔐 Giriş Linki Doğrulanıyor
        </h1>
        <p style="color: #666; font-size: 18px;">
            Giriş bağlantınız doğrulanıyor, lütfen bekleyin...
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # URL'den token parametresini al
    query_params = st.query_params
    if 'token' in query_params:
        token = query_params['token']
        
        # Loading spinner göster
        with st.spinner("Token doğrulanıyor..."):
            try:
                # Backend API'sine token doğrulama isteği gönder (POST method)
                response = requests.post(
                    f"{BACKEND_URL}/auth/consume-token",
                    json={"code": token},
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Başarılı - response'dan JWT token'ı al
                    response_data = response.json()
                    
                    # Session state'i set et
                    st.session_state.authenticated = True
                    st.session_state.access_token = response_data["access_token"]
                    st.session_state.user_email = response_data["email"]
                    st.session_state.user_full_name = response_data.get("full_name", "")
                    st.session_state.user_department = response_data.get("department", "")
                    st.session_state.profile_completed = response_data["profile_completed"]
                    
                    # URL'den token'ı temizle
                    st.query_params.clear()
                    
                    st.success("✅ Giriş başarılı! Yönlendiriliyorsunuz...")
                    
                    # Dashboard'a yönlendir
                    st.rerun()
                    
                else:
                    # Hata - login sayfasına yönlendir
                    st.error("❌ Geçersiz veya süresi dolmuş bağlantı")
                    st.info("Lütfen tekrar giriş linki isteyin")
                    
                    # 3 saniye sonra login sayfasına yönlendir
                    time.sleep(3)
                    st.session_state.authenticated = False
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Doğrulama hatası: {str(e)}")
                st.info("Lütfen tekrar giriş linki isteyin")
                
                # 3 saniye sonra login sayfasına yönlendir
                time.sleep(3)
                st.session_state.authenticated = False
                st.rerun()
    else:
        st.error("❌ Token bulunamadı")
        st.info("Lütfen e-postanızdaki giriş linkini kullanın")
        
        # 3 saniye sonra login sayfasına yönlendir
        time.sleep(3)
        st.session_state.authenticated = False
        st.rerun()

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="AI Helper - Bursa Nilüfer Belediyesi",
    page_icon="icon.ico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS stilleri - Buton renkleri ve gelişmiş gölgeler
st.markdown("""
<style>
    /* Ana buton stilleri - Güçlü gölge */
    .stButton > button {
        width: 100%;
        margin-top: 1rem;
        background-color: #50c2eb !important;
        border-color: #50c2eb !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.05) !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }
    
    .stButton > button:hover {
        background-color: #3ba8d1 !important;
        border-color: #3ba8d1 !important;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15), 0 4px 8px rgba(0,0,0,0.1) !important;
        transform: translateY(-2px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Text input - Orta gölge + renkli gölge */
    .stTextInput > div > div > input {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1), 0 2px 4px rgba(52, 152, 219, 0.1) !important;
        border-radius: 8px !important;
        border: 2px solid #e0e0e0 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        box-shadow: 0 4px 8px rgba(52, 152, 219, 0.2), 0 2px 4px rgba(0,0,0,0.05) !important;
        border-color: #50c2eb !important;
        transform: translateY(-1px) !important;
    }
    
    /* Text area - Güçlü gölge + renkli gölge */
    .stTextArea textarea {
        box-shadow: 0 6px 12px rgba(0,0,0,0.1), 0 2px 4px rgba(52, 152, 219, 0.1) !important;
        border-radius: 8px !important;
        padding: 16px !important;
        border: 2px solid #e0e0e0 !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus {
        box-shadow: 0 8px 16px rgba(52, 152, 219, 0.15), 0 4px 8px rgba(0,0,0,0.1) !important;
        border-color: #50c2eb !important;
        transform: translateY(-1px) !important;
    }
    
    /* Selectbox - Orta gölge */
    .stSelectbox > div > div > div {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.05) !important;
        border-radius: 8px !important;
        border: 2px solid #e0e0e0 !important;
        transition: all 0.3s ease !important;
    }
    
    .stSelectbox > div > div > div:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.15), 0 2px 4px rgba(52, 152, 219, 0.1) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Slider - Yumuşak gölge */
    .stSlider > div > div > div {
        box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 1px 2px rgba(52, 152, 219, 0.1) !important;
        border-radius: 6px !important;
    }
    
    /* Expander - Güçlü gölge */
    .stExpander {
        box-shadow: 0 6px 12px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.05) !important;
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    /* Response kartları - Çoklu gölge */
    .response-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 4px 8px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
    }
    
    .response-card:hover {
        box-shadow: 0 8px 16px rgba(0,0,0,0.15), 0 4px 8px rgba(52, 152, 219, 0.1) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Form container - Yumuşak gölge */
    .stForm {
        box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.02) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        background: rgba(255, 255, 255, 0.95) !important;
    }
    
    /* Info/Success/Error boxes - Renkli gölge */
    .stAlert {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1), 0 2px 4px rgba(52, 152, 219, 0.1) !important;
        border-radius: 8px !important;
        border: none !important;
    }
    
    /* Sidebar - Yumuşak gölge */
    .css-1d391kg {
        box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.02) !important;
    }
</style>
""", unsafe_allow_html=True)

# Müdürlük listesi

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

def create_request(original_text, is_new_request=False):
    """Create a new request"""
    try:
        data = {
            "original_text": original_text,
            "response_type": "informative",  # Sabit değer
            "is_new_request": is_new_request  # Yeni istek öneri mi?
        }
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = requests.post(f"{BACKEND_URL}/requests", json=data, headers=headers)
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

def mark_request_as_copied(request_id):
    """Mark request as processed"""
    try:
        url = f"{BACKEND_URL}/requests/{request_id}"
        response = requests.put(url)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Request işaretlenemedi: {e}")
        return False

def mark_response_as_copied(response_id):
    """Mark response as copied (has_been_copied=True)"""
    try:
        url = f"{BACKEND_URL}/responses/{response_id}/mark-copied"
        response = requests.put(url)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Response kopyalandı olarak işaretlenemedi: {e}")
        return False

# Ana uygulama
def main():
    # Session state'i initialize et
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'responses' not in st.session_state:
        st.session_state.responses = []
    if 'current_response' not in st.session_state:
        st.session_state.current_response = None
    if 'generated_response' not in st.session_state:
        st.session_state.generated_response = None
    if 'is_generating' not in st.session_state:
        st.session_state.is_generating = False
    if 'last_model_name' not in st.session_state:
        st.session_state.last_model_name = 'gemini-2.5-flash'
    if 'original_text_input' not in st.session_state:
        st.session_state.original_text_input = ""
    if 'custom_input_text' not in st.session_state:
        st.session_state.custom_input_text = ""
    if 'current_request_id' not in st.session_state:
        st.session_state.current_request_id = 0
    if 'user_department' not in st.session_state:
        st.session_state.user_department = ""
    if 'user_full_name' not in st.session_state:
        st.session_state.user_full_name = ""
    if 'user_email' not in st.session_state:
        st.session_state.user_email = ""
    if 'profile_completed' not in st.session_state:
        st.session_state.profile_completed = None
    if 'show_admin_panel' not in st.session_state:
        st.session_state.show_admin_panel = False
    
    # Durum makinesi için yeni state'ler
    if 'state' not in st.session_state:
        st.session_state.state = "draft"  # "draft" veya "finalized"
    if 'has_copied' not in st.session_state:
        st.session_state.has_copied = False
    if 'yanit_sayisi' not in st.session_state:
        st.session_state.yanit_sayisi = 0  # Her istek için üretilen yanıt sayısı
    
    # E-posta geçmişi için session state
    if 'email_history' not in st.session_state:
        st.session_state.email_history = []
    

    
    # Eğer zaferturan@nilufer.bel.tr ise müdürlük bilgisini manuel olarak set et
    if st.session_state.get('user_email') == "zaferturan@nilufer.bel.tr" and not st.session_state.get('user_department'):
        st.session_state.user_department = "Bilgi İşlem Müdürlüğü"
        st.session_state.user_full_name = "zafer turan"
    
    # Eğer engin akyıldız ise müdürlük bilgisini manuel olarak set et
    if st.session_state.get('user_email') == "enginakyildiz@nilufer.bel.tr" and not st.session_state.get('user_department'):
        st.session_state.user_department = "Bilgi İşlem Müdürlüğü"
        st.session_state.user_full_name = "engin akyıldız"
    
    # Verify sayfası kontrolü - giriş linki için
    query_params = st.query_params
    if 'token' in query_params:
        verify_page()
        return
    
    # Authentication kontrolü - her sayfa yenilendiğinde token kontrolü
    if not check_authentication():
        # Login sent page kontrolü
        if st.session_state.get("login_sent", False):
            login_sent_page()
            return
        
        login_page()
        return
    
    # Token süresi kontrolü artık check_authentication() içinde yapılıyor
    # Burada ekstra kontrol yapmaya gerek yok
    
    # Profil tamamlama kontrolü
    if st.session_state.get('profile_completed') is False:
        profile_completion_page()
        return
    
    # Kullanıcı bilgileri ve butonlar
    col_user, col_buttons = st.columns([3, 1])
    with col_user:
        # Sadece kullanıcı bilgileri mavi kutu içinde
        user_department = st.session_state.get('user_department', '')
        if user_department:
            st.info(f"👤 {st.session_state.user_full_name} - {user_department}")
        else:
            st.info(f"👤 {st.session_state.user_full_name}")
    
    with col_buttons:
        # Admin ve çıkış butonları yan yana
        col_admin, col_logout = st.columns(2)
        with col_admin:
            if st.session_state.get('user_email') == "zaferturan@nilufer.bel.tr":
                if st.button("📊 İstatistikler", type="secondary", use_container_width=True):
                    st.session_state.show_admin_panel = True
                    st.rerun()
        with col_logout:
            if st.button("🚪 Çıkış Yap"):
                logout()
                return

    # Admin Paneli - sadece admin kullanıcılar görebilir
    if st.session_state.get('show_admin_panel', False) and st.session_state.get('user_email') == "zaferturan@nilufer.bel.tr":
        from admin_panel import show_admin_panel
        show_admin_panel()


    
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
    if 'is_generating' not in st.session_state:
        st.session_state.is_generating = False
    
    # Model seçimini her seferinde varsayılan yap
    if 'last_model_name' in st.session_state:
        del st.session_state.last_model_name
    
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
    
    # Varsayılan değerler - tüm kullanıcılar için
    selected_model = "gemini-2.5-flash"  # Varsayılan model
    temperature = 0.5  # Varsayılan temperature
    top_p = 0.4  # Varsayılan top_p
    repetition_penalty = 2.0  # Varsayılan repetition_penalty
    
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
        
        # İstek metni değişiklik kontrolü

        
        # Hazırladığınız cevap
        st.subheader("✍️ Hazırladığınız Cevap")
        custom_input = st.text_area(
            "Hazırladığınız cevap taslağını buraya yazın:",
            value="Orası size tahsis edilmiş bir yer değil. Nilüfer halkının ortak kullanım alanı. Kaldırımlar da öyle.",
            height=100
        )
        
        # Yanıt ayarları - sadece admin'ler görebilir
        if st.session_state.get('user_email') == "zaferturan@nilufer.bel.tr":
            with st.expander("🔧 Yanıt Ayarları", expanded=False):
                # Model seçimi (üstte)
                if models:
                    # Sadece Gemini modellerini göster
                    allowed_models = [
                        "gemini-2.5-flash",
                        "gemini-1.5-flash-002", 
                        "gemini-2.0-flash-001",
                        "gpt-oss:latest"
                    ]
                    
                    # Mevcut modellerden sadece izin verilenleri filtrele ve allowed_models sırasına göre sırala
                    filtered_models = []
                    for allowed_model in allowed_models:
                        for model in models:
                            if model["name"] == allowed_model:
                                filtered_models.append(model)
                                break
                    
                    if filtered_models:
                        model_names = [model["name"] for model in filtered_models]
                        # Varsayılan olarak gemini-2.5-flash kullan (index 0)
                        default_index = 0
                        
                        selected_model = st.selectbox(
                            "🤖 Model Seçimi:",
                            model_names,
                            index=default_index,  # Önceki seçim veya varsayılan
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
        
        # Yanıt üret ve yeni istek öneri butonları
        col_generate, col_new_request = st.columns([2, 1])
        
        with col_generate:
            # Yanıt üret butonu - durum makinesine ve yanıt sayısına göre kontrol
            if st.session_state.state == "draft":
                if st.session_state.yanit_sayisi < 5:
                    if st.button("🚀 Yanıt Üret", type="primary", use_container_width=True):
                        if original_text and custom_input:
                            # Loading state'i session'a kaydet
                            st.session_state.is_generating = True
                            # Sayaç 1: Toplam Üretilen Yanıt (sadece burada artar)
                            st.session_state.yanit_sayisi += 1
                            st.rerun()
                        else:
                            st.warning("⚠️ Lütfen gelen istek ve cevap alanlarını doldurun")
                else:
                    st.warning("⚠️ Maksimum 5 yanıt üretildi! Yeni istek öneri için 'Farklı İstek Öneri Cevapla' butonuna basın.")
                    # "Farklı İstek Öneri Cevapla" butonunu göster
                    st.session_state.state = "finalized"
        
        with col_new_request:
            # Farklı istek öneri butonu - durum makinesine göre kontrol
            if st.session_state.state == "finalized":
                if st.button("🆕 Farklı İstek Öneri Cevapla", type="secondary", use_container_width=True):
                    # Session state'i temizle
                    if 'responses' in st.session_state:
                        st.session_state.responses = []
                    if 'current_response' in st.session_state:
                        st.session_state.current_response = None
                    if 'generated_response' in st.session_state:
                        st.session_state.generated_response = None
                    if 'history' in st.session_state:
                        st.session_state.history = []
                    if 'is_generating' in st.session_state:
                        st.session_state.is_generating = False
                    

                    
                    # Admin paneli yenileme flag'ini sıfırla
                    st.session_state.admin_needs_refresh = False
                    
                    # Backend'de sayaç sıfırlama kaldırıldı - Sayı 2 korunacak
                    
                    # Durum makinesini sıfırla (yeni istek için)
                    st.session_state.state = "draft"
                    st.session_state.has_copied = False  # Yeni istek için yanıt seçilebilir olsun
                    st.session_state.yanit_sayisi = 0  # Yanıt sayısını sıfırla
                    
                    # Farklı istek öneri flag'i set et
                    st.session_state.is_new_request = True
                    
                    st.success("✅ Yeni istek için hazır! Gelen istek ve cevap alanlarını doldurun.")
                    st.rerun()
    
    # Sağ sütun - Yanıtlar paneli (sticky)
    with col_right:
        # Loading mesajı - yanıt alanının ortasında
        if st.session_state.get('is_generating', False):
            st.markdown("""
            <div style="
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 300px; 
                background: rgba(255, 255, 255, 0.95); 
                border-radius: 10px; 
                border: 2px dashed #ddd;
                z-index: 999999;
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                backdrop-filter: blur(5px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            ">
                <div style="text-align: center;">
                    <div style="font-size: 24px; margin-bottom: 10px;">🔄</div>
                    <div style="font-size: 18px; color: #666; font-weight: bold;">Yanıt üretiliyor...</div>
                    <div style="font-size: 14px; color: #999; margin-top: 5px;">Lütfen bekleyin</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Arka planda yanıt üret
            if original_text and custom_input:
                try:
                    # Request oluştur
                    request_id = create_request(original_text, is_new_request=True)
                    
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
                            
                            # Yanıt sayısını artır
                            st.session_state.yanit_sayisi += 1
                            
                            # Current request ID'yi güncelle
                            st.session_state.current_request_id = request_id
                            
                            # History'ye en başa ekle
                            st.session_state.history.insert(0, response_data)
                            
                            # Loading state'i kapat
                            st.session_state.is_generating = False
                            st.success("✅ Yanıt başarıyla üretildi!")
                            st.rerun()
                        else:
                            st.error("❌ Yanıt üretilemedi")
                            st.session_state.is_generating = False
                    else:
                        st.error("❌ Request oluşturulamadı")
                        st.session_state.is_generating = False
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
                    st.session_state.is_generating = False
        # Yanıt üretildikten sonra burada görünecek
        elif st.session_state.generated_response:
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
                try:
                    pyperclip.copy(response_text)
                    st.success("✅ Yanıt panoya kopyalandı!")
                    update_response_feedback(response['id'], is_selected=True, copied=True)
                    
                    # Response'u kopyalandı olarak işaretle - durum makinesine göre
                    if response.get('id'):
                        # Durum makinesi kontrolü - eğer zaten kopyalanmışsa hiçbir şey yapma
                        if st.session_state.has_copied:
                            st.warning("⚠️ Bu istek için zaten bir yanıt kopyalandı!")
                            return
                        
                        # Response'u kopyalandı olarak işaretle
                        result = mark_response_as_copied(response['id'])
                        if result:
                            # İlk kopyalama - sayac2 artacak
                            st.session_state.has_copied = True
                            st.session_state.state = "finalized"
                            # Kısa süreli çift tıklama koruması (opsiyonel)
                            st.markdown("""
                            <script>
                            const buttons = Array.from(document.querySelectorAll('button'));
                            buttons.filter(b=>b.textContent.includes('Seç ve Kopyala')).forEach(b=>{b.disabled=true; setTimeout(()=>b.disabled=false, 800);});
                            </script>
                            """, unsafe_allow_html=True)
                            
                            # Seçilen yanıtı "Son Yanıt" olarak ayarla ve diğerlerini temizle
                            st.session_state.generated_response = response
                            st.session_state.history = [response]  # Sadece seçilen yanıt kalsın
                            st.session_state.responses = [response]  # Responses'u da temizle
                            
                            st.success("✅ Response kopyalandı! Sayı 2 arttı.")
                            # Admin panelini otomatik yenile
                            st.session_state.admin_needs_refresh = True
                            st.rerun()
                        else:
                            st.error("❌ Response işaretlenemedi!")
                except Exception as e:
                    st.error(f"❌ Kopyalama hatası: {str(e)}")
        
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
                        try:
                            pyperclip.copy(resp.get('response_text', ''))
                            st.success(f"✅ Yanıt #{i} panoya kopyalandı ve seçildi!")
                            update_response_feedback(resp['id'], is_selected=True, copied=True)
                            
                            # Response'u kopyalandı olarak işaretle - durum makinesine göre
                            if resp.get('id'):
                                # Durum makinesi kontrolü - eğer zaten kopyalanmışsa hiçbir şey yapma
                                if st.session_state.has_copied:
                                    st.warning("⚠️ Bu istek için zaten bir yanıt kopyalandı!")
                                    return
                                
                                # Response'u kopyalandı olarak işaretle
                                result = mark_response_as_copied(resp['id'])
                                if result:
                                    # İlk kopyalama - sayac2 artacak
                                    st.session_state.has_copied = True
                                    st.session_state.state = "finalized"
                                    # Kısa süreli çift tıklama koruması (opsiyonel)
                                    st.markdown("""
                                    <script>
                                    const buttons = Array.from(document.querySelectorAll('button'));
                                    buttons.filter(b=>b.textContent.includes('Seç ve Kopyala')).forEach(b=>{b.disabled=true; setTimeout(()=>b.disabled=false, 800);});
                                    </script>
                                    """, unsafe_allow_html=True)
                                    
                                    # Seçilen yanıtı "Son Yanıt" olarak ayarla ve diğerlerini temizle
                                    st.session_state.generated_response = resp
                                    st.session_state.history = [resp]  # Sadece seçilen yanıt kalsın
                                    st.session_state.responses = [resp]  # Responses'u da temizle
                                    
                                    st.success("✅ Önceki yanıt response kopyalandı! Sayı 2 arttı.")
                                    # Admin panelini otomatik yenile
                                    st.session_state.admin_needs_refresh = True
                                    st.rerun()
                                else:
                                    st.error("❌ Response işaretlenemedi!")
                        except Exception as e:
                            st.error(f"❌ Kopyalama hatası: {str(e)}")

if __name__ == "__main__":
    main() 