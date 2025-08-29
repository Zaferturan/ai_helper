#!/usr/bin/env python3
import smtplib
import socket
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_port25_detailed():
    """Port 25 için detaylı SMTP test"""
    host = "mail.nilufer.bel.tr"
    port = 25
    
    print("🔌 Port 25 Detaylı SMTP Test")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print("-" * 50)
    
    try:
        # 1. Port bağlantısı
        print("1️⃣ Port bağlantısı test ediliyor...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result != 0:
            print("❌ Port 25 kapalı")
            return False
        
        print("✅ Port 25 açık")
        
        # 2. SMTP bağlantısı
        print("\n2️⃣ SMTP bağlantısı kuruluyor...")
        server = smtplib.SMTP(host, port, timeout=10)
        print("✅ SMTP bağlantısı kuruldu")
        
        # 3. EHLO
        print("\n3️⃣ EHLO komutu gönderiliyor...")
        try:
            response = server.ehlo()
            print(f"✅ EHLO başarılı: {response[0]}")
            print(f"   Sunucu özellikleri: {response[1]}")
        except Exception as e:
            print(f"❌ EHLO hatası: {str(e)}")
            return False
        
        # 4. Sunucu özelliklerini analiz et
        print("\n4️⃣ Sunucu özellikleri analiz ediliyor...")
        if hasattr(server, 'esmtp_features'):
            features = server.esmtp_features
            print("📋 ESMTP Özellikleri:")
            for feature, value in features.items():
                print(f"   - {feature}: {value}")
        else:
            print("ℹ️ ESMTP özellikleri bulunamadı")
        
        # 5. SMTP AUTH olmadan e-posta göndermeyi dene
        print("\n5️⃣ SMTP AUTH olmadan e-posta gönderimi deneniyor...")
        
        # Test e-postası hazırla
        msg = MIMEMultipart()
        msg['From'] = "test@nilufer.bel.tr"
        msg['To'] = "test@example.com"
        msg['Subject'] = "Test E-postası - Port 25"
        
        body = "Bu bir test e-postasıdır. Port 25 üzerinden gönderilmiştir."
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            # E-posta göndermeyi dene
            text = msg.as_string()
            server.sendmail("test@nilufer.bel.tr", ["test@example.com"], text)
            print("✅ E-posta gönderildi! (SMTP AUTH olmadan)")
            server.quit()
            return True
            
        except smtplib.SMTPRecipientsRefused as e:
            print(f"⚠️ Alıcı reddedildi: {str(e)}")
            print("   Bu normal - test e-postası olduğu için")
            
        except smtplib.SMTPDataError as e:
            print(f"⚠️ Veri hatası: {str(e)}")
            
        except Exception as e:
            print(f"❌ E-posta gönderme hatası: {type(e).__name__}: {str(e)}")
        
        # 6. Alternatif yöntemler
        print("\n6️⃣ Alternatif yöntemler deneniyor...")
        
        # HELO ile dene
        try:
            server.helo("localhost")
            print("✅ HELO başarılı")
        except Exception as e:
            print(f"❌ HELO hatası: {str(e)}")
        
        # 7. Sunucu bilgilerini al
        print("\n7️⃣ Sunucu bilgileri alınıyor...")
        try:
            if hasattr(server, 'sock'):
                sock_info = server.sock.getpeername()
                print(f"📡 Bağlantı bilgisi: {sock_info}")
        except:
            pass
        
        server.quit()
        print("\n✅ Test tamamlandı")
        return True
        
    except Exception as e:
        print(f"❌ Genel hata: {type(e).__name__}: {str(e)}")
        return False

def test_port25_with_auth():
    """Port 25 ile SMTP AUTH dene"""
    host = "mail.nilufer.bel.tr"
    port = 25
    username = "zaferturan"
    password = "6174858524"
    
    print("\n🔐 Port 25 + SMTP AUTH Test")
    print("=" * 50)
    
    try:
        server = smtplib.SMTP(host, port, timeout=10)
        print("✅ SMTP bağlantısı kuruldu")
        
        # EHLO
        server.ehlo()
        print("✅ EHLO başarılı")
        
        # SMTP AUTH dene
        try:
            server.login(username, password)
            print("🎉 SMTP AUTH başarılı!")
            server.quit()
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP AUTH hatası: {str(e)}")
            print("   Port 25 genellikle SMTP AUTH desteklemez")
        except Exception as e:
            print(f"❌ Diğer hata: {str(e)}")
        
        server.quit()
        return False
        
    except Exception as e:
        print(f"❌ Bağlantı hatası: {str(e)}")
        return False

def main():
    """Ana fonksiyon"""
    print("🚀 AI Helper Port 25 Detaylı Test")
    print("=" * 60)
    
    # Detaylı test
    success1 = test_port25_detailed()
    
    # SMTP AUTH test
    success2 = test_port25_with_auth()
    
    # Sonuçlar
    print("\n" + "=" * 60)
    print("📊 TEST SONUÇLARI:")
    print(f"   Port 25 Detaylı Test: {'✅ Başarılı' if success1 else '❌ Başarısız'}")
    print(f"   Port 25 + SMTP AUTH: {'✅ Başarılı' if success2 else '❌ Başarısız'}")
    
    if success1 and not success2:
        print("\n💡 SONUÇ:")
        print("   Port 25 açık ve çalışıyor")
        print("   Ancak SMTP AUTH desteklemiyor")
        print("   Bu durumda:")
        print("   1. Sunucu-arası e-posta gönderimi mümkün")
        print("   2. Kullanıcı e-postası için farklı port gerekli")
        print("   3. Veya SMTP AUTH destekleyen başka sunucu kullanılmalı")

if __name__ == "__main__":
    main() 