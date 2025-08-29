#!/usr/bin/env python3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# SMTP ayarları
SMTP_HOST = os.getenv("SMTP_HOST", "mail.nilufer.bel.tr")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "zaferturan")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "6174858524")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "zaferturan@nilufer.bel.tr")

def test_smtp_connection():
    """SMTP bağlantısını test et"""
    try:
        print(f"🔌 SMTP Bağlantısı test ediliyor...")
        print(f"Host: {SMTP_HOST}")
        print(f"Port: {SMTP_PORT}")
        print(f"Username: {SMTP_USERNAME}")
        print(f"Sender: {SENDER_EMAIL}")
        print("-" * 50)
        
        # SMTP bağlantısı
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        print("✅ SMTP bağlantısı kuruldu")
        
        # TLS başlat
        server.starttls()
        print("✅ TLS başlatıldı")
        
        # Giriş yap
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("✅ SMTP girişi başarılı")
        
        return server
        
    except Exception as e:
        print(f"❌ SMTP Hatası: {type(e).__name__}: {str(e)}")
        return None

def test_email_send(server, test_email="test@example.com"):
    """Test e-postası gönder"""
    try:
        print(f"\n📧 Test e-postası gönderiliyor...")
        print(f"Alıcı: {test_email}")
        
        # E-posta oluştur
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = test_email
        msg['Subject'] = "AI Helper - SMTP Test E-postası"
        
        # HTML içerik
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>SMTP Test</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5aa0;">AI Helper - SMTP Test E-postası</h2>
                <p>Merhaba,</p>
                <p>Bu bir test e-postasıdır. SMTP ayarları başarıyla çalışıyor!</p>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2c5aa0;">Test Detayları</h3>
                    <p><strong>SMTP Host:</strong> {}</p>
                    <p><strong>Port:</strong> {}</p>
                    <p><strong>Kullanıcı:</strong> {}</p>
                    <p><strong>Gönderici:</strong> {}</p>
                </div>
                <p>Test başarılı! 🎉</p>
            </div>
        </body>
        </html>
        """.format(SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SENDER_EMAIL)
        
        # Plain text içerik
        text_content = f"""
        AI Helper - SMTP Test E-postası
        
        Merhaba,
        
        Bu bir test e-postasıdır. SMTP ayarları başarıyla çalışıyor!
        
        Test Detayları:
        - SMTP Host: {SMTP_HOST}
        - Port: {SMTP_PORT}
        - Kullanıcı: {SMTP_USERNAME}
        - Gönderici: {SENDER_EMAIL}
        
        Test başarılı! 🎉
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        msg.attach(MIMEText(text_content, 'plain'))
        
        # E-postayı gönder
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, test_email, text)
        print("✅ Test e-postası başarıyla gönderildi!")
        
        return True
        
    except Exception as e:
        print(f"❌ E-posta gönderme hatası: {type(e).__name__}: {str(e)}")
        return False

def main():
    """Ana fonksiyon"""
    print("🚀 AI Helper SMTP Test Script'i")
    print("=" * 50)
    
    # SMTP bağlantısını test et
    server = test_smtp_connection()
    if not server:
        print("\n❌ SMTP bağlantısı başarısız!")
        return
    
    # Test e-postası gönder
    test_email = input("\n📧 Test e-postası göndermek istediğiniz adresi girin (Enter = test@example.com): ").strip()
    if not test_email:
        test_email = "test@example.com"
    
    success = test_email_send(server, test_email)
    
    # Bağlantıyı kapat
    server.quit()
    print("✅ SMTP bağlantısı kapatıldı")
    
    if success:
        print("\n🎉 Tüm testler başarılı! SMTP ayarları çalışıyor.")
    else:
        print("\n❌ E-posta gönderimi başarısız!")

if __name__ == "__main__":
    main() 