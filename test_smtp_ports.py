#!/usr/bin/env python3
import smtplib
import socket
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# SMTP ayarları
SMTP_HOST = os.getenv("SMTP_HOST", "mail.nilufer.bel.tr")
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "zaferturan")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "6174858524")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "zaferturan@nilufer.bel.tr")

# Test edilecek portlar
TEST_PORTS = [25, 465, 587, 2525, 8025]

def test_port_connection(host, port, timeout=10):
    """Belirli bir portta bağlantı test et"""
    try:
        print(f"🔌 Port {port} test ediliyor...")
        
        # Socket ile bağlantı testi
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} açık")
            return True
        else:
            print(f"❌ Port {port} kapalı")
            return False
            
    except Exception as e:
        print(f"❌ Port {port} hatası: {type(e).__name__}: {str(e)}")
        return False

def test_smtp_port(host, port, timeout=10):
    """SMTP port testi"""
    try:
        print(f"\n📧 SMTP Port {port} test ediliyor...")
        
        # SMTP bağlantısı
        server = smtplib.SMTP(host, port, timeout=timeout)
        print(f"✅ SMTP bağlantısı kuruldu (Port {port})")
        
        # Sunucu bilgilerini al
        server.ehlo()
        print(f"✅ EHLO başarılı")
        
        # TLS desteği kontrol et
        if port == 587:
            try:
                server.starttls()
                print(f"✅ TLS başlatıldı")
                server.ehlo()
            except Exception as e:
                print(f"⚠️ TLS hatası: {str(e)}")
        
        # Giriş denemesi
        try:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print(f"✅ SMTP girişi başarılı!")
            server.quit()
            return True
        except Exception as e:
            print(f"⚠️ SMTP girişi başarısız: {str(e)}")
            server.quit()
            return False
            
    except Exception as e:
        print(f"❌ SMTP Port {port} hatası: {type(e).__name__}: {str(e)}")
        return False

def main():
    """Ana fonksiyon"""
    print("🚀 AI Helper SMTP Port Test Script'i")
    print("=" * 60)
    print(f"Host: {SMTP_HOST}")
    print(f"Username: {SMTP_USERNAME}")
    print(f"Sender: {SENDER_EMAIL}")
    print("=" * 60)
    
    # Önce port bağlantılarını test et
    print("\n🔍 Port bağlantı testleri:")
    open_ports = []
    
    for port in TEST_PORTS:
        if test_port_connection(SMTP_HOST, port):
            open_ports.append(port)
    
    if not open_ports:
        print("\n❌ Hiçbir port açık değil!")
        print("💡 Olası sebepler:")
        print("   - Firewall engeli")
        print("   - SMTP sunucusu çalışmıyor")
        print("   - Host adresi yanlış")
        return
    
    print(f"\n✅ Açık portlar: {open_ports}")
    
    # SMTP testleri
    print("\n📧 SMTP testleri:")
    working_ports = []
    
    for port in open_ports:
        if test_smtp_port(SMTP_HOST, port):
            working_ports.append(port)
    
    # Sonuçlar
    print("\n" + "=" * 60)
    if working_ports:
        print(f"🎉 Çalışan SMTP portları: {working_ports}")
        print(f"💡 Önerilen port: {working_ports[0]}")
        
        # .env güncelleme önerisi
        print(f"\n📝 .env dosyasını güncellemek için:")
        print(f"SMTP_PORT={working_ports[0]}")
    else:
        print("❌ Hiçbir SMTP portu çalışmıyor!")
        print("💡 Kontrol edilmesi gerekenler:")
        print("   - SMTP kullanıcı adı ve şifre")
        print("   - SMTP sunucu ayarları")
        print("   - Network bağlantısı")

if __name__ == "__main__":
    main() 