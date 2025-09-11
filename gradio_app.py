import gradio as gr
import requests
import json
from datetime import datetime
import urllib.parse

# Backend URL
BACKEND_URL = "http://localhost:8000/api/v1"

# Global state
app_state = {
    'authenticated': False,
    'access_token': None,
    'user_email': None,
    'login_email': None,
    'login_sent': False,
    'show_admin_panel': False,
    'history': [],  # Önceki yanıtlar
    'current_response': None,  # Mevcut yanıt
    'current_request_id': None,  # Mevcut request ID
    'response_count': 0,  # Bu request için üretilen yanıt sayısı
    'is_admin': False,  # Admin kontrolü için
    'state': 'draft',  # 'draft' veya 'finalized' - eski koddan
    'yanit_sayisi': 0,  # Her istek için üretilen yanıt sayısı - eski koddan
    'has_copied': False  # Kopyalama durumu - eski koddan
}


def force_show_main_app():
    """LocalStorage'dan auth bilgilerini al ve ana uygulamayı göster"""
    try:
        # State'i güncelle (localStorage'dan gelecek)
        app_state['authenticated'] = True
        app_state['access_token'] = "from_localStorage"  # JavaScript'ten gelecek
        app_state['user_email'] = "from_localStorage"    # JavaScript'ten gelecek
        app_state['is_admin'] = check_admin_status()
        
        user_profile_html = "<h3>🎉 Giriş Başarılı! Hoş geldiniz.</h3>"
        
        return (
            gr.update(visible=False),  # login_title
            gr.update(visible=False),  # login_subtitle
            gr.update(visible=False),  # login_instruction
            gr.update(visible=False),  # email_input
            gr.update(visible=False),  # send_code_btn
            gr.update(visible=False),  # code_title
            gr.update(visible=False),  # code_subtitle
            gr.update(visible=False),  # code_input
            gr.update(visible=False),  # verify_btn
            gr.update(visible=False),  # code_buttons
            gr.update(visible=True),   # user_info_row
            gr.update(visible=True, value=user_profile_html),  # user_info_html
            gr.update(visible=True),   # logout_btn
            gr.update(visible=False),  # force_show_btn
            gr.update(visible=True),   # main_app_area
            gr.update(visible=app_state['is_admin']),  # admin_panel
            gr.update(visible=True)    # main_banner
        )
    except Exception as e:
        print(f"Force show error: {e}")
        return tuple([gr.update() for _ in range(16)])


def check_auth_token():
    """Backend'den session kontrolü yap ve otomatik giriş yap"""
    try:
        import requests
        import json
        
        # Backend'den aktif session'ları al
        try:
            with open("active_sessions.json", "r") as f:
                sessions = json.load(f)
        except:
            sessions = {}
        
        # En son session'ı bul
        latest_session = None
        latest_time = None
        
        for user_id, session_data in sessions.items():
            if latest_time is None or session_data.get('created_at', '') > latest_time:
                latest_session = session_data
                latest_time = session_data.get('created_at', '')
        
        if latest_session:
            print(f"Otomatik giriş bulundu: {latest_session.get('email')}")
            
            # Session'ı kullanarak giriş yap
            app_state['authenticated'] = True
            app_state['user_email'] = latest_session.get('email')
            app_state['access_token'] = latest_session.get('jwt_token')
            app_state['is_admin'] = check_admin_status()
            
            # Her linkle girişte yeni istek olarak başla
            app_state['yanit_sayisi'] = 0
            app_state['state'] = 'draft'
            app_state['history'] = []
            app_state['current_response'] = None
            app_state['has_copied'] = False
            
            # Bu kullanıcının önceki yanıtlarını backend'den al
            try:
                headers = {"Authorization": f"Bearer {app_state['access_token']}"}
                response = requests.get(f"{BACKEND_URL}/responses/history", headers=headers, timeout=30)
                if response.status_code == 200:
                    history_data = response.json()
                    app_state['history'] = history_data.get('responses', [])
                    print(f"Kullanıcı {app_state['user_email']} için {len(app_state['history'])} önceki yanıt yüklendi")
                else:
                    print(f"History yüklenemedi: {response.status_code}")
            except Exception as e:
                print(f"History yükleme hatası: {e}")
            
            # Profil tamamlama kontrolü
            full_name = latest_session.get('full_name', '')
            department = latest_session.get('department', '')
            
            if not full_name or not department:
                print("Profil tamamlanmamış, profil tamamlama sayfasına yönlendiriliyor")
                sessions.clear()
                with open("active_sessions.json", "w") as f:
                    json.dump(sessions, f)
                
                return (
                    gr.update(visible=False),  # login_title
                    gr.update(visible=False),  # login_subtitle
                    gr.update(visible=False),  # login_instruction
                    gr.update(visible=False),  # email_input
                    gr.update(visible=False),  # send_code_btn
                    gr.update(visible=False),  # code_title
                    gr.update(visible=False),  # code_subtitle
                    gr.update(visible=False),  # code_input
                    gr.update(visible=False),  # verify_btn
                    gr.update(visible=False),  # code_buttons
                    gr.update(visible=False),  # user_info_row
                    gr.update(visible=False),  # user_info_html
                    gr.update(visible=False),  # logout_btn
                    gr.update(visible=False),  # force_show_btn
                    gr.update(visible=False),  # main_app_area
                    gr.update(visible=False),  # admin_panel
                    gr.update(visible=True),   # main_banner
                    gr.update(visible=True),   # profile_completion_area
                    gr.update(visible=False),  # profile_error_msg
                    gr.update(visible=False)    # response_settings_accordion
                )
            
            # Session'ı temizle (tek kullanımlık)
            sessions.clear()
            with open("active_sessions.json", "w") as f:
                json.dump(sessions, f)
            
            print("Otomatik giriş başarılı!")
            
            # UI'yi ana uygulamaya geçir
            # Session'dan kullanıcı bilgilerini al
            user_profile_html = f"<h3 style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;'>👤 {full_name} - {department}</h3>"
            
            return (
                gr.update(visible=False),  # login_title
                gr.update(visible=False),  # login_subtitle
                gr.update(visible=False),  # login_instruction
                gr.update(visible=False),  # email_input
                gr.update(visible=False),  # send_code_btn
                gr.update(visible=False),  # code_title
                gr.update(visible=False),  # code_subtitle
                gr.update(visible=False),  # code_input
                gr.update(visible=False),  # verify_btn
                gr.update(visible=False),  # code_buttons
                gr.update(visible=True),   # user_info_row
                gr.update(visible=True, value=user_profile_html),  # user_info_html
                gr.update(visible=True),   # logout_btn
                gr.update(visible=False),  # force_show_btn
                gr.update(visible=True),   # main_app_area
                gr.update(visible=app_state['is_admin']),  # admin_panel
                gr.update(visible=True),   # main_banner
                gr.update(visible=False),  # profile_completion_area
                gr.update(visible=False),  # profile_error_msg
                gr.update(visible=app_state['is_admin'])  # response_settings_accordion
            )
        else:
            print("Otomatik giriş bulunamadı")
            return tuple([gr.update() for _ in range(20)])
            
    except Exception as e:
        print(f"Otomatik giriş hatası: {e}")
        return tuple([gr.update() for _ in range(20)])
        
        if auth_token:
            # JWT token'ı backend'e gönder ve doğrula
            response = requests.post(f"{BACKEND_URL}/auth/verify-token", 
                                   json={"token": auth_token})
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # Giriş başarılı, state'i güncelle
                    app_state['authenticated'] = True
                    app_state['access_token'] = auth_token
                    app_state['user_email'] = data.get("email")
                    app_state['is_admin'] = data.get("is_admin", False)
                    print(f"Magic link ile giriş başarılı: {data.get('email')}")
    except Exception as e:
        print(f"Auth token kontrol hatası: {e}")


