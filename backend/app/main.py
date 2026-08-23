from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import engine, Base, SessionLocal
from app.models import Contact, Message, FollowUpTemplate, Broadcast
from app.routers import contacts, messages, followup, broadcast, stats

# Buat tabel
Base.metadata.create_all(bind=engine)

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed default template jika kosong
    db = SessionLocal()
    try:
        if db.query(FollowUpTemplate).count() == 0:
            defaults = [
                FollowUpTemplate(
                    name="Tagihan 2 Jam",
                    trigger_status="belum_bayar",
                    delay_minutes=120,
                    message_template="Halo {nama} 👋\n\nPesanan kamu masih *Belum Dibayar* nih. Mau kami bantu proses pembayarannya?\n\nBalas chat ini kalau ada kendala ya!",
                    is_active=True
                ),
                FollowUpTemplate(
                    name="Reminder 24 Jam",
                    trigger_status="belum_bayar",
                    delay_minutes=1440,
                    message_template="Hai {nama}, jangan sampai kehabisan! Pesanan kamu akan hangus dalam 24 jam. Klik link ini untuk bayar: [link_pembayaran]",
                    is_active=False
                ),
                FollowUpTemplate(
                    name="Follow Up Baru 30 menit",
                    trigger_status="baru",
                    delay_minutes=30,
                    message_template="Halo {nama}! Terima kasih sudah hubungi kami 🙏 Ada yang bisa kami bantu?",
                    is_active=False
                ),
            ]
            db.add_all(defaults)
            db.commit()
            print("[SEED] Default follow-up templates created")
    finally:
        db.close()

    # Start scheduler untuk follow-up
    async def job():
        from app.routers.followup import run_followup_job
        db = SessionLocal()
        try:
            sent = await run_followup_job(db)
            if sent > 0:
                print(f"[SCHEDULER] Sent {sent} follow-ups")
        finally:
            db.close()

    scheduler.add_job(job, "interval", minutes=1, id="followup_job")
    scheduler.start()
    print("[SCHEDULER] Follow-up job started (every 1 min)")

    yield
    scheduler.shutdown()

app = FastAPI(
    title="WACRM API",
    description="WA-CRM untuk UMKM - Inbox, Follow-up otomatis, Broadcast",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router)
app.include_router(messages.router)
app.include_router(followup.router)
app.include_router(broadcast.router)
app.include_router(stats.router)

@app.get("/health")
def health():
    return {"status": "ok"}

# Serve frontend & landing (hanya jika foldernya ada)
# Lokal: folder static ada di repo root; di Docker: sejajar dengan app/
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_DIR = os.path.dirname(_BASE_DIR)

def _find_static_dir(name):
    for base in (_BASE_DIR, _REPO_DIR):
        d = os.path.join(base, name)
        if os.path.isdir(d):
            return d
    return None

FRONTEND_DIR = _find_static_dir("frontend")
LANDING_DIR = _find_static_dir("landing")

if FRONTEND_DIR:
    app.mount("/dashboard", StaticFiles(directory=FRONTEND_DIR, html=True), name="dashboard")
if LANDING_DIR:
    # Mount paling akhir supaya route /api & /docs tetap prioritas
    app.mount("/", StaticFiles(directory=LANDING_DIR, html=True), name="landing")

@app.get("/api/seed-demo")
def seed_demo():
    """Isi data demo untuk testing dashboard"""
    db = SessionLocal()
    try:
        # Cek sudah ada data?
        if db.query(Contact).count() > 5:
            return {"ok": False, "msg": "Data demo sudah ada, hapus DB dulu jika mau reseed"}
        demo = [
            Contact(phone="6281234567890", name="Budi - Kaos Polos", status="belum_bayar", notes="Order 2 kaos hitam L"),
            Contact(phone="6281234567891", name="Siti - Tas Ransel", status="sudah_bayar", notes="Resi: JNE 123456"),
            Contact(phone="6281234567892", name="Agus", status="baru", notes="Tanya harga grosir"),
            Contact(phone="6281234567893", name="Rina Komplain", status="komplain", notes="Barang salah warna"),
            Contact(phone="6281234567894", name="Joko", status="dikirim", notes="Sudah kirim kemarin"),
            Contact(phone="6281234567895", name="Dewi", status="belum_bayar", notes="Total 250rb"),
        ]
        db.add_all(demo)
        db.commit()
        for c in demo:
            db.add(Message(contact_id=c.id, direction="in", content="Halo kak, mau tanya stok ready?"))
            if c.status == "sudah_bayar":
                db.add(Message(contact_id=c.id, direction="out", content="Siap kak, pembayaran diterima, segera kami kirim!"))
        db.commit()
        return {"ok": True, "count": len(demo)}
    finally:
        db.close()
