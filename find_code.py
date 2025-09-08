import hashlib

hash_target = 'a2595a581c9d43ef7e12d6e93f95ee9d356db7a51a64e3f899c059be9b6a1091'

print("Kod aranıyor...")
for i in range(100000, 1000000):
    code = f'{i:06d}'
    if hashlib.sha256(code.encode()).hexdigest() == hash_target:
        print(f"✅ Kod bulundu: {code}")
        break
else:
    print("❌ Kod bulunamadı")