def handle_complete_login_flow(email_or_code, current_step="email"):
    """
    Tek fonksiyonla tüm login akışını yönet
    UI geçişi yok, sadece mesaj değişimi
    """
    try:
        if current_step == "email":
            # Email gönderme aşaması
            if not email_or_code or not email_or_code.strip():
                return (
                    gr.update(visible=True),  # login_title
                    gr.update(visible=True),  # login_subtitle
                    gr.update(visible=True),  # login_instruction
                    gr.update(),  # email_input
                    gr.update(),  # send_code_btn
                    gr.update(visible=False),  # code_title
                    gr.update(visible=False),  # code_subtitle
                    gr.update(visible=False),  # code_input
                    gr.update(visible=False),  # verify_btn
                    gr.update(visible=False)  # code_buttons
                )

            # Backend'e email gönder
            response = requests.post(
                f"{BACKEND_URL}/auth/send",
                json={"email": email_or_code},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    app_state['login_email'] = email_or_code
                    return (
                        gr.update(visible=False),  # login_title
                        gr.update(visible=False),  # login_subtitle
                        gr.update(visible=False),  # login_instruction
                        gr.update(),  # email_input
                        gr.update(visible=False),  # send_code_btn
                        gr.update(visible=True),  # code_title
                        gr.update(visible=True),  # code_subtitle
                        gr.update(visible=True),  # code_input
                        gr.update(visible=True),  # verify_btn
                        gr.update(visible=True)  # code_buttons
                    )
                else:
                    return (
                        gr.update(visible=True),  # login_title
                        gr.update(visible=True),  # login_subtitle
                        gr.update(visible=True),  # login_instruction
                        gr.update(),  # email_input
                        gr.update(),  # send_code_btn
                        gr.update(visible=False),  # code_title
                        gr.update(visible=False),  # code_subtitle
                        gr.update(visible=False),  # code_input
                        gr.update(visible=False),  # verify_btn
                        gr.update(visible=False)  # code_buttons
                    )
            else:
                return (
                    gr.update(visible=True),  # login_title
                    gr.update(visible=True),  # login_subtitle
                    gr.update(visible=True),  # login_instruction
                    gr.update(),  # email_input
                    gr.update(),  # send_code_btn
                    gr.update(visible=False),  # code_title
                    gr.update(visible=False),  # code_subtitle
                    gr.update(visible=False),  # code_input
                    gr.update(visible=False),  # verify_btn
                    gr.update(visible=False)  # code_buttons
                )

        elif current_step == "code":
            # Kod doğrulama aşaması
            if not email_or_code or len(email_or_code) != 6:
                return (
                    gr.update(),  # code_title
                    gr.update(),  # code_subtitle
                    gr.update(),  # code_input
                    gr.update(),  # verify_btn
                    gr.update(),  # code_buttons
                    gr.update(),  # email_input
                    gr.update(visible=False),  # user_info_row
                    gr.update(visible=False),  # user_info_html
                    gr.update(visible=False),  # logout_btn
                    gr.update(visible=False),  # main_app_area
                    gr.update(visible=False),  # admin_panel
                    gr.update(visible=False)  # main_banner
                )

            # Backend'de kod doğrula
            response = requests.post(
                f"{BACKEND_URL}/auth/verify-code",
                json={"email": app_state.get('login_email'), "code": email_or_code},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                # Giriş başarılı - state'i güncelle
                app_state['authenticated'] = True
                app_state['access_token'] = data.get("access_token")
                app_state['user_email'] = data.get("email")
                app_state['is_admin'] = check_admin_status()

                user_profile_html = f"""
                <div style="text-align: center; padding: 1rem; background: #e8f5e8; border-radius: 8px;">
                    <h3 style="color: #2e7d32; margin-bottom: 0.5rem; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">🎉 Giriş Başarılı!</h3>
                    <p style="color: #666; margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">Hoş geldiniz: {data.get('email', 'Kullanıcı')}</p>
                </div>
                """

                return (
                    gr.update(),  # code_title
                    gr.update(),  # code_subtitle
                    gr.update(),  # code_input
                    gr.update(),  # verify_btn
                    gr.update(),  # code_buttons
                    gr.update(),  # email_input
                    gr.update(visible=True),   # user_info_row
                    gr.update(visible=True, value=user_profile_html),  # user_info_html
                    gr.update(visible=True),   # logout_btn
                    gr.update(visible=False),  # force_show_btn
                    gr.update(visible=True),   # main_app_area
                    gr.update(visible=app_state['is_admin']),  # admin_panel
                    gr.update(visible=True)    # main_banner
                )
            else:
                return (
                    gr.update(),  # code_title
                    gr.update(),  # code_subtitle
                    gr.update(value=""),  # code_input
                    gr.update(),  # verify_btn
                    gr.update(),  # code_buttons
                    gr.update(),  # email_input
                    gr.update(visible=False),  # user_info_row
                    gr.update(visible=False),  # user_info_html
                    gr.update(visible=False),  # logout_btn
                    gr.update(visible=False),  # main_app_area
                    gr.update(visible=False),  # admin_panel
                    gr.update(visible=False)  # main_banner
                )

    except Exception as e:
        return (
            gr.update(visible=True),  # login_title
            gr.update(visible=True),  # login_subtitle
            gr.update(visible=True),  # login_instruction
            gr.update(),  # email_input
            gr.update(),  # send_code_btn
            gr.update(visible=False),  # code_title
            gr.update(visible=False),  # code_subtitle
            gr.update(visible=False),  # code_input
            gr.update(visible=False),  # verify_btn
            gr.update(visible=False)  # code_buttons
        )

def send_login_code(email):
    """E-posta ile giriş kodu gönder - mevcut arayüzü koruyarak"""
    try:
        if not email or not email.endswith("@nilufer.bel.tr"):
            return (
                gr.update(visible=True),  # login_title
                gr.update(visible=True),  # login_subtitle
                gr.update(visible=True),  # login_instruction
                gr.update(),  # email_input
                gr.update(),  # send_code_btn
                gr.update(visible=False),  # code_title
                gr.update(visible=False),  # code_subtitle
                gr.update(visible=False),  # code_input
                gr.update(visible=False),  # verify_btn
                gr.update(visible=False)  # code_buttons
            )
        
        response = requests.post(
            f"{BACKEND_URL}/auth/send",
            json={"email": email},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Email gönderildi, response: {data}")
            app_state['login_email'] = email
            app_state['login_sent'] = True
            return (
                gr.update(visible=False),  # login_title
                gr.update(visible=False),  # login_subtitle
                gr.update(visible=False),  # login_instruction
                gr.update(),  # email_input
                gr.update(visible=False),  # send_code_btn
                gr.update(visible=True),  # code_title
                gr.update(visible=True),  # code_subtitle
                gr.update(visible=True),  # code_input
                gr.update(visible=True),  # verify_btn
                gr.update(visible=True)  # code_buttons
            )
        else:
            return (
                gr.update(visible=True),  # login_title
                gr.update(visible=True),  # login_subtitle
                gr.update(visible=True),  # login_instruction
                gr.update(),  # email_input
                gr.update(),  # send_code_btn
                gr.update(visible=False),  # code_title
                gr.update(visible=False),  # code_subtitle
                gr.update(visible=False),  # code_input
                gr.update(visible=False),  # verify_btn
                gr.update(visible=False)  # code_buttons
            )
    except Exception as e:
        return (
            gr.update(visible=True),  # login_title
            gr.update(visible=True),  # login_subtitle
            gr.update(visible=True),  # login_instruction
            gr.update(),  # email_input
            gr.update(),  # send_code_btn
            gr.update(visible=False),  # code_title
            gr.update(visible=False),  # code_subtitle
            gr.update(visible=False),  # code_input
            gr.update(visible=False),  # verify_btn
            gr.update(visible=False)  # code_buttons
        )

def verify_login_code(email, code):
    """6 haneli kod ile giriş doğrula - mevcut arayüzü koruyarak"""
    try:
        if not code or len(code) != 6:
            return (
                gr.update(),  # code_title
                gr.update(),  # code_subtitle
                gr.update(),  # code_input
                gr.update(),  # verify_btn
                gr.update(),  # code_buttons
                gr.update(),  # email_input
                gr.update(visible=False),  # user_info_row
                gr.update(visible=False),  # user_info_html
                gr.update(visible=False),  # logout_btn
                gr.update(visible=False),  # main_app_area
                gr.update(visible=False),  # admin_panel
                gr.update(visible=False)  # main_banner
            )
        
        response = requests.post(
            f"{BACKEND_URL}/auth/verify-code",
            json={"email": email, "code": code},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Session state'i set et
            app_state['authenticated'] = True
            app_state['access_token'] = data["access_token"]
            app_state['user_email'] = data["email"]
            app_state['login_sent'] = False
            
            # Admin durumunu kontrol et
            app_state['is_admin'] = check_admin_status()
            
            # Kullanıcı profil bilgilerini al
            user_profile_html = get_user_profile()
            
            # Profil tamamlama kontrolü
            try:
                headers = {"Authorization": f"Bearer {app_state['access_token']}"}
                profile_response = requests.get(f"{BACKEND_URL}/auth/profile", headers=headers)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    full_name = profile_data.get('full_name', '')
                    department = profile_data.get('department', '')
                    
                    if not full_name or not department:
                        print("Profil tamamlanmamış, profil tamamlama sayfasına yönlendiriliyor")
                        return (
                            gr.update(visible=False),  # code_title
                            gr.update(visible=False),  # code_subtitle
                            gr.update(visible=False),  # code_input
                            gr.update(visible=False),  # verify_btn
                            gr.update(visible=False),  # code_buttons
                            gr.update(visible=False),  # email_input
                            gr.update(visible=False),  # user_info_row
                            gr.update(visible=False),  # user_info_html
                            gr.update(visible=False),  # logout_btn
                            gr.update(visible=False),  # force_show_btn
                            gr.update(visible=False),  # main_app_area
                            gr.update(visible=False),  # admin_panel
                            gr.update(visible=True),   # main_banner
                            gr.update(visible=True),   # profile_completion_area
                            gr.update(visible=False),  # profile_error_msg
                            gr.update(visible=False)    # response_settings_accordion
                        )
            except Exception as e:
                print(f"Profil kontrolü hatası: {e}")
            
            return (
                gr.update(visible=False),  # code_title
                gr.update(visible=False),  # code_subtitle
                gr.update(visible=False),  # code_input
                gr.update(visible=False),  # verify_btn
                gr.update(visible=False),  # code_buttons
                gr.update(visible=False),  # email_input
                gr.update(visible=True),   # user_info_row
                gr.update(visible=True, value=user_profile_html),  # user_info_html
                gr.update(visible=True),   # logout_btn
                gr.update(visible=False),  # force_show_btn
                gr.update(visible=True),   # main_app_area
                gr.update(visible=app_state['is_admin']),  # admin_panel
                gr.update(visible=True),   # main_banner
                gr.update(visible=False),  # profile_completion_area
                gr.update(visible=False),  # profile_error_msg
                gr.update(visible=app_state['is_admin'])  # response_settings_accordion
            )
        else:
            error_data = response.json()
            return (
                gr.update(),  # code_title
                gr.update(),  # code_subtitle
                gr.update(),  # code_input
                gr.update(),  # verify_btn
                gr.update(),  # code_buttons
                gr.update(),  # email_input
                gr.update(visible=False),  # user_info_row
                gr.update(visible=False),  # user_info_html
                gr.update(visible=False),  # logout_btn
                gr.update(visible=False),  # force_show_btn
                gr.update(visible=False),  # main_app_area
                gr.update(visible=False),  # admin_panel
                gr.update(visible=False),  # main_banner
                gr.update(visible=False),  # profile_completion_area
                gr.update(visible=False),  # profile_error_msg
                gr.update(visible=False)   # response_settings_accordion
            )
    except Exception as e:
        return (
            gr.update(),  # code_title
            gr.update(),  # code_subtitle
            gr.update(),  # code_input
            gr.update(),  # verify_btn
            gr.update(),  # code_buttons
            gr.update(),  # email_input
            gr.update(visible=False),  # user_info_row
            gr.update(visible=False),  # user_info_html
            gr.update(visible=False),  # logout_btn
            gr.update(visible=False),  # force_show_btn
            gr.update(visible=False),  # main_app_area
            gr.update(visible=False),  # admin_panel
            gr.update(visible=False),  # main_banner
            gr.update(visible=False),  # profile_completion_area
            gr.update(visible=False),  # profile_error_msg
            gr.update(visible=False)   # response_settings_accordion
        )

def logout_user():
    """Logout - localStorage temizle"""
    # Server state temizle
    for key in app_state:
        if key in ['authenticated', 'access_token', 'user_email', 'is_admin']:
            app_state[key] = False if key == 'authenticated' or key == 'is_admin' else None
    
    # JavaScript ile localStorage temizle (sayfa yüklendiğinde çalışacak)
    logout_html = """
    <script>
    localStorage.clear();
    setTimeout(() => location.reload(), 100);
    </script>
    """
    
    return (
        gr.update(visible=True),   # login ekranını göster
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(value=""),       # email_input temizle
        gr.update(visible=True),
        gr.update(visible=False),  # code ekranını gizle
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),  # user info gizle
        gr.update(visible=False, value=logout_html),  # logout script çalıştır
        gr.update(visible=False),
        gr.update(visible=False),  # force_show_btn gizle
        gr.update(visible=False),  # main app gizle
        gr.update(visible=False),
        gr.update(visible=False)
    )

def complete_profile(full_name, department):
    """Profil tamamlama fonksiyonu"""
    try:
        if not full_name or not department:
                return (
                    gr.update(visible=True, value="<div style='color: red; text-align: center; padding: 1rem; font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif;'>❌ Lütfen tüm alanları doldurun!</div>"),  # profile_error_msg
                gr.update(),  # profile_completion_area
                gr.update(),  # user_info_row
                gr.update(),  # user_info_html
                gr.update(),  # logout_btn
                gr.update(),  # force_show_btn
                gr.update(),  # main_app_area
                gr.update(),  # admin_panel
                gr.update()   # main_banner
            )
        
        # Backend'e profil bilgilerini gönder
        import requests
        response = requests.post(
            f"{BACKEND_URL}/auth/complete-profile",
            json={"full_name": full_name, "department": department},
            headers={"Authorization": f"Bearer {app_state.get('access_token')}"},
            timeout=30
        )
        
        if response.status_code == 200:
            # Profil tamamlandı, ana uygulamaya geç
            app_state['user_full_name'] = full_name
            app_state['user_department'] = department
            
            user_profile_html = f"<h3 style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;'>👤 {full_name} - {department}</h3>"
            
            return (
                gr.update(visible=False),  # profile_error_msg
                gr.update(visible=False),  # profile_completion_area
                gr.update(visible=True),   # user_info_row
                gr.update(visible=True, value=user_profile_html),  # user_info_html
                gr.update(visible=True),   # logout_btn
                gr.update(visible=False),  # force_show_btn
                gr.update(visible=True),   # main_app_area
                gr.update(visible=True),   # admin_panel
                gr.update(visible=True)    # main_banner
            )
        else:
            error_data = response.json()
            error_message = f"<div style='color: red; text-align: center; padding: 1rem; font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif;'>❌ Hata: {error_data.get('detail', 'Bilinmeyen hata')}</div>"
            return (
                gr.update(visible=True, value=error_message),  # profile_error_msg
                gr.update(),  # profile_completion_area
                gr.update(),  # user_info_row
                gr.update(),  # user_info_html
                gr.update(),  # logout_btn
                gr.update(),  # force_show_btn
                gr.update(),  # main_app_area
                gr.update(),  # admin_panel
                gr.update()   # main_banner
            )
            
    except Exception as e:
        error_message = f"<div style='color: red; text-align: center; padding: 1rem; font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif;'>❌ Bağlantı hatası: {str(e)}</div>"
        return (
            gr.update(visible=True, value=error_message),  # profile_error_msg
            gr.update(),  # profile_completion_area
            gr.update(),  # user_info_row
            gr.update(),  # user_info_html
            gr.update(),  # logout_btn
            gr.update(),  # force_show_btn
            gr.update(),  # main_app_area
            gr.update(),  # admin_panel
            gr.update()   # main_banner
        )

def get_user_profile():
    """Kullanıcı profil bilgilerini getir"""
    try:
        headers = {"Authorization": f"Bearer {app_state['access_token']}"}
        response = requests.get(f"{BACKEND_URL}/auth/profile", headers=headers)
        if response.status_code == 200:
            data = response.json()
            full_name = data.get('full_name', 'İsimsiz')
            department = data.get('department', 'Departman Belirtilmemiş')
            return f"<h3 style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;'>👤 {full_name} - {department}</h3>"
        else:
            return "<h3 style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;'>👤 Kullanıcı Bilgileri Alınamadı</h3>"
    except Exception as e:
        return f"<h3 style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;'>👤 Hata: {str(e)}</h3>"

def check_admin_status():
    """Admin durumunu kontrol et"""
    try:
        headers = {"Authorization": f"Bearer {app_state['access_token']}"}
        response = requests.get(f"{BACKEND_URL}/auth/admin/users", headers=headers, timeout=10)
        return response.status_code == 200
    except:
        return False

def mark_response_as_copied(response_id):
    """Mark response as copied (copied=True) - eski koddan"""
    try:
        url = f"{BACKEND_URL}/responses/{response_id}/mark-copied"
        response = requests.put(url)
        return response.status_code == 200
    except Exception as e:
        print(f"Response kopyalandı olarak işaretlenemedi: {e}")
        return False

def update_response_feedback(response_id, is_selected=False, copied=False):
    """Update response feedback - eski koddan"""
    try:
        data = {
            "response_id": response_id,
            "is_selected": is_selected,
            "copied": copied
        }
        response = requests.post(f"{BACKEND_URL}/responses/feedback", json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Geri bildirim güncellenemedi: {e}")
        return False

def get_admin_statistics():
    """Admin istatistiklerini al - eski kodun mantığını takip eder"""
    try:
        headers = {"Authorization": f"Bearer {app_state['access_token']}"}
        response = requests.get(f"{BACKEND_URL}/auth/admin/users", headers=headers, timeout=30)
        
        if response.status_code == 200:
            users_data = response.json()
            users = users_data.get('users', [])
            
            if users:
                # Toplam değerleri hesapla - eski kodun mantığı
                total_generated_responses = sum(user.get('total_requests', 0) for user in users)
                total_answered_requests = sum(user.get('answered_requests', 0) for user in users)
                
                # HTML tablosu oluştur
                html = f"""
                <div style="background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 4px 8px rgba(0,0,0,0.1);">
                    <h2 style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">📊 İstatistik Paneli</h2>
                    
                    <h3 style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">📈 Genel İstatistikler</h3>
                    <div style="display: flex; gap: 2rem; margin-bottom: 2rem;">
                        <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px; text-align: center; flex: 1;">
                            <h4 style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Toplam Üretilen Yanıt</h4>
                            <div style="font-size: 2rem; font-weight: bold; color: #1976d2; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{total_generated_responses}</div>
                        </div>
                        <div style="background: #e8f5e8; padding: 1rem; border-radius: 8px; text-align: center; flex: 1;">
                            <h4 style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Toplam Cevaplanan İstek Öneri</h4>
                            <div style="font-size: 2rem; font-weight: bold; color: #2e7d32; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{total_answered_requests}</div>
                        </div>
                    </div>
                    
                    <h3 style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">👥 Kullanıcı Detayları</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
                        <thead>
                            <tr style="background: #f5f5f5;">
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: left; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Ad Soyad</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: left; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Müdürlük</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: left; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">E-posta</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Toplam Ürettiği Yanıt</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Cevapladığı İstek Sayısı</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                
                # Kullanıcı verilerini tabloya ekle - eski kodun mantığı
                for user in users:
                    full_name = user.get('full_name', 'N/A')
                    department = user.get('department', 'N/A')
                    email = user.get('email', 'N/A')
                    total_requests = user.get('total_requests', 0)  # Toplam Üretilen Yanıt
                    answered_requests = user.get('answered_requests', 0)  # Cevapladığı İstek Sayısı
                    
                    html += f"""
                            <tr>
                                <td style="padding: 12px; border: 1px solid #ddd; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{full_name}</td>
                                <td style="padding: 12px; border: 1px solid #ddd; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{department}</td>
                                <td style="padding: 12px; border: 1px solid #ddd; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{email}</td>
                                <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{total_requests}</td>
                                <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">{answered_requests}</td>
                            </tr>
                    """
                
                html += """
                        </tbody>
                    </table>
                    
                </div>
                """
                
                return html
            else:
                return "<div style='color: orange; font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif;'>ℹ️ Kullanıcı bulunamadı</div>"
        else:
            return "<div style='color: red; font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif;'>❌ Kullanıcı listesi alınamadı</div>"
    except Exception as e:
        return f"<div style='color: red; font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif;'>❌ Bağlantı hatası: {str(e)}</div>"

def refresh_admin_panel_handler():
    """Admin panelini yenile - verileri güncelle"""
    return gr.update(value=get_admin_statistics())

def create_request_handler(original_text, custom_input):
    """Yeni request oluştur"""
    try:
        headers = {
            "Authorization": f"Bearer {app_state['access_token']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "original_text": original_text,
            "response_type": "informative",
            "is_new_request": True
        }
        
        response = requests.post(f"{BACKEND_URL}/requests", json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('id'), "✅ İstek oluşturuldu"
        else:
            error_data = response.json()
            return None, f"❌ İstek oluşturma hatası: {error_data.get('detail', 'Bilinmeyen hata')}"
            
    except Exception as e:
        return None, f"❌ Bağlantı hatası: {str(e)}"

def generate_response_handler(original_text, custom_input, model, temperature, max_tokens):
    """Yanıt üret - eski Streamlit mantığını takip eder"""
    try:
        print(f"DEBUG: generate_response_handler çağrıldı")
        print(f"DEBUG: app_state['state'] = {app_state.get('state')}")
        print(f"DEBUG: app_state['yanit_sayisi'] = {app_state.get('yanit_sayisi')}")
        
        # Maksimum 5 yanıt kontrolü - eski koddan
        if app_state['yanit_sayisi'] >= 5:
            print(f"DEBUG: Maksimum 5 yanıt üretildi, hata mesajı döndürülüyor")
            return ("⚠️ Maksimum 5 yanıt üretildi! Yeni istek öneri için 'Yeni İstek Öneri Cevapla' butonuna basın.", "", gr.update(visible=False), gr.update(visible=True),
                   gr.update(visible=False),  # Ana copy butonu gizli olsun
                   gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                   gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                   gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
        
        # Eğer yeni istekse request oluştur
        if app_state['current_request_id'] is None:
            request_id, create_msg = create_request_handler(original_text, custom_input)
            if not request_id:
                return ("", "", gr.update(visible=False), gr.update(visible=True),
                       gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                       gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                       gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
            app_state['current_request_id'] = request_id
        else:
            request_id = app_state['current_request_id']
        
        # Yanıt üret
        headers = {
            "Authorization": f"Bearer {app_state['access_token']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "request_id": request_id,
            "model_name": model,
            "custom_input": custom_input,
            "temperature": temperature,
            "top_p": 0.9,
            "repetition_penalty": 1.2,
            "system_prompt": ""
        }
        
        response = requests.post(f"{BACKEND_URL}/generate", json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            generated_text = data.get('response_text', '')
            response_id = data.get('id')
            
            # Yanıtı state'e ekle
            new_response = {
                'id': response_id,
                'response_text': generated_text,
                'created_at': datetime.now().isoformat(),
                'latency_ms': data.get('latency_ms', 0),
                'model_name': model
            }
            
            # Eski Streamlit mantığını takip et: history'ye yeni yanıtı ekle
            app_state['history'].insert(0, new_response)
            print(f"DEBUG: History'ye eklendi. History uzunluğu: {len(app_state['history'])}")
            
            # Current response'u güncelle (en yeni yanıt)
            app_state['current_response'] = new_response
            app_state['response_count'] += 1
            app_state['yanit_sayisi'] += 1  # Eski koddan - yanıt sayısını artır
            
            print(f"DEBUG: Yeni yanıt eklendi. History: {len(app_state['history'])}, Current: {app_state['current_response'] is not None}")
            
            # Ana yanıt için kopyalanabilir display oluştur
            main_response_html = create_copyable_response_display(generated_text)
            
            # Önceki yanıtlar HTML'ini oluştur (history[1:] - ilk yanıt hariç)
            previous_html = create_previous_responses_html()
            
            # Gradio akordiyonlarını tekrar görünür yap ama içlerinde yeşil textarea'lar olsun
            accordion_updates = []
            text_updates = []
            button_updates = []
            
            for i, resp in enumerate(app_state['history'][1:], 1):
                if i <= 4:  # Maksimum 4 önceki yanıt
                    # Accordion'ı görünür yap ama içeriği yeşil textarea ile değiştir
                    accordion_updates.append(gr.update(visible=True, label=f"📄 Yanıt #{i} - {resp.get('created_at', '')[:19]}"))
                    # Normal textbox yerine normal renkli textarea HTML'i gönder
                    normal_textarea_html = f"""
                    <div style="padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <textarea readonly onclick="this.select(); document.execCommand('copy'); showCopySuccess(this);" 
                                  class="gradio-textbox">
{resp.get('response_text', '')}
                        </textarea>
                        <p style="color: #666; font-size: 12px; margin: 8px 0 0 0;">
                            💡 Metne dokunarak otomatik kopyalayın
                        </p>
                    </div>
                    """
                    text_updates.append(gr.update(visible=True, value=normal_textarea_html))
                    button_updates.append(gr.update(visible=True))
                else:
                    accordion_updates.append(gr.update(visible=False))
                    text_updates.append(gr.update(visible=False))
                    button_updates.append(gr.update(visible=False))
            
            # Eksik olanları gizle
            while len(accordion_updates) < 4:
                accordion_updates.append(gr.update(visible=False))
                text_updates.append(gr.update(visible=False))
                button_updates.append(gr.update(visible=False))
            
            # Buton görünürlüğünü güncelle
            generate_visible = app_state['state'] == 'draft' and app_state['yanit_sayisi'] < 5
            new_request_visible = app_state['state'] == 'finalized' or app_state['yanit_sayisi'] >= 5
            
            return (main_response_html, previous_html, gr.update(visible=generate_visible), gr.update(visible=new_request_visible),
                   gr.update(visible=True),  # Ana copy butonu görünür olsun
                   accordion_updates[0], accordion_updates[1], accordion_updates[2], accordion_updates[3],
                   text_updates[0], text_updates[1], text_updates[2], text_updates[3],
                   button_updates[0], button_updates[1], button_updates[2], button_updates[3])
        else:
            error_data = response.json()
            error_msg = f"❌ Hata: {error_data.get('detail', 'Bilinmeyen hata')}"
            return ("", error_msg, gr.update(), gr.update(),
                   gr.update(visible=False),  # Ana copy butonu gizli olsun
                   gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                   gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                   gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
            
    except Exception as e:
        error_msg = f"❌ Bağlantı hatası: {str(e)}"
        return ("", "", gr.update(visible=False), gr.update(visible=True),
               gr.update(visible=False),  # Ana copy butonu gizli olsun
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))

def create_copyable_response_display(response_text=""):
    """Kopyalanabilir yeşil kutu formatında yanıt göster"""
    if not response_text:
        return """
        <div style="background: transparent; padding: 15px; border-radius: 8px; margin: 10px 0; min-height: 100px;">
            <p style="color: #666; text-align: center; margin: 0;">Henüz yanıt üretilmedi...</p>
        </div>
        """
    
    copyable_html = f"""
    <div style="padding: 15px; border-radius: 8px; margin: 10px 0;">
        <p style="margin: 0 0 10px 0; font-weight: bold;">📝 Son Üretilen Yanıt:</p>
        <textarea readonly onclick="this.select(); document.execCommand('copy'); showCopySuccess(this);" 
                  class="gradio-textbox">
{response_text}
        </textarea>
        <p style="color: #666; font-size: 12px; margin: 8px 0 0 0;">
            💡 Metne dokunarak otomatik kopyalayın
        </p>
    </div>
    
    <script>
    function showCopySuccess(textarea) {{
        const originalBorder = textarea.style.border;
        const originalBackground = textarea.style.background;
        textarea.style.border = '2px solid #3B82F6';
        textarea.style.background = '#f0f9ff';
        
        // Geçici mesaj göster
        const parent = textarea.parentElement;
        const successMsg = document.createElement('div');
        successMsg.innerHTML = '<p style="color: #3B82F6; font-weight: bold; margin: 5px 0;">✅ Kopyalandı!</p>';
        parent.appendChild(successMsg);
        
        setTimeout(() => {{
            textarea.style.border = originalBorder;
            textarea.style.background = originalBackground;
            parent.removeChild(successMsg);
        }}, 2000);
    }}
    </script>
    """
    
    return copyable_html

def create_previous_response_accordion(response_data, index):
    """Önceki yanıtlar için kopyalanabilir accordion"""
    response_text = response_data.get('response_text', '')
    created_at = response_data.get('created_at', '')
    model_name = response_data.get('model_name', '')
    
    return f"""
    <details style="margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <summary style="background: #f8f9fa; padding: 12px; cursor: pointer; font-weight: bold;">
            📄 Yanıt #{index} - {created_at[:19] if created_at else 'Bilinmeyen zaman'} ({model_name})
        </summary>
        <div style="padding: 15px;">
            <textarea readonly onclick="this.select(); document.execCommand('copy'); showCopySuccess(this);" 
                      class="gradio-textbox">
{response_text}
            </textarea>
            <p style="color: #666; font-size: 12px; margin: 8px 0 0 0;">
                💡 Metne dokunarak da kopyalayabilirsiniz
            </p>
        </div>
    </details>
    """

def create_previous_responses_html():
    """Önceki yanıtları HTML formatında oluştur - sadece başlık"""
    print(f"DEBUG: create_previous_responses_html çağrıldı. History uzunluğu: {len(app_state['history'])}")
    
    if len(app_state['history']) <= 1:  # Sadece 1 yanıt varsa önceki yanıt yok
        return "<div style='color: #666; font-style: italic; font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif;'>Henüz önceki yanıt yok</div>"
    
    # Sadece başlık döndür, yeşil kutuları kaldır (accordion'larda zaten var)
    return "<h3 style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;'>📚 Önceki Yanıtlar</h3>"

def copy_response_handler(response_text):
    """Mevcut yanıtı kopyala - eski koddan mantık"""
    # İlk kopyalama kontrolü - eğer zaten kopyalanmışsa hiçbir şey yapma
    if app_state['has_copied']:
        return ("⚠️ Bu istek için zaten bir yanıt kopyalandı!", gr.update(), gr.update())
    
    # Durum makinesini finalized yap - eski koddan
    app_state['state'] = 'finalized'
    app_state['has_copied'] = True  # Eski koddan
    
    # Veritabanında response'u kopyalandı olarak işaretle
    if app_state['current_response'] and app_state['current_response'].get('id'):
        response_id = app_state['current_response']['id']
        
        # Response'u kopyalandı olarak işaretle
        result = mark_response_as_copied(response_id)
        if result:
            # Feedback'i güncelle
            update_response_feedback(response_id, is_selected=True, copied=True)
            print("✅ Response veritabanında kopyalandı olarak işaretlendi!")
        else:
            print("❌ Response işaretlenemedi!")
    
    # Panoya kopyala
    try:
        import pyperclip
        pyperclip.copy(response_text)
        print("✅ Yanıt panoya kopyalandı!")
    except Exception as e:
        print(f"❌ Panoya kopyalama hatası: {e}")
    
    # Buton görünürlüğünü güncelle
    generate_visible = app_state['state'] == 'draft' and app_state['yanit_sayisi'] < 5
    new_request_visible = app_state['state'] == 'finalized' or app_state['yanit_sayisi'] >= 5
    
    return ("✅ Yanıt kopyalandı! (Ctrl+V ile yapıştırabilirsiniz)", gr.update(visible=generate_visible), gr.update(visible=new_request_visible))

def copy_previous_response_handler(response_id):
    """Önceki yanıtı kopyala ve seç - eski koddan mantık"""
    try:
        # History'den yanıtı bul
        for resp in app_state['history']:
            if resp['id'] == response_id:
                # Durum makinesi kontrolü - eğer zaten kopyalanmışsa hiçbir şey yapma
                if app_state['has_copied']:
                    return ("⚠️ Bu istek için zaten bir yanıt kopyalandı!", gr.update(), gr.update(),
                           gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                           gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                           gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                           gr.update(visible=False), gr.update(visible=False))
                
                # Response'u kopyalandı olarak işaretle
                result = mark_response_as_copied(response_id)
                if result:
                    # Feedback'i güncelle
                    update_response_feedback(response_id, is_selected=True, copied=True)
                    
                    # Durum makinesini güncelle
                    app_state['state'] = 'finalized'
                    app_state['has_copied'] = True
                    app_state['yanit_sayisi'] += 1  # Yanıt sayısını artır
                    
                    # Seçilen yanıtı current_response olarak ayarla
                    app_state['current_response'] = resp
                    app_state['history'].remove(resp)
                    
                    # Panoya kopyala
                    try:
                        import pyperclip
                        pyperclip.copy(resp['response_text'])
                        print("✅ Önceki yanıt panoya kopyalandı!")
                    except Exception as e:
                        print(f"❌ Panoya kopyalama hatası: {e}")
                    
                    # Buton görünürlüğünü güncelle
                    generate_visible = app_state['state'] == 'draft' and app_state['yanit_sayisi'] < 5
                    new_request_visible = app_state['state'] == 'finalized' or app_state['yanit_sayisi'] >= 5
                    
                    print("✅ Önceki yanıt response kopyalandı! Sayı 2 arttı.")
                    
                    # Ana yanıt için kopyalanabilir display oluştur
                    main_response_html = create_copyable_response_display(resp['response_text'])
                    
                    # Önceki yanıtlar HTML'ini oluştur
                    previous_html = create_previous_responses_html()
                    
                    # Tüm akordiyonları gizle (seçilen yanıt ana alana gittiği için)
                    accordion_updates = [gr.update(visible=False)] * 4
                    text_updates = [gr.update(visible=False)] * 4
                    button_updates = [gr.update(visible=False)] * 4
                    
                    return (main_response_html, previous_html, gr.update(visible=generate_visible), gr.update(visible=new_request_visible),
                           gr.update(visible=False),  # Ana copy butonu gizli olsun (seçim yapıldı)
                           accordion_updates[0], accordion_updates[1], accordion_updates[2], accordion_updates[3],
                           text_updates[0], text_updates[1], text_updates[2], text_updates[3],
                           button_updates[0], button_updates[1], button_updates[2], button_updates[3])
                else:
                    return ("❌ Response işaretlenemedi!", "", gr.update(), gr.update(),
                           gr.update(visible=False),  # Ana copy butonu gizli olsun
                           gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                           gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                           gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
        
        return ("❌ Yanıt bulunamadı!", "", gr.update(), gr.update(),
               gr.update(visible=False),  # Ana copy butonu gizli olsun
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
    except Exception as e:
        return (f"❌ Kopyalama hatası: {str(e)}", "", gr.update(), gr.update(),
               gr.update(visible=False),  # Ana copy butonu gizli olsun
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))

def new_request_handler():
    """Yeni istek - state'i temizle - eski koddan mantık"""
    # Session state'i temizle - eski koddan
    app_state['history'] = []
    app_state['current_response'] = None
    app_state['current_request_id'] = None
    app_state['response_count'] = 0
    
    # Durum makinesini sıfırla - eski koddan
    app_state['state'] = 'draft'
    app_state['yanit_sayisi'] = 0  # Yanıt sayısını sıfırla
    app_state['has_copied'] = False  # Kopyalama durumunu sıfırla
    
    # Buton görünürlüğünü güncelle
    generate_visible = app_state['state'] == 'draft' and app_state['yanit_sayisi'] < 5
    new_request_visible = app_state['state'] == 'finalized' or app_state['yanit_sayisi'] >= 5
    
    # Ana yanıt için boş display
    main_response_html = create_copyable_response_display()
    
    # Önceki yanıtlar HTML'ini oluştur
    previous_html = create_previous_responses_html()
    
    # Tüm akordiyonları gizle
    accordion_updates = [gr.update(visible=False)] * 4
    text_updates = [gr.update(visible=False)] * 4
    button_updates = [gr.update(visible=False)] * 4
    
    return (main_response_html, previous_html, gr.update(visible=generate_visible), gr.update(visible=new_request_visible),
           gr.update(visible=False),  # Ana copy butonu gizli olsun
           accordion_updates[0], accordion_updates[1], accordion_updates[2], accordion_updates[3],
           text_updates[0], text_updates[1], text_updates[2], text_updates[3],
           button_updates[0], button_updates[1], button_updates[2], button_updates[3])

# Gradio UI
with gr.Blocks(
    title="AI Helper - Nilüfer Belediyesi",
    theme=gr.themes.Soft(primary_hue="blue"),
    css="""
    .gradio-container {
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .main-container {
        width: 100% !important;
        max-width: none !important;
    }
    .container {
        max-width: none !important;
        width: 100% !important;
    }
    /* Tüm butonlar için güçlü CSS kuralları */
    button[data-testid="button"] {
        background: #3B82F6 !important;
        border-color: #3B82F6 !important;
        color: white !important;
    }
    button[data-testid="button"]:hover {
        background: #2563EB !important;
        border-color: #2563EB !important;
        color: white !important;
    }
    /* Primary butonlar için ekstra güçlü kurallar */
    .gr-button-primary, button.gr-button-primary {
        background: #3B82F6 !important;
        border-color: #3B82F6 !important;
        color: white !important;
    }
    .gr-button-primary:hover, button.gr-button-primary:hover {
        background: #2563EB !important;
        border-color: #2563EB !important;
        color: white !important;
    }
    /* Secondary butonlar için */
    .gr-button-secondary, button.gr-button-secondary {
        background: #3B82F6 !important;
        border-color: #3B82F6 !important;
        color: white !important;
    }
    .gr-button-secondary:hover, button.gr-button-secondary:hover {
        background: #2563EB !important;
        border-color: #2563EB !important;
        color: white !important;
    }
    /* Gradio'nun kendi buton sınıfları için */
    .gradio-button {
        background: #3B82F6 !important;
        border-color: #3B82F6 !important;
        color: white !important;
    }
    .gradio-button:hover {
        background: #2563EB !important;
        border-color: #2563EB !important;
        color: white !important;
    }
    /* Gradio footer'ını gizle */
    footer {
        display: none !important;
    }
    .gradio-footer {
        display: none !important;
    }
    /* Gradio'nun alt kısmındaki linkleri gizle */
    .gradio-container footer,
    .gradio-container .footer,
    .gradio-container [data-testid="footer"] {
        display: none !important;
    }
    /* Gradio'nun alt kısmındaki tüm footer elementlerini gizle */
    .gradio-container > div:last-child {
        display: none !important;
    }
    /* Kopyalanabilir textarea'ları gr.Textbox ile aynı yap */
    .gradio-textbox {
        background: var(--input-background-fill) !important;
        color: var(--body-text-color) !important;
        border-color: var(--border-color-primary) !important;
        border-style: solid !important;
        border-width: 1px !important;
        border-radius: var(--radius-lg) !important;
        padding: var(--spacing-lg) !important;
        font-family: var(--body-text-font) !important;
        font-size: var(--body-text-size) !important;
        line-height: var(--body-text-line-height) !important;
        box-shadow: var(--shadow-drop) !important;
        width: 100% !important;
        height: 200px !important;
        resize: vertical !important;
        cursor: pointer !important;
    }
    """
) as demo:
    
    
    
    # Logo'yu base64'e çevir
    def get_logo_base64():
        """Logo'yu base64'e çevir"""
        try:
            import base64
            with open("logo.png", "rb") as f:
                logo_data = base64.b64encode(f.read()).decode()
                return f"data:image/png;base64,{logo_data}"
        except FileNotFoundError:
            return None
    
    # Ana banner - JavaScript auth handler ile
    logo_base64 = get_logo_base64()
    
    if logo_base64:
        main_banner_html = f"""
        <div style="display: flex; align-items: center; padding: 2rem; background: #3B82F6; color: white; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 4px 8px rgba(0,0,0,0.1); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="background: white; border-radius: 12px; padding: 15px; margin-right: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <img src="{logo_base64}" alt="Nilüfer Belediyesi Logo" style="height: 150px; filter: brightness(1.1);">
            </div>
            <div style="flex: 1; text-align: center;">
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 600; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">AI Yardımcı</h1>
                <p style="margin: 0.3rem 0 0 0; font-size: 1rem; opacity: 0.9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">Nilüfer Belediyesi - Yapay Zeka Destekli Yanıt Üretim Sistemi</p>
            </div>
        </div>
        """
    else:
        main_banner_html = """
        <div style="text-align: center; padding: 2rem; background: #3B82F6; color: white; border-radius: 12px; margin-bottom: 2rem; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <h1 style="margin: 0; font-size: 2.2rem;">🏛️ AI Yardımcı</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.9;">Nilüfer Belediyesi - Yapay Zeka Destekli Yanıt Üretim Sistemi</p>
        </div>
        """
    
    main_banner = gr.HTML(main_banner_html)
    
    # JavaScript auth handler
    auth_script = """
    <script>
    function handleAuthFromUrl() {{
        console.log('Auth URL handler başlatıldı');
        
        const urlParams = new URLSearchParams(window.location.search);
        const authToken = urlParams.get('auth_token');
        const userEmail = urlParams.get('user_email');
        const userName = urlParams.get('user_name');
        const loginSuccess = urlParams.get('login_success');
        const error = urlParams.get('error');
        
        // Error handling
        if (error) {{
            let message = 'Giriş hatası';
            if (error === 'invalid_token') message = 'Geçersiz token';
            if (error === 'no_token') message = 'Token bulunamadı';
            if (error === 'auth_failed') message = 'Kimlik doğrulama başarısız';
            
            alert(message);
            window.history.replaceState({{}}, document.title, '/');
            return;
        }}
        
        // Başarılı giriş - Magic Link ile
        if (loginSuccess === 'true' && authToken && userEmail) {{
            console.log('Magic link ile başarılı giriş tespit edildi:', userEmail);
            console.log('Auth token:', authToken);
            console.log('User email:', userEmail);
            
            // LocalStorage'a kaydet
            localStorage.setItem('auth_token', authToken);
            localStorage.setItem('user_email', userEmail);
            localStorage.setItem('user_name', userName || '');
            localStorage.setItem('authenticated', 'true');
            localStorage.setItem('login_time', Date.now().toString());
            
            // URL'i temizle
            window.history.replaceState({{}}, document.title, '/');
            
            // Backend'e token doğrulama isteği gönder
            fetch('/api/v1/auth/verify-token', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{ token: authToken }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    console.log('Token backend\'de doğrulandı');
                    // Force show main app
                    setTimeout(() => {{
                        triggerMainApp();
                    }}, 500);
                }} else {{
                    console.error('Token doğrulama başarısız:', data.message);
                    alert('Token doğrulama başarısız');
                }}
            }})
            .catch(error => {{
                console.error('Token doğrulama hatası:', error);
                alert('Token doğrulama hatası');
            }});
        }}
    }}

    function triggerMainApp() {{
        // Force show button'ı bul ve tetikle
        const forceBtn = document.querySelector('button[data-testid*="force"]') ||
                        document.querySelector('button[aria-label*="Force"]') ||
                        Array.from(document.querySelectorAll('button')).find(btn => 
                            btn.textContent.includes('Force Show') || btn.textContent.includes('Ana Uygulama'));
        
        if (forceBtn) {{
            console.log('Force show button bulundu, tetikleniyor');
            forceBtn.click();
        }} else {{
            console.log('Force show button bulunamadı, sayfa yenileniyor');
            setTimeout(() => location.reload(), 1000);
        }}
    }}

    function checkExistingAuth() {{
        const authenticated = localStorage.getItem('authenticated');
        const authToken = localStorage.getItem('auth_token');
        
        if (authenticated === 'true' && authToken) {{
            console.log('Mevcut auth bulundu');
            setTimeout(() => triggerMainApp(), 1000);
        }}
    }}

    function copyToClipboard(text) {{
        navigator.clipboard.writeText(text).then(function() {{
            alert('✅ Yanıt kopyalandı! (Ctrl+V ile yapıştırabilirsiniz)');
        }}, function(err) {{
            console.error('Kopyalama hatası: ', err);
            alert('❌ Kopyalama hatası!');
        }});
    }}
    
    function copyPreviousResponse(responseId) {{
        // Önceki yanıtı kopyala ve seç
        navigator.clipboard.writeText('').then(function() {{
            // Gradio'ya önceki yanıtı kopyala sinyali gönder
            // Bu fonksiyon Gradio'nun event handler'ını tetikleyecek
            alert('✅ Önceki yanıt kopyalandı ve seçildi!');
        }}, function(err) {{
            console.error('Kopyalama hatası: ', err);
            alert('❌ Kopyalama hatası!');
        }});
    }}

    // Sayfa yüklendiğinde çalıştır
    document.addEventListener('DOMContentLoaded', function() {{
        handleAuthFromUrl();
        checkExistingAuth();
    }});

    // Global logout function
    window.logoutUser = function() {{
        localStorage.clear();
        location.reload();
    }};
    </script>
    """
    
    auth_handler = gr.HTML(auth_script, visible=False)
    
    # Login bölümü (başlangıçta görünür)
    login_title = gr.HTML("""
    <div style="text-align: center; padding: 2rem; background: #e8f5e8; border-radius: 12px; margin: 2rem 0;">
        <h2 style="color: #2e7d32; margin-bottom: 1rem;">🔐 AI Helper - Giriş</h2>
    </div>
    """, visible=False)
    
    login_subtitle = gr.HTML("""
    <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px; margin: 1rem 0;">
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 0.5rem;">Bursa Nilüfer Belediyesi AI Yardımcı sistemine hoş geldiniz</p>
    </div>
    """, visible=False)
    
    login_instruction = gr.HTML("""
    <div style="text-align: center; padding: 1rem; background: #fff3cd; border-radius: 8px; margin: 1rem 0;">
        <p style="color: #888; font-size: 0.9rem;">E-posta adresinizi girin, giriş için gerekli link ve kodu gönderelim</p>
    </div>
    """, visible=True)
    
    with gr.Row():
        with gr.Column(scale=1):
            pass
        with gr.Column(scale=2):
            with gr.Group():
                email_input = gr.Textbox(
                    label="E-posta Adresi",
                    placeholder="ornek@nilufer.bel.tr",
                    max_lines=1
                )
                send_code_btn = gr.Button("📧 Bağlantı ve Kod Gönder", variant="primary")
        with gr.Column(scale=1):
            pass
    
    # Kod doğrulama bölümü (başlangıçta gizli)
    code_title = gr.HTML("""
    <div style="text-align: center; padding: 2rem; background: #e3f2fd; border-radius: 12px; margin: 2rem 0;">
        <h2 style="color: #1976d2; margin-bottom: 1rem;">📧 Giriş için gerekli link ve kodu gönderdik</h2>
    </div>
    """, visible=False)
    
    code_subtitle = gr.HTML("""
    <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px; margin: 1rem 0;">
        <p style="color: #666; font-size: 1.1rem;">E-postandaki bağlantıya tıkla ya da aşağıya 6 haneli giriş kodunu yaz</p>
    </div>
    """, visible=False)
    
    with gr.Row():
        with gr.Column(scale=3):
            code_input = gr.Textbox(
                label="6 Haneli Giriş Kodu",
                placeholder="000000",
                max_lines=1,
                value="",
                visible=False
            )
        with gr.Column(scale=1):
            verify_btn = gr.Button("✅ Doğrula", variant="primary", visible=False)
    
    # Tekrar gönder ve geri dön butonları
    code_buttons = gr.Row(visible=False)
    with code_buttons:
        resend_btn = gr.Button("🔄 Tekrar gönder", variant="secondary")
        back_btn = gr.Button("⬅️ Geri Dön", variant="secondary")
    
    # Profil tamamlama alanı (başlangıçta gizli)
    with gr.Row(visible=False) as profile_completion_area:
        with gr.Column():
            profile_title = gr.HTML("""
            <div style="text-align: center; padding: 2rem; background: #e3f2fd; border-radius: 12px; margin: 2rem 0;">
                <h2 style="color: #1976d2; margin-bottom: 1rem; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">👤 Profil Bilgilerini Tamamlayın</h2>
                <p style="color: #666; font-size: 1.1rem; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">Lütfen aşağıdaki bilgileri doldurun</p>
            </div>
            """)
            
            with gr.Group():
                profile_name_input = gr.Textbox(
                    label="Ad Soyad",
                    placeholder="Adınız Soyadınız",
                    interactive=True
                )
                
                profile_department_input = gr.Dropdown(
                    label="Müdürlük",
                    choices=[
                        "Bilgi İşlem Müdürlüğü",
                        "İnsan Kaynakları Müdürlüğü", 
                        "Mali Hizmetler Müdürlüğü",
                        "Plan ve Proje Müdürlüğü",
                        "Kültür ve Sosyal İşler Müdürlüğü",
                        "Çevre Koruma ve Kontrol Müdürlüğü",
                        "İmar ve Şehircilik Müdürlüğü",
                        "Fen İşleri Müdürlüğü",
                        "Sağlık İşleri Müdürlüğü",
                        "Sosyal Yardım İşleri Müdürlüğü",
                        "Kültür ve Turizm Müdürlüğü",
                        "Basın Yayın ve Halkla İlişkiler Müdürlüğü",
                        "Hukuk İşleri Müdürlüğü",
                        "Strateji Geliştirme Müdürlüğü",
                        "İç Denetim Birimi",
                        "Özel Kalem Müdürlüğü",
                        "Destek Hizmetleri Müdürlüğü"
                    ],
                    interactive=True
                )
                
                complete_profile_btn = gr.Button("✅ Profili Tamamla", variant="primary")
                profile_error_msg = gr.HTML(visible=False)

    # Kullanıcı bilgileri ve çıkış butonu (başlangıçta gizli)
    with gr.Row(visible=False) as user_info_row:
        user_info_html = gr.HTML(visible=False)
        logout_btn = gr.Button("🚪 Çıkış Yap", variant="secondary", visible=False)
        force_show_btn = gr.Button("🔓 Ana Uygulama", variant="primary", visible=False)
    
    # Ana uygulama alanı (başlangıçta gizli)
    main_app_area = gr.Column(visible=False)
    with main_app_area:
        # Admin İstatistikler Paneli - sadece admin kullanıcılarda görünür
        admin_panel = gr.Accordion("📊 İstatistikler", open=False, visible=False)
        with admin_panel:
            admin_stats_html = gr.HTML(value="")
            refresh_admin_btn = gr.Button("🔄 Yenile", variant="secondary")
        
        # İki sütunlu layout
        with gr.Row():
            # Sol sütun - Giriş ve ayarlar
            with gr.Column(scale=1):
                gr.HTML("<h3 style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;'></h3>")
                original_text = gr.Textbox(
                    label="Gelen istek/öneri metnini buraya yapıştırın:",
                    value="Bursa Nilüfer'de bir dükkanım var ve yönetim planından tahsisli otoparkımda bulunan dubaları, belediye ekipleri mafyavari şekilde tahsisli alanımdan alıp götürebiliyor. Geri aradığımda ise belediye zabıtası, görevliyi mahkemeye vermemi söylüyor. Bu nasıl bir hizmet anlayışı? Benim tahsisli alanımdan eşyamı alıyorsunuz, buna ne denir? Herkes biliyordur. Bir yeri koruduğunu zannedip başka bir yeri mağdur etmek mi belediyecilik?",
                    lines=6
                )
                
                gr.HTML("<h3 style='font-family: \"Segoe UI\", Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;'></h3>")
                custom_input = gr.Textbox(
                    label="Hazırladığınız cevap taslağını buraya yazın:",
                    value="Orası size tahsis edilmiş bir yer değil. Nilüfer halkının ortak kullanım alanı. Kaldırımlar da öyle.",
                    lines=4
                )
                
                # Model ayarları - açılır kapanır (sadece admin için)
                with gr.Accordion("⚙️ Yanıt Ayarları", open=False, visible=False) as response_settings_accordion:
                    with gr.Row():
                        model = gr.Dropdown(
                            choices=["gemini-2.5-flash", "gemini-1.5-flash-002", "gemini-2.0-flash-001", "gpt-oss:latest"],
                            value="gemini-2.5-flash",
                            label="Model"
                        )
                        temperature = gr.Slider(
                            minimum=0.1,
                            maximum=2.0,
                            value=0.7,
                            step=0.1,
                            label="Yaratıcılık (Temperature)"
                        )
                    
                    max_tokens = gr.Slider(
                        minimum=100,
                        maximum=4000,
                        value=4000,
                        step=100,
                        label="Maksimum Token Sayısı"
                    )
                
                # Yanıt üret butonu
                generate_btn = gr.Button("🚀 Yanıt Üret", variant="primary", size="lg", visible=True)
            
            # Sağ sütun - Sonuçlar
            with gr.Column(scale=1):
                # Ana yanıt alanını HTML ile değiştirin
                main_response_html = gr.HTML(
                    value=create_copyable_response_display(),
                    label="Son Üretilen Yanıt"
                )
                
                # Ana Seç ve Kopyala butonu
                main_copy_btn = gr.Button("📋 Seç ve Kopyala", variant="primary", visible=False)
                copy_result = gr.Textbox(label="Kopyalama Durumu", interactive=False, visible=False)
                
                # Yeni istek öneri butonu
                new_request_btn = gr.Button("🆕 Yeni İstek Öneri Cevapla", variant="secondary", visible=False)
                
                # Önceki yanıtlar - dinamik HTML olarak göster
                previous_responses = gr.HTML()
                
                # Önceki yanıtlar için Gradio akordiyonları (maksimum 4 önceki yanıt)
                with gr.Column():
                    prev_accordion_1 = gr.Accordion("📄 Yanıt #1", open=False, visible=False)
                    with prev_accordion_1:
                        prev_text_1 = gr.HTML(visible=False, value="")
                        prev_copy_btn_1 = gr.Button("📋 Seç ve Kopyala #1", variant="primary", visible=False)
                    
                    prev_accordion_2 = gr.Accordion("📄 Yanıt #2", open=False, visible=False)
                    with prev_accordion_2:
                        prev_text_2 = gr.HTML(visible=False, value="")
                        prev_copy_btn_2 = gr.Button("📋 Seç ve Kopyala #2", variant="primary", visible=False)
                    
                    prev_accordion_3 = gr.Accordion("📄 Yanıt #3", open=False, visible=False)
                    with prev_accordion_3:
                        prev_text_3 = gr.HTML(visible=False, value="")
                        prev_copy_btn_3 = gr.Button("📋 Seç ve Kopyala #3", variant="primary", visible=False)
                    
                    prev_accordion_4 = gr.Accordion("📄 Yanıt #4", open=False, visible=False)
                    with prev_accordion_4:
                        prev_text_4 = gr.HTML(visible=False, value="")
                        prev_copy_btn_4 = gr.Button("📋 Seç ve Kopyala #4", variant="primary", visible=False)
    
    # Event handlers
    send_code_btn.click(
        fn=send_login_code,
        inputs=[email_input],
        outputs=[login_title, login_subtitle, login_instruction, email_input, send_code_btn, 
                code_title, code_subtitle, code_input, verify_btn, code_buttons]
    )
    
    verify_btn.click(
        fn=verify_login_code,
        inputs=[email_input, code_input],
        outputs=[code_title, code_subtitle, code_input, verify_btn, code_buttons, 
                email_input, user_info_row, user_info_html, logout_btn, force_show_btn, main_app_area, admin_panel, main_banner,
                profile_completion_area, profile_error_msg, response_settings_accordion]
    )
    
    complete_profile_btn.click(
        fn=complete_profile,
        inputs=[profile_name_input, profile_department_input],
        outputs=[profile_error_msg, profile_completion_area, user_info_row, user_info_html, 
                logout_btn, force_show_btn, main_app_area, admin_panel, main_banner]
    )
    
    logout_btn.click(
        fn=logout_user,
        inputs=[],
        outputs=[login_title, login_subtitle, login_instruction, email_input, send_code_btn, 
                code_title, code_subtitle, code_input, verify_btn, code_buttons, 
                user_info_row, user_info_html, logout_btn, force_show_btn, main_app_area, admin_panel, main_banner]
    )
    
    # Force show button
    force_show_btn.click(
        fn=force_show_main_app,
        inputs=[],
        outputs=[login_title, login_subtitle, login_instruction, email_input, send_code_btn, 
                code_title, code_subtitle, code_input, verify_btn, code_buttons, 
                user_info_row, user_info_html, logout_btn, force_show_btn, main_app_area, admin_panel, main_banner]
    )
    
    # Tekrar gönder butonu
    resend_btn.click(
        fn=lambda email: send_login_code(email),
        inputs=[email_input],
        outputs=[login_title, login_subtitle, login_instruction, email_input, send_code_btn, 
                code_title, code_subtitle, code_input, verify_btn, code_buttons]
    )
    
    # Geri dön butonu
    back_btn.click(
        fn=lambda: (
            gr.update(visible=True),  # login_title
            gr.update(visible=True),  # login_subtitle
            gr.update(visible=True),  # login_instruction
            gr.update(),  # email_input
            gr.update(visible=True),  # send_code_btn
            gr.update(visible=False),  # code_title
            gr.update(visible=False),  # code_subtitle
            gr.update(visible=False),  # code_input
            gr.update(visible=False),  # verify_btn
            gr.update(visible=False)  # code_buttons
        ),
        inputs=[],
        outputs=[login_title, login_subtitle, login_instruction, email_input, send_code_btn, 
                code_title, code_subtitle, code_input, verify_btn, code_buttons]
    )
    
    # Ana uygulama event handlers
    generate_btn.click(
        fn=generate_response_handler,
        inputs=[original_text, custom_input, model, temperature, max_tokens],
        outputs=[main_response_html, previous_responses, generate_btn, new_request_btn,
                main_copy_btn,  # Ana copy butonu
                prev_accordion_1, prev_accordion_2, prev_accordion_3, prev_accordion_4,
                prev_text_1, prev_text_2, prev_text_3, prev_text_4,
                prev_copy_btn_1, prev_copy_btn_2, prev_copy_btn_3, prev_copy_btn_4]
    )
    
    # Ana Seç ve Kopyala butonu event handler
    main_copy_btn.click(
        fn=lambda: copy_previous_response_handler(app_state['current_response']['id'] if app_state['current_response'] and app_state['current_response'].get('id') else None),
        inputs=[],
        outputs=[main_response_html, previous_responses, generate_btn, new_request_btn,
                main_copy_btn,  # Ana copy butonu
                prev_accordion_1, prev_accordion_2, prev_accordion_3, prev_accordion_4,
                prev_text_1, prev_text_2, prev_text_3, prev_text_4,
                prev_copy_btn_1, prev_copy_btn_2, prev_copy_btn_3, prev_copy_btn_4]
    )
    
    new_request_btn.click(
        fn=new_request_handler,
        inputs=[],
        outputs=[main_response_html, previous_responses, generate_btn, new_request_btn,
                main_copy_btn,  # Ana copy butonu
                prev_accordion_1, prev_accordion_2, prev_accordion_3, prev_accordion_4,
                prev_text_1, prev_text_2, prev_text_3, prev_text_4,
                prev_copy_btn_1, prev_copy_btn_2, prev_copy_btn_3, prev_copy_btn_4]
    )
    
    # Önceki yanıt butonları için event handler'lar
    prev_copy_btn_1.click(
        fn=lambda: copy_previous_response_handler(app_state['history'][1]['id'] if len(app_state['history']) > 1 else None),
        inputs=[],
        outputs=[main_response_html, previous_responses, generate_btn, new_request_btn,
                main_copy_btn,  # Ana copy butonu
                prev_accordion_1, prev_accordion_2, prev_accordion_3, prev_accordion_4,
                prev_text_1, prev_text_2, prev_text_3, prev_text_4,
                prev_copy_btn_1, prev_copy_btn_2, prev_copy_btn_3, prev_copy_btn_4]
    )
    
    prev_copy_btn_2.click(
        fn=lambda: copy_previous_response_handler(app_state['history'][2]['id'] if len(app_state['history']) > 2 else None),
        inputs=[],
        outputs=[main_response_html, previous_responses, generate_btn, new_request_btn,
                main_copy_btn,  # Ana copy butonu
                prev_accordion_1, prev_accordion_2, prev_accordion_3, prev_accordion_4,
                prev_text_1, prev_text_2, prev_text_3, prev_text_4,
                prev_copy_btn_1, prev_copy_btn_2, prev_copy_btn_3, prev_copy_btn_4]
    )
    
    prev_copy_btn_3.click(
        fn=lambda: copy_previous_response_handler(app_state['history'][3]['id'] if len(app_state['history']) > 3 else None),
        inputs=[],
        outputs=[main_response_html, previous_responses, generate_btn, new_request_btn,
                main_copy_btn,  # Ana copy butonu
                prev_accordion_1, prev_accordion_2, prev_accordion_3, prev_accordion_4,
                prev_text_1, prev_text_2, prev_text_3, prev_text_4,
                prev_copy_btn_1, prev_copy_btn_2, prev_copy_btn_3, prev_copy_btn_4]
    )
    
    prev_copy_btn_4.click(
        fn=lambda: copy_previous_response_handler(app_state['history'][4]['id'] if len(app_state['history']) > 4 else None),
        inputs=[],
        outputs=[main_response_html, previous_responses, generate_btn, new_request_btn,
                main_copy_btn,  # Ana copy butonu
                prev_accordion_1, prev_accordion_2, prev_accordion_3, prev_accordion_4,
                prev_text_1, prev_text_2, prev_text_3, prev_text_4,
                prev_copy_btn_1, prev_copy_btn_2, prev_copy_btn_3, prev_copy_btn_4]
    )
    
    # Admin paneli event handlers
    refresh_admin_btn.click(
        fn=refresh_admin_panel_handler,
        inputs=[],
        outputs=[admin_stats_html]
    )
    
    
    # Admin paneli görünürlüğünü kontrol et
    
    # Magic link kontrolü - sayfa yüklendiğinde auth_token'ı kontrol et
    demo.load(
        fn=check_auth_token,
        inputs=[],
        outputs=[
            login_title, login_subtitle, login_instruction, email_input, send_code_btn,
            code_title, code_subtitle, code_input, verify_btn, code_buttons,
            user_info_row, user_info_html, logout_btn, force_show_btn, main_app_area, admin_panel, main_banner,
            profile_completion_area, profile_error_msg, response_settings_accordion
        ]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=8500,
        share=False,
        show_error=True
    )
