# Auth API entegrasyon rehberi (yeni uygulama)

Bu belge, **yzsrv** üzerinde çalışan yeni bir uygulamanın `nilufer_auth` (auth-api) ile Active Directory girişi yapması içindir. Uygulamayı yazan ajana / geliştiriciye verilir.

## Ne bu, ne değil

| Bu | Değil |
|----|--------|
| Senin uygulamanın kendi login ekranı | Ortak SSO kapısı / Caddy `forward_auth` |
| `POST /v1/login` ile AD doğrulama | Authelia / Authentik |
| Dönen JWT’yi senin oturumunda tutma | Auth’un senin UI’ını host etmesi |

Akış:

1. Kullanıcı senin login formuna kullanıcı adı + şifre yazar.
2. Uygulama (veya tarayıcı) auth-api’ye `POST /v1/login` atar.
3. Başarılıysa JWT + kullanıcı profili gelir → kendi session/cookie/store’una koyarsın.
4. Başarısızsa `401` → “Giriş başarısız” göster; AD hata kodunu kullanıcıya yansıtma.

## Ağ adresleri (aynı sunucu / Docker)

Auth stack `yapayzeka` Docker network’ünde çalışır.

| Kimden | Auth API tabanı | Ne zaman |
|--------|-----------------|----------|
| Başka konteyner (sunucu tarafı) | `http://auth-api:8000` | Backend login proxy veya token verify |
| Host / SSH tünel (geliştirme) | `http://127.0.0.1:8089` | Yerel curl / tünel |
| Tarayıcı → senin app origin’in | Aşağıya bak | CORS veya reverse proxy gerekir |

**Öneri (aynı sunucu):** Login isteğini **kendi backend’inden** `http://auth-api:8000`’e yap. Şifre tarayıcıdan doğrudan auth-api’ye gitmesin; CORS listesine her app eklemek zorunda kalmazsın.

```
Browser → senin-app (login form / API)
                ↓  Docker network
           auth-api:8000  POST /v1/login
                ↓
           Active Directory
```

Alternatif: Tarayıcıdan doğrudan auth-api’ye istek. O zaman auth tarafında `CORS_ORIGINS` içine senin origin’in eklenmeli (auth stack `.env` / yeniden deploy). Demo örneği: nginx ile `/v1` proxy (same-origin).

### Compose’da network

```yaml
services:
  my-app:
    networks:
      - yapayzeka
    environment:
      AUTH_API_URL: http://auth-api:8000

networks:
  yapayzeka:
    external: true
```

Servis adı: `auth-api` (container_name). Port konteyner içi: `8000`.

## Ortam değişkeni

```bash
AUTH_API_URL=http://auth-api:8000
```

Tarayıcıdan çağırıyorsan (proxy yoksa) public URL kullan; örneğin tünelde `http://127.0.0.1:8089`. Production’da edge/Caddy ile sabit bir host tercih edilir — o host CORS’a eklenmeli veya reverse proxy kullan.

## API sözleşmesi (v1)

Base: `{AUTH_API_URL}`

### `POST /v1/login`

Request:

```json
{ "username": "ornek.kullanici", "password": "..." }
```

Username biçimleri (hepsi kabul): `sam` | `DOMAIN\sam` | `sam@gunes.sistemi`  
Sunucu UPN bind yapar: `sam@gunes.sistemi`.

Başarı — `200`:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {
    "sam": "ornek.kullanici",
    "upn": "ornek.kullanici@gunes.sistemi",
    "display_name": "Örnek Kullanıcı",
    "mail": "ornek@nilufer.bel.tr",
    "dn": "CN=...,OU=...,DC=gunes,DC=sistemi"
  }
}
```

Hata:

| Kod | Anlam |
|-----|--------|
| `401` | Yanlış kullanıcı/şifre (genel mesaj) |
| `422` | Body eksik/geçersiz |
| `429` | Rate limit (IP) |

Şifreyi loglama, response’a yazma, tarayıcı `console`’una basma.

### `GET /v1/me`

Header: `Authorization: Bearer <access_token>`  
→ user profili (`sam`, `upn`, `display_name`, `mail`, `dn`) veya `401`.

### `POST /v1/verify`

Body: `{ "token": "<jwt>" }` **veya** Bearer header.  
→ `{ "valid": true, "claims": { ... } }` veya `{ "valid": false }`.

### Sağlık

- `GET /health` — process ayakta
- `GET /ready` — AD DC erişilebilir (`503` değilse hazır)

## Minimal örnekler

### Backend (önerilen) — Python

```python
import os
import httpx

AUTH_API_URL = os.environ["AUTH_API_URL"].rstrip("/")

async def ad_login(username: str, password: str) -> dict:
    r = await httpx.AsyncClient(timeout=15.0).post(
        f"{AUTH_API_URL}/v1/login",
        json={"username": username, "password": password},
    )
    if r.status_code == 401:
        raise PermissionError("invalid credentials")
    r.raise_for_status()
    return r.json()  # access_token, user, expires_in
```

### Backend — curl (smoke)

```bash
curl -sS -X POST "$AUTH_API_URL/v1/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"sam","password":"..."}'
```

### Frontend (yalnızca same-origin proxy veya CORS açıkken)

```javascript
const res = await fetch("/auth/v1/login", {  // kendi reverse proxy path'in
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
});
if (res.status === 401) { /* giriş başarısız */ }
if (!res.ok) { /* hata */ }
const { access_token, user, expires_in } = await res.json();
// access_token'ı güvenli sakla (httpOnly cookie tercih; localStorage riskli)
```

## JWT kullanımı

- Algoritma: HS256; secret yalnızca **auth-api**’de.
- Claims (özet): `sub` (= sam), `upn`, `display_name`, `mail`, `dn`, `exp`, `iat`.
- Uygulama seçenekleri:
  1. **Sadece login için kullan** — kendi session cookie’ni üret; sonraki isteklerde auth-api’ye gitme.
  2. **JWT’yi taşı** — korumalı route’larda `POST /v1/verify` veya `GET /v1/me` ile doğrula (her istekte veya cache’li).

`JWT_SECRET`’i başka uygulamaya kopyalama; imza doğrulamayı auth-api üzerinden yap.

Varsayılan süre: `expires_in` ≈ 28800 sn (8 saat). Süresi dolunca yeniden login.

## Uygulama checklist (ajan)

- [ ] Docker network: `yapayzeka` (external)
- [ ] `AUTH_API_URL=http://auth-api:8000`
- [ ] Kendi login UI (form: username + password)
- [ ] Server-side `POST {AUTH_API_URL}/v1/login`
- [ ] `200` → oturum aç; `user.display_name` / `mail` gösterilebilir
- [ ] `401` → genel “Giriş başarısız”
- [ ] Şifre / token loglanmıyor
- [ ] (İsteğe bağlı) Korunan API’lerde Bearer + `/v1/me` veya `/v1/verify`
- [ ] Tarayıcıdan doğrudan auth çağırıyorsan: CORS veya reverse proxy planı

## Bilinçli yapma

- AD LDAP’a doğrudan bağlanma (auth-api zaten yapıyor)
- Kullanıcıya AD `52e` vb. alt kod gösterme
- Auth demo UI’ını production login sanma (sadece test)
- `forward_auth` / merkezi SSO varsayımı

## Referans

- Repo: `nilufer_auth` — `stacks/auth/`
- Demo (referans UI): host `127.0.0.1:8088` (SSH tünel)
- API host bind: `127.0.0.1:8089` → konteyner `8000`
- Plan: [PLAN.md](PLAN.md) · bağlam: [CONTEXT.md](CONTEXT.md)
