# Diğer ajana yapıştırılacak prompt — İstek Öneri + AD login

Aşağıdaki bloğu **olduğu gibi** istek öneri yardımcısı projesindeki Agent sohbetine yapıştır.

---

```
Görev: yzsrv’de çalışan İstek Öneri Yardımcısı uygulamasına Active Directory login ekle.
Kimlik doğrulama için mevcut nilufer_auth (auth-api) servisini kullan. AD/LDAP’a doğrudan bağlanma.

## Kritik ayrım (karıştırma)

- Active Directory’ye SSH tüneli AÇMAZSIN. DC’ye (192.168.1.11) lokalinden tünel kurma.
- AD’ye bağlanan tek servis: yzsrv’deki auth-api (Docker, zaten ayakta).
- SSH tüneli sadece şunun için: kendi PC’nden yzsrv localhost portlarına erişip demo/test etmek
  (auth-api :8089, istek-öneri UI portu, vs.).
- Aynı sunucuda konteyner ↔ konteyner: Docker network `yapayzeka`, adres `http://auth-api:8000`.

Akış:
  Browser → İstek Öneri (kendi login formu)
         → backend (önerilen) POST http://auth-api:8000/v1/login
         → auth-api → AD (LDAP, yzsrv LAN)
         ← JWT + user profil
         → senin session/cookie

## ai_helper .env_AD — hangi değişken, kim kullanır

Dosya (okuma; şifreleri sohbete/log’a basma):
  /media/yapayzeka/depo/cursor projects/ai_helper/.env_AD

### A) SSH ile yzsrv’ye bağlanmak / tünel (sen kullanırsın)

| Değişken | Kullanım |
|----------|----------|
| `ssh_user` | SSH kullanıcı |
| `ssh_password` | SSH (+ gerekirse sudo); `SSHPASS` olarak export |
| `ssh_host` | Tercihen Tailscale `100.66.128.121` veya `yzsrv` |

Bağlanma kalıbı (zorunlu):
```bash
set -a; source "/media/yapayzeka/depo/cursor projects/ai_helper/.env_AD"; set +a
export SSHPASS="$ssh_password"
# Tek seferlik komut:
sshpass -e ssh -T -o StrictHostKeyChecking=accept-new "${ssh_user}@${ssh_host}" 'hostname; docker ps --filter name=auth'
# Auth API tüneli (yerel test; arka planda bırak):
sshpass -e ssh -N -o StrictHostKeyChecking=accept-new \
  -L 8089:127.0.0.1:8089 \
  "${ssh_user}@${ssh_host}"
# Sonra yerelden: curl http://127.0.0.1:8089/health
```

İstek öneri UI’sı yzsrv’de hangi host porta bağlıysa onu da aynı şekilde `-L YEREL:127.0.0.1:UZAK` ile ekle.
Tüneli iş bitince kapat (ssh process kill).

### B) AD smoke test hesabı (opsiyonel; login denemesi)

| Değişken | Kullanım |
|----------|----------|
| `bel_user` | Test AD kullanıcı (sam) |
| `bel_password` | Test şifre — ASLA log/commit/sohbet |
| `bel_domain` | Genelde `gunes.sistemi` (bilgi; login’de sam yeter) |

Bunlar yorum satırındaysa (`# bel_user=...`) önce satır başındaki `#` kaldırılmış olmalı.
Başarılı login smoke (tünel açıkken veya SSH üzerinden yzsrv localhost’ta):

```bash
set -a; source "/media/yapayzeka/depo/cursor projects/ai_helper/.env_AD"; set +a
curl -sS -X POST http://127.0.0.1:8089/v1/login \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"${bel_user}\",\"password\":\"${bel_password}\"}"
# 200 + access_token beklenir; token’ı yanıtta tam basma / loglama
```

### C) İstek öneri uygulamasının KENDİ env’i (auth-api’nin .env’ini kopyalama)

Uygulama konteynerine / compose’a koy:

| Değişken | Değer | Not |
|----------|-------|-----|
| `AUTH_API_URL` | `http://auth-api:8000` | Docker içi zorunlu adres |
| (opsiyonel) session secret | kendi ürettiğin | auth JWT_SECRET değil |

Şunları istek-öneri’ye KOYMA / kopyalama:
- `JWT_SECRET`, `AD_LDAP_URL`, `AD_DOMAIN`, `AD_BASE_DN` → bunlar yalnız auth-api’de
- `ssh_*` → yalnız ajanın deploy/tünel işi için; app’e gömme
- `bel_*` → yalnız manuel smoke test; production’a gömme

CORS: Tarayıcıdan doğrudan auth-api’ye gideceksen nilufer_auth tarafında `CORS_ORIGINS`’e
istek-öneri origin’ini ekletmek gerekir. ÖNERİLEN: login’i kendi backend’inden
`AUTH_API_URL` ile yap → CORS gerekmez.

## Auth API sözleşmesi (ezber)

Base (Docker): `http://auth-api:8000`
Base (SSH tünel / host): `http://127.0.0.1:8089`

- `POST /v1/login` body: `{"username","password"}`
  → 200: `{access_token, token_type:"bearer", expires_in, user:{sam,upn,display_name,mail,dn}}`
  → 401: genel hata (AD alt kodunu kullanıcıya gösterme)
- `GET /v1/me` — `Authorization: Bearer <token>`
- `POST /v1/verify` — token geçerli mi?
- `GET /health`, `GET /ready`

Username: `sam` / `DOMAIN\sam` / `sam@gunes.sistemi` hepsi olur.

## Ne yap / ne yapma

Yap:
1. İstek öneri reposunu/stack’ini bul (yzsrv Docker / yerel proje).
2. Network’e `yapayzeka` (external) ekle; `AUTH_API_URL=http://auth-api:8000`.
3. Login ekranı ekle (veya varsa bağla); backend `POST .../v1/login`.
4. 200 → oturum aç (kendi session’ın); 401 → “Giriş başarısız”.
5. SSH tünel ile smoke test; şifre/token loglama.

Yapma:
- ldap3 ile DC’ye direkt bağlanma
- Authelia / Authentik / Caddy forward_auth varsayma
- nilufer_auth JWT_SECRET ile kendi imza doğrulaman (verify için auth-api kullan)
- .env sırlarını commit / sohbete yapıştırma

## Referans (oku, yeniden keşfetme)

- Entegrasyon: `/media/yapayzeka/depo/cursor projects/nilufer_auth/docs/INTEGRATION.md`
- Auth stack: `/media/yapayzeka/depo/cursor projects/nilufer_auth/stacks/auth/`
- Auth zaten yzsrv’de: `~/stacks/auth/` — container `auth-api`, `auth-demo`

Başla: önce yzsrv’de `auth-api` healthy mi kontrol et; sonra istek öneri compose/koduna login entegre et.
```
