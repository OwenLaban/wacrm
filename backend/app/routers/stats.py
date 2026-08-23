from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Contact, Message

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Contact.id)).scalar() or 0
    belum_bayar = db.query(func.count(Contact.id)).filter(Contact.status == "belum_bayar").scalar() or 0
    sudah_bayar = db.query(func.count(Contact.id)).filter(Contact.status == "sudah_bayar").scalar() or 0
    komplain = db.query(func.count(Contact.id)).filter(Contact.status == "komplain").scalar() or 0
    # pesan hari ini
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    msg_today = db.query(func.count(Message.id)).filter(func.date(Message.created_at) == today).scalar() or 0

    # estimasi omzet hilang: belum_bayar * asumsi 150rb
    omzet_terancam = belum_bayar * 150000

    return {
        "total_kontak": total,
        "belum_bayar": belum_bayar,
        "sudah_bayar": sudah_bayar,
        "komplain": komplain,
        "pesan_hari_ini": msg_today,
        "omzet_terancam": omzet_terancam,
        "by_status": {
            "baru": db.query(func.count(Contact.id)).filter(Contact.status=="baru").scalar() or 0,
            "belum_bayar": belum_bayar,
            "sudah_bayar": sudah_bayar,
            "dikirim": db.query(func.count(Contact.id)).filter(Contact.status=="dikirim").scalar() or 0,
            "selesai": db.query(func.count(Contact.id)).filter(Contact.status=="selesai").scalar() or 0,
            "komplain": komplain,
        }
    }
