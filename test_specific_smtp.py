#!/usr/bin/env python3
import smtplib
import socket
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Test edilecek SMTP kombinasyonları
TEST_COMBINATIONS = [
    # Mevcut çalışan mail.nilufer.bel.tr
    ("mail.nilufer.bel.tr", 25, "zaferturan", "6174858524", "zaferturan@nilufer.bel.tr"),
    
    # Yeni ayarlar (DNS çözümlenemiyor)
    ("smtp.niluferyapayzeka.tr", 587, "yonetici", "BimOrtak12*", "yonetici@niluferyapayzeka.tr"),
    
    # Alternatif kombinasyonlar
    ("mail.nilufer.bel.tr", 587, "zaferturan", "6174858524", "zaferturan@nilufer.bel.tr"),
    ("mail.nilufer.bel.tr", 465, "zaferturan", "6174858524", "zaferturan@nilufer.bel.tr"),
    
    # IP adresi ile test
    ("95.0.15.58", 587, "zaferturan", "6174858524", "zaferturan@nilufer.bel.tr"),
    ("95.0.15.58", 465, "zaferturan", "6174858524", "zaferturan@nilufer.bel.tr"),
]

def test_smtp_combination(host, port, username, password, sender_email):
    """Belirli SMTP kombinasyonunu test et"""
    try:
        print(f"\n🔌 Test: {host}:{port}")
        print(f"   Username: {username}")
        print(f"   Sender: {sender_email}")
        print("-" * 50)
        
        # Port bağlantısını test et
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result != 0:
            print(f"❌ Port {port} kapalı")
            return False
        
        print(f"✅ Port {port} açık")
        
        # SMTP bağlantısını test et
        server = smtplib.SMTP(host, port, timeout=10)
        print(f"✅ SMTP bağlantısı kuruldu")
        
        # EHLO
        server.ehlo()
        print(f"✅ EHLO başarılı")
        
        # TLS (port 587 için)
        if port == 587:
            try:
                server.starttls()
                print(f"✅ TLS başlatıldı")
                server.ehlo()
            except Exception as e:
                print(f"⚠️ TLS hatası: {str(e)}")
        
        # SMTP AUTH
        try:
            server.login(username, password)
            print(f"✅ SMTP girişi başarılı!")
            server.quit()
            return True
        except Exception as e:
            print(f"⚠️ SMTP girişi başarısız: {str(e)}")
            server.quit()
            return False
            
    except Exception as e:
        print(f"❌ Genel hata: {type(e).__name__}: {str(e)}")
        return False

def main():
    """Ana fonksiyon"""
    print("🚀 AI Helper SMTP Kombinasyon Test Script'i")
    print("=" * 70)
    
    working_combinations = []
    
    for host, port, username, password, sender_email in TEST_COMBINATIONS:
        if test_smtp_combination(host, port, username, password, sender_email):
            working_combinations.append((host, port, username, password, sender_email))
            print(f"🎉 ÇALIŞAN KOMBİNASYON: {host}:{port}")
    
    # Sonuçlar
    print("\n" + "=" * 70)
    if working_combinations:
        print(f"🎉 Çalışan SMTP kombinasyonları:")
        for host, port, username, password, sender_email in working_combinations:
            print(f"   ✅ {host}:{port} - {username}")
        
        # .env güncelleme önerisi
        best_host, best_port, best_username, best_password, best_sender = working_combinations[0]
        print(f"\n📝 .env dosyasını güncellemek için:")
        print(f"SMTP_HOST={best_host}")
        print(f"SMTP_PORT={best_port}")
        print(f"SMTP_USERNAME={best_username}")
        print(f"SMTP_PASSWORD={best_password}")
        print(f"SENDER_EMAIL={best_sender}")
    else:
        print("❌ Hiçbir SMTP kombinasyonu çalışmıyor!")
        print("💡 Kontrol edilmesi gerekenler:")
        print("   - SMTP sunucu bilgileri")
        print("   - Kullanıcı adı ve şifre")
        print("   - Network/firewall ayarları")
        print("   - SMTP sunucusu aktif mi?")

if __name__ == "__main__":
    main() 