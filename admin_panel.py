import streamlit as st
import requests
import time
from config import BACKEND_URL

def show_admin_panel():
    """İstatistik panelini göster - kullanıcı listesi ve istatistikler"""
    st.markdown("---")
    st.subheader("📊 İstatistik Paneli")
    
    # Otomatik yenileme için container oluştur
    admin_container = st.container()
    
    # Admin paneli yenileme flag'i kontrol et
    if st.session_state.get('admin_needs_refresh', False):
        st.session_state.admin_needs_refresh = False
        st.rerun()
    
    # Her 2 saniyede bir admin panelini güncelle
    with admin_container:
        st.subheader("👥 Kullanıcı Listesi")
        try:
            # Backend'den kullanıcı listesini al
                    response = requests.get(
            f"{BACKEND_URL}/auth/admin/users",
            headers={"Authorization": f"Bearer {st.session_state.access_token}"},
            timeout=30
        )
            
            if response.status_code == 200:
                users_data = response.json()
                users = users_data.get('users', [])
                
                # Toplam istatistikler tablosu
                if users:
                    st.markdown("### 📈 Genel İstatistikler")
                    
                    # Toplam değerleri hesapla
                    total_generated_responses = sum(user.get('total_requests', 0) for user in users)
                    total_answered_requests = sum(user.get('answered_requests', 0) for user in users)
                    
                    # Toplam istatistikler tablosu
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            label="Toplam Üretilen Yanıt",
                            value=total_generated_responses,
                            delta=None
                        )
                    
                    with col2:
                        st.metric(
                            label="Toplam Cevaplanan İstek Öneri",
                            value=total_answered_requests,
                            delta=None
                        )
                    
                    st.markdown("---")
                    st.markdown("### 👥 Kullanıcı Detayları")
                    
                    # Streamlit tablosu için veri hazırla
                    table_data = []
                    for user in users:
                        full_name = user.get('full_name', 'N/A')
                        department = user.get('department', 'N/A')
                        email = user.get('email', 'N/A')
                        total_requests = user.get('total_requests', 0)  # Toplam Üretilen Yanıt
                        answered_requests = user.get('answered_requests', 0)  # Cevapladığı İstek Sayısı
                        
                        table_data.append({
                            "Ad Soyad": full_name,
                            "Müdürlük": department,
                            "E-posta": email,
                            "Toplam Ürettiği Yanıt": total_requests,
                            "Cevapladığı İstek Sayısı": answered_requests
                        })
                    
                    # Streamlit tablosu göster
                    if table_data:
                        st.dataframe(
                            table_data,
                            use_container_width=True,
                            hide_index=True
                        )
                else:
                    st.info("Kullanıcı bulunamadı")
            else:
                st.error("Kullanıcı listesi alınamadı")
        except Exception as e:
            st.error(f"Bağlantı hatası: {e}")
    
    # Yenile butonu
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Yenile", use_container_width=True):
            st.rerun()
    
    # Admin panelini kapat
    with col2:
        if st.button("❌ İstatistikleri Kapat", use_container_width=True):
            st.session_state.show_admin_panel = False
            st.rerun()
