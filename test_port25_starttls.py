#!/usr/bin/env python3
import smtplib
import socket
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_port25_starttls():
    """Port 25'te STARTTLS ile SMTP AUTH test"""
    host = "mail.nilufer.bel.tr"
    port = 25
    username = "zaferturan"
    password = "6174858524"
    
    print("🔌 Port 25 + STARTTLS + SMTP AUTH Test")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print("-" * 60)
    
    try:
        # 1. SMTP bağlantısı
        print("1️⃣ SMTP bağlantısı kuruluyor...")
        server = smtplib.SMTP(host, port, timeout=10)
        print("✅ SMTP bağlantısı kuruldu")
        
        # 2. EHLO
        print("\n2️⃣ EHLO komutu gönderiliyor...")
        response = server.ehlo()
        print(f"✅ EHLO başarılı: {response[0]}")
        
        # 3. STARTTLS
        print("\n3️⃣ STARTTLS başlatılıyor...")
        try:
            server.starttls()
            print("✅ STARTTLS başarılı")
            
            # 4. TLS sonrası EHLO
            print("\n4️⃣ TLS sonrası EHLO...")
            response = server.ehlo()
            print(f"✅ TLS sonrası EHLO başarılı: {response[0]}")
            
            # 5. SMTP AUTH
            print("\n5️⃣ SMTP AUTH deneniyor...")
            try:
                server.login(username, password)
                print("🎉 SMTP AUTH başarılı!")
                
                # 6. Test e-postası gönder
                print("\n6️⃣ Test e-postası gönderiliyor...")
                msg = MIMEMultipart()
                msg['From'] = f"{username}@nilufer.bel.tr"
                msg['To'] = f"{username}@nilufer.bel.tr"  # Kendine gönder
                msg['Subject'] = "Port 25 STARTTLS Test"
                
                body = "Bu e-posta Port 25 + STARTTLS + SMTP AUTH ile gönderilmiştir."
                msg.attach(MIMEText(body, 'plain'))
                
                text = msg.as_string()
                server.sendmail(f"{username}@nilufer.bel.tr", [f"{username}@nilufer.bel.tr"], text)
                print("✅ Test e-postası gönderildi!")
                
                server.quit()
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                print(f"❌ SMTP AUTH hatası: {str(e)}")
                print("   STARTTLS sonrası da SMTP AUTH desteklenmiyor")
                
            except Exception as e:
                print(f"❌ Diğer hata: {type(e).__name__}: {str(e)}")
            
        except Exception as e:
            print(f"❌ STARTTLS hatası: {str(e)}")
            print("   STARTTLS başlatılamadı")
        
        server.quit()
        return False
        
    except Exception as e:
        print(f"❌ Genel hata: {type(e).__name__}: {str(e)}")
        return False

def test_port25_starttls_no_auth():
    """Port 25'te STARTTLS ile SMTP AUTH olmadan e-posta gönder"""
    host = "mail.nilufer.bel.tr"
    port = 25
    
    print("\n📧 Port 25 + STARTTLS (SMTP AUTH olmadan) Test")
    print("=" * 60)
    
    try:
        # 1. SMTP bağlantısı
        print("1️⃣ SMTP bağlantısı kuruluyor...")
        server = smtplib.SMTP(host, port, timeout=10)
        print("✅ SMTP bağlantısı kuruldu")
        
        # 2. EHLO
        print("\n2️⃣ EHLO komutu gönderiliyor...")
        server.ehlo()
        print("✅ EHLO başarılı")
        
        # 3. STARTTLS
        print("\n3️⃣ STARTTLS başlatılıyor...")
        server.starttls()
        print("✅ STARTTLS başarılı")
        
        # 4. TLS sonrası EHLO
        print("\n4️⃣ TLS sonrası EHLO...")
        server.ehlo()
        print("✅ TLS sonrası EHLO başarılı")
        
        # 5. E-posta gönder (SMTP AUTH olmadan)
        print("\n5️⃣ E-posta gönderimi deneniyor...")
        
        msg = MIMEMultipart()
        msg['From'] = "test@nilufer.bel.tr"
        msg['To'] = "test@nilufer.bel.tr"
        msg['Subject'] = "Port 25 STARTTLS Test - No Auth"
        
        body = "Bu e-posta Port 25 + STARTTLS ile SMTP AUTH olmadan gönderilmiştir."
        msg.attach(MIMEText(body, 'plain'))
        
        text = msg.as_string()
        
        try:
            server.sendmail("test@nilufer.bel.tr", ["test@nilufer.bel.tr"], text)
            print("✅ E-posta gönderildi! (SMTP AUTH olmadan)")
            server.quit()
            return True
            
        except smtplib.SMTPRecipientsRefused as e:
            print(f"⚠️ Alıcı reddedildi: {str(e)}")
            print("   Relay kısıtlaması var")
            
        except Exception as e:
            print(f"❌ E-posta gönderme hatası: {type(e).__name__}: {str(e)}")
        
        server.quit()
        return False
        
    except Exception as e:
        print(f"❌ Genel hata: {type(e).__name__}: {str(e)}")
        return False

def main():
    """Ana fonksiyon"""
    print("🚀 AI Helper Port 25 STARTTLS Test")
    print("=" * 70)
    
    # STARTTLS + SMTP AUTH test
    success1 = test_port25_starttls()
    
    # STARTTLS (SMTP AUTH olmadan) test
    success2 = test_port25_starttls_no_auth()
    
    # Sonuçlar
    print("\n" + "=" * 70)
    print("📊 TEST SONUÇLARI:")
    print(f"   Port 25 + STARTTLS + SMTP AUTH: {'✅ Başarılı' if success1 else '❌ Başarısız'}")
    print(f"   Port 25 + STARTTLS (No Auth): {'✅ Başarılı' if success2 else '❌ Başarısız'}")
    
    if success1:
        print("\n🎉 SONUÇ:")
        print("   Port 25 + STARTTLS + SMTP AUTH çalışıyor!")
        print("   Bu kombinasyon ile e-posta gönderimi mümkün")
        
    elif success2:
        print("\n⚠️ SONUÇ:")
        print("   Port 25 + STARTTLS çalışıyor")
        print("   Ancak SMTP AUTH desteklenmiyor")
        print("   Sadece sunucu-arası e-posta gönderimi mümkün")
        
    else:
        print("\n❌ SONUÇ:")
        print("   Port 25'te STARTTLS de çalışmıyor")
        print("   Alternatif port veya SMTP servisi gerekli")

if __name__ == "__main__":
    main() 