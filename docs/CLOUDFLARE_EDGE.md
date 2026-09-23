# Cloudflare / edge hardening (Faz 6)

Target architecture: **all public traffic → origin `localhost:8500` (nginx)**. Nginx proxies `/api/` to loopback uvicorn `:8000`. Do **not** publish host port 8000.

## Hop rules (simplify)

| Path pattern | Target |
|--------------|--------|
| `*` (including `/api/v1/*`, `/static/*`, `/manifest*`) | `http://localhost:8500` |

Remove any hops that still point API/static/manifest at `:8000`.

**Interim (until hops updated):** origin may publish **both** `8500:80` and `8000:80` mapped to **nginx** (not uvicorn). Legacy CF hops to `:8000` then still work. After all Public Hostnames use `:8500`, drop the `8000:80` publish.

> Status: hops migrated to `:8500`; Docker publishes **only** `8500:80`.

## Why login broke (2026-09-23)

Closing host `:8000` while Cloudflare still routed `/api/v1/*` → `localhost:8000` produced **502** on send/login. Frontend showed “E-posta gönderilirken hata oluştu”. Fix: remapped `8000→nginx` interim + migrate CF hops.

## Recommended edge controls

1. **WAF / Bot Fight Mode** — enable managed rules; challenge or block obvious scanners.
2. **Rate limiting** (Cloudflare Rate Limiting or WAF custom rules):
   - `/api/v1/send` and `/api/v1/verify-code` — strict (e.g. 10 req / min / IP)
   - `/api/v1/generate` — moderate (e.g. 30 req / min / IP) in addition to app daily quota
3. **Access / IP allowlist** (optional) — municipal VPN or office ranges; during pen-test, allow tester IPs only.
4. **TLS** — terminate at Cloudflare; origin HTTP on 8500 behind tunnel is acceptable if tunnel is the only path. Host firewall: block direct internet to 8000/8500 except Cloudflare tunnel process.
5. **Security headers** (edge Transform Rules or Cloudflare settings) — reinforce CSP / HSTS; nginx already sets CSP, XFO, XCTO, Referrer-Policy, Permissions-Policy.
6. **Log redaction** — strip or hash query strings containing `token` / `auth_token` / `code` in Cloudflare and origin access logs. Magic links use `#magic=` fragment so the secret never hits query logs on the final hop.

## Origin lock checklist

- [ ] Cloudflare Tunnel / hops: only `:8500`
- [ ] Docker publish: only `8500:80`
- [ ] Host `ss -tlnp` shows no public `*:8000`
- [ ] HSTS enabled at Cloudflare (HTTPS)
