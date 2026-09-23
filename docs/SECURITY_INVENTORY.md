# Security inventory (Faz 0)

| Item | Status |
|------|--------|
| Domain | yardimci.niluferyapayzeka.tr |
| Origin ports (target) | 8500→nginx:80 only; uvicorn internal 127.0.0.1:8000 |
| Secrets | `.env` in volume `ai_helper_data_v2`; gitignored; not in image |
| DEBUG_MODE | false |
| JWT_SECRET_KEY | rotated from placeholder (Faz 0); required non-placeholder at boot |
| ALLOWED_ORIGINS | production + localhost:8500 |
| Cloudflare hops (target) | all → localhost:8500 — see `CLOUDFLARE_EDGE.md` |
| Image secrets | `.dockerignore` excludes `.env` |
| Access token TTL | `ACCESS_TOKEN_EXPIRE_HOURS` (default 8h) |
| Generate quota | `GENERATE_DAILY_QUOTA` (default 200/user/day) |

## Attack surface (post-hardening)
- Public: Cloudflare → nginx → static UI + `/api/` proxy
- Auth endpoints under `/api/v1/*`
- Generate / templates with JWT
- Docs: `PENTEST_SCOPE.md`, `PENTEST_BRIEF.md`, `CLOUDFLARE_EDGE.md`
