#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# Database bağlantısı
db_url = os.getenv('DATABASE_URL', 'postgresql://engin:BimOrtak12*@postgr_server:5432/postgres')

try:
    engine = create_engine(db_url)
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    with engine.connect() as conn:
        # Model bazında istatistikler
        print("=" * 80)
        print("GEMINI API KULLANIM İSTATİSTİKLERİ (SON 7 GÜN)")
        print("=" * 80)
        
        query = text("""
            SELECT 
                model_name,
                COUNT(*) as request_count,
                COALESCE(SUM(tokens_used), 0) as total_tokens,
                COALESCE(ROUND(AVG(tokens_used), 0), 0) as avg_tokens,
                MIN(created_at) as first_request,
                MAX(created_at) as last_request
            FROM ai_helper.responses
            WHERE model_name LIKE '%gemini%'
                AND created_at >= :seven_days_ago
            GROUP BY model_name
            ORDER BY request_count DESC
        """)
        
        result = conn.execute(query, {'seven_days_ago': seven_days_ago})
        rows = result.fetchall()
        
        total_requests = 0
        total_tokens = 0
        
        for row in rows:
            total_requests += row.request_count
            total_tokens += row.total_tokens
            
            print(f"\n📊 Model: {row.model_name}")
            print(f"   Request Sayısı: {row.request_count:,}")
            print(f"   Toplam Token: {row.total_tokens:,}")
            print(f"   Ortalama Token/Request: {row.avg_tokens:,.0f}")
            print(f"   İlk Request: {row.first_request}")
            print(f"   Son Request: {row.last_request}")
        
        # Günlük dağılım
        print("\n" + "=" * 80)
        print("GÜNLÜK DAĞILIM")
        print("=" * 80)
        
        query2 = text("""
            SELECT 
                DATE(created_at) as request_date,
                COUNT(*) as daily_requests,
                COALESCE(SUM(tokens_used), 0) as daily_tokens
            FROM ai_helper.responses
            WHERE model_name LIKE '%gemini%'
                AND created_at >= :seven_days_ago
            GROUP BY DATE(created_at)
            ORDER BY request_date DESC
        """)
        
        result2 = conn.execute(query2, {'seven_days_ago': seven_days_ago})
        
        for row in result2:
            cost_tl = (row.daily_tokens / 1_000_000) * 0.30 * 34
            print(f"📅 {row.request_date}: {row.daily_requests:,} request | {row.daily_tokens:,} token | ~{cost_tl:.2f} TL")
        
        # Toplam maliyet
        print("\n" + "=" * 80)
        print("TOPLAM ÖZET")
        print("=" * 80)
        print(f"🔢 Toplam Gemini Request: {total_requests:,}")
        print(f"🎯 Toplam Token Kullanımı: {total_tokens:,}")
        
        # Tahmini maliyet (Gemini 2.0 Flash pricing)
        estimated_cost_usd = (total_tokens / 1_000_000) * 0.20
        estimated_cost_tl = estimated_cost_usd * 34
        
        print(f"💰 Tahmini Maliyet: ${estimated_cost_usd:.2f} USD (~{estimated_cost_tl:.2f} TL)")
        print("=" * 80)
        
        if estimated_cost_tl > 100:
            print("\n⚠️  UYARI: Haftalık maliyet 100 TL'yi aştı!")
        if total_requests > 1000:
            print(f"⚠️  UYARI: Haftalık {total_requests:,} request yapılmış!")
            
except Exception as e:
    print(f"❌ Hata: {e}", file=sys.stderr)
    sys.exit(1)
