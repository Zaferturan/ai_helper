#!/usr/bin/env python3
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

def test_google_workspace_smtp():
    """Google Workspace SMTP test"""
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    sender_email = os.getenv("SENDER_EMAIL", "")
    
    print("🔌 Google Workspace SMTP Test")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print(f"Sender: {sender_email}")
    print("-" * 60)
    
    try:
        # 1. SMTP bağlantısı
        print("1️⃣ SMTP bağlantısı kuruluyor...")
        server = smtplib.SMTP(host, port, timeout=30)
        print("✅ SMTP bağlantısı kuruldu")
        
        # 2. EHLO
        print("\n2️⃣ EHLO komutu gönderiliyor...")
        response = server.ehlo()
        print(f"✅ EHLO başarılı: {response[0]}")
        print(f"   Sunucu özellikleri: {response[1]}")
        
        # 3. STARTTLS
        print("\n3️⃣ STARTTLS başlatılıyor...")
        server.starttls(context=ssl.create_default_context())
        print("✅ STARTTLS başarılı")
        
        # 4. TLS sonrası EHLO
        print("\n4️⃣ TLS sonrası EHLO...")
        response = server.ehlo()
        print(f"✅ TLS sonrası EHLO başarılı: {response[0]}")
        
        # 5. SMTP AUTH
        print("\n5️⃣ SMTP AUTH deneniyor...")
        print(f"   Username: {username}")
        print(f"   Password: {'*' * len(password) if password else 'BOŞ'}")
        
        try:
            server.login(username, password)
            print("🎉 SMTP AUTH başarılı!")
            
            # 6. Test e-postası gönder
            print("\n6️⃣ Test e-postası gönderiliyor...")
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = username  # Kendine gönder
            msg['Subject'] = "Google Workspace SMTP Test"
            
            body = f"""
            Bu e-posta Google Workspace SMTP ile gönderilmiştir.
            
            Test Detayları:
            - Host: {host}
            - Port: {port}
            - Username: {username}
            - Sender: {sender_email}
            
            Test başarılı! 🎉
            """
            
            msg.attach(MIMEText(body, 'plain'))
            text = msg.as_string()
            
            server.sendmail(sender_email, [username], text)
            print("✅ Test e-postası gönderildi!")
            
            server.quit()
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP AUTH hatası: {str(e)}")
            print("\n💡 Hata Analizi:")
            print("   - Username doğru mu?")
            print("   - App Password doğru mu?")
            print("   - 2-adımlı doğrulama etkin mi?")
            print("   - IMAP/SMTP etkin mi?")
            
        except Exception as e:
            print(f"❌ Diğer hata: {type(e).__name__}: {str(e)}")
        
        server.quit()
        return False
        
    except Exception as e:
        print(f"❌ Genel hata: {type(e).__name__}: {str(e)}")
        return False

def test_alternative_ports():
    """Alternatif port'ları test et"""
    host = "smtp.gmail.com"
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    
    print("\n🔌 Alternatif Port Test")
    print("=" * 40)
    
    ports = [587, 465, 25]
    
    for port in ports:
        try:
            print(f"\nPort {port} test ediliyor...")
            
            if port == 465:
                # SSL port
                server = smtplib.SMTP_SSL(host, port, timeout=10)
                print(f"✅ Port {port} (SSL) bağlantısı kuruldu")
            else:
                # Normal port
                server = smtplib.SMTP(host, port, timeout=10)
                print(f"✅ Port {port} bağlantısı kuruldu")
                
                if port == 587:
                    server.starttls(context=ssl.create_default_context())
                    print(f"✅ Port {port} TLS başlatıldı")
            
            # EHLO
            server.ehlo()
            print(f"✅ Port {port} EHLO başarılı")
            
            # SMTP AUTH
            try:
                server.login(username, password)
                print(f"🎉 Port {port} SMTP AUTH başarılı!")
                server.quit()
                return port
            except Exception as e:
                print(f"❌ Port {port} SMTP AUTH hatası: {str(e)}")
            
            server.quit()
            
        except Exception as e:
            print(f"❌ Port {port} hatası: {str(e)}")
    
    return None

def main():
    """Ana fonksiyon"""
    print("🚀 AI Helper Google Workspace SMTP Test")
    print("=" * 70)
    
    # Ana test
    success = test_google_workspace_smtp()
    
    if not success:
        print("\n🔄 Alternatif port'lar deneniyor...")
        working_port = test_alternative_ports()
        
        if working_port:
            print(f"\n🎉 Port {working_port} çalışıyor!")
            print(f"   .env dosyasında SMTP_PORT={working_port} yapın")
        else:
            print("\n❌ Hiçbir port çalışmıyor!")
    
    # Sonuç
    print("\n" + "=" * 70)
    if success:
        print("🎉 Google Workspace SMTP testi başarılı!")
    else:
        print("❌ Google Workspace SMTP testi başarısız!")
        print("\n💡 Kontrol edilmesi gerekenler:")
        print("   1. Username doğru mu?")
        print("   2. App Password doğru mu?")
        print("   3. 2-adımlı doğrulama etkin mi?")
        print("   4. IMAP/SMTP etkin mi?")
        print("   5. Domain'de SMTP kısıtlaması var mı?")

if __name__ == "__main__":
    main() 