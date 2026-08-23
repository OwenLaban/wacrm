# WACRM - WA-CRM untuk UMKM

Inbox terpusat + Follow-up otomatis + Broadcast anti-banned.

## Stack
- Backend: FastAPI + SQLAlchemy + PostgreSQL (SQLite fallback) + APScheduler
- WA Gateway: Abstraction (mock / fonnte / wablas)
- Frontend: Tailwind + Vanilla JS (no build)
- Infra: Docker Compose

## Struktur
```
wacrm/
  backend/
    app/
      main.py          # FastAPI + scheduler + seed
      database.py
      models.py
      routers/
        contacts.py    # CRUD kontak & status
        messages.py    # kirim, webhook, inbox
        followup.py    # template & scheduler
        broadcast.py   # broadcast background job
        stats.py       # dashboard stats
      services/
        wa_gateway.py  # fonnte/wablas/mock
  frontend/index.html  # Dashboard
  landing/index.html   # Landing page validasi
  docker-compose.yml
```

## Cara Jalan (2 opsi)

### Opsi A: Tanpa Docker (paling cepat)
```powershell
cd C:\Users\owens\Documents\Saas\wacrm\backend
pip install -r requirements.txt
# pakai SQLite otomatis
uvicorn app.main:app --reload --port 8000
```
Buka:
- API Docs: http://localhost:8000/docs
- Dashboard: buka file `frontend/index.html` langsung (double klik) ATAU serve via `npx serve frontend`
- Landing: buka `landing/index.html`

### Opsi B: Docker (production-like)
```powershell
cd C:\Users\owens\Documents\Saas\wacrm
docker-compose up --build
```
- API: http://localhost:8000
- DB: postgres://wacrm:wacrm123@localhost:5432/wacrm

## Konfigurasi WA Gateway
Buat `backend/.env` dari `.env.example`:

```
WA_GATEWAY_PROVIDER=mock   # mock | fonnte | wablas
FONNTE_TOKEN=xxx            # isi jika pakai fonnte
WABLAS_TOKEN=xxx
WABLAS_DOMAIN=https://console.wablas.com
```

- `mock`: untuk dev, tidak kirim WA beneran, log di console
- `fonnte`: daftar di fonnte.com, dapat token, isi FONNTE_TOKEN
- `wablas`: daftar di wablas.com

Webhook URL untuk provider: `https://domain-kamu.com/api/messages/webhook`

Test webhook manual:
```bash
curl -X POST http://localhost:8000/api/messages/webhook -H "Content-Type: application/json" -d "{\"phone\":\"628123456789\",\"message\":\"halo kak\",\"name\":\"Budi\"}"
```

## Fitur MVP
- [x] CRUD Kontak + status (baru/belum_bayar/sudah_bayar/dikirim/komplain)
- [x] Inbox + chat 1-1
- [x] Kirim WA via gateway abstraction
- [x] Webhook pesan masuk (auto-buat kontak + auto-deteksi status)
- [x] Follow-up template + scheduler tiap 1 menit + trigger manual
- [x] Broadcast background job + jeda anti-banned
- [x] Stats dashboard
- [x] Landing page + capture lead

## Next Step (validasi 7 hari)
1. Bikin landing online: deploy `landing/index.html` ke Vercel/Netlify (drag & drop)
2. Chat 20 olshop: "Kak, sering kelewat follow-up WA? Aku bikin tool 79rb/bulan, mau coba gratis 14 hari?"
3. Target 10 waiting list → kasih akses dashboard (mock dulu gpp)
4. Jika 3+ mau bayar → lanjut integrasi Fonnte & payment (Midtrans/Xendit)

## API Penting
- `GET /api/stats` - dashboard
- `GET /api/messages/inbox` - inbox
- `POST /api/messages/send` - kirim WA
- `POST /api/messages/webhook` - terima WA
- `GET /api/contacts` - list kontak
- `POST /api/followup/schedule/{id}` - jadwalkan followup
- `POST /api/broadcast/{id}/send` - kirim broadcast
