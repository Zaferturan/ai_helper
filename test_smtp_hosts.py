#!/usr/bin/env python3
import smtplib
import socket
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Test edilecek SMTP host'ları
TEST_HOSTS = [
    "mail.nilufer.bel.tr",
    "smtp.nilufer.bel.tr", 
    "mail.nilufer.bel.tr",
    "95.0.15.58",  # IP adresi
    "smtp.gmail.com",  # Gmail test
    "smtp.office365.com"  # Office 365 test
]

# SMTP ayarları
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "zaferturan")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "6174858524")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "zaferturan@nilufer.bel.tr")

# Test edilecek portlar
TEST_PORTS = [25, 465, 587]

def test_host_connection(host, port, timeout=10):
    """Host ve port bağlantısını test et"""
    try:
        print(f"🔌 {host}:{port} test ediliyor...")
        
        # Socket ile bağlantı testi
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ {host}:{port} açık")
            return True
        else:
            print(f"❌ {host}:{port} kapalı")
            return False
            
    except Exception as e:
        print(f"❌ {host}:{port} hatası: {type(e).__name__}: {str(e)}")
        return False

def test_smtp_connection(host, port, timeout=10):
    """SMTP bağlantısını test et"""
    try:
        print(f"\n📧 SMTP {host}:{port} test ediliyor...")
        
        # SMTP bağlantısı
        server = smtplib.SMTP(host, port, timeout=timeout)
        print(f"✅ SMTP bağlantısı kuruldu")
        
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
        print(f"❌ SMTP hatası: {type(e).__name__}: {str(e)}")
        return False

def main():
    """Ana fonksiyon"""
    print("🚀 AI Helper SMTP Host Test Script'i")
    print("=" * 70)
    print(f"Username: {SMTP_USERNAME}")
    print(f"Sender: {SENDER_EMAIL}")
    print("=" * 70)
    
    working_combinations = []
    
    for host in TEST_HOSTS:
        print(f"\n🌐 Host: {host}")
        print("-" * 50)
        
        for port in TEST_PORTS:
            if test_host_connection(host, port):
                if test_smtp_connection(host, port):
                    working_combinations.append((host, port))
                    print(f"🎉 ÇALIŞAN KOMBİNASYON: {host}:{port}")
                    break  # Bu host için çalışan port bulundu
    
    # Sonuçlar
    print("\n" + "=" * 70)
    if working_combinations:
        print(f"🎉 Çalışan SMTP kombinasyonları:")
        for host, port in working_combinations:
            print(f"   ✅ {host}:{port}")
        
        # .env güncelleme önerisi
        best_host, best_port = working_combinations[0]
        print(f"\n📝 .env dosyasını güncellemek için:")
        print(f"SMTP_HOST={best_host}")
        print(f"SMTP_PORT={best_port}")
    else:
        print("❌ Hiçbir SMTP kombinasyonu çalışmıyor!")
        print("💡 Kontrol edilmesi gerekenler:")
        print("   - SMTP sunucu bilgileri")
        print("   - Kullanıcı adı ve şifre")
        print("   - Network/firewall ayarları")
        print("   - SMTP sunucusu aktif mi?")

if __name__ == "__main__":
    main() 