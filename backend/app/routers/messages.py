from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models import Contact, Message
from app.services.wa_gateway import wa_gateway

router = APIRouter(prefix="/api/messages", tags=["messages"])

class SendMessagePayload(BaseModel):
    contact_id: Optional[int] = None
    phone: Optional[str] = None  # alternatif jika contact belum ada
    name: Optional[str] = None
    content: str

@router.post("/send")
async def send_message(payload: SendMessagePayload, db: Session = Depends(get_db)):
    # Cari atau buat kontak
    contact = None
    if payload.contact_id:
        contact = db.query(Contact).get(payload.contact_id)
        if not contact:
            raise HTTPException(404, "Kontak tidak ditemukan")
    elif payload.phone:
        phone = payload.phone.strip().replace(" ", "").replace("-", "").replace("+", "")
        if phone.startswith("0"):
            phone = "62" + phone[1:]
        contact = db.query(Contact).filter(Contact.phone == phone).first()
        if not contact:
            contact = Contact(phone=phone, name=payload.name or phone, status="baru")
            db.add(contact)
            db.commit()
            db.refresh(contact)
    else:
        raise HTTPException(400, "contact_id atau phone wajib diisi")

    # Kirim via gateway
    result = await wa_gateway.send_message(contact.phone, payload.content)
    if not result["success"]:
        # tetap simpan sebagai failed, tapi return error
        msg = Message(contact_id=contact.id, direction="out", content=payload.content, is_auto=False, wa_message_id=None)
        db.add(msg)
        db.commit()
        raise HTTPException(502, f"Gagal kirim WA: {result.get('error')}")

    # Simpan ke DB
    msg = Message(contact_id=contact.id, direction="out", content=payload.content, is_auto=False, wa_message_id=result.get("id"))
    contact.last_message_at = datetime.utcnow()
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"ok": True, "message_id": msg.id, "wa_id": result.get("id")}

@router.post("/webhook")
async def webhook(payload: dict, db: Session = Depends(get_db)):
    """
    Webhook untuk pesan masuk.
    Fonnte/Wablas akan POST ke endpoint ini.
    Format diseragamkan: {phone, message, name}
    Untuk mock/testing, kirim manual:
    POST /api/messages/webhook {"phone":"628123456789","message":"halo","name":"Budi"}
    """
    phone = payload.get("phone") or payload.get("sender") or payload.get("from") or ""
    message = payload.get("message") or payload.get("text") or payload.get("msg") or ""
    name = payload.get("name") or payload.get("pushName") or None

    if not phone or not message:
        # coba parse format fonnte: {"device":"...","sender":"628...","message":"..."}
        # Jika masih kosong, return ok biar tidak retry
        return {"ok": True, "skip": True}

    phone = str(phone).strip().replace(" ", "").replace("-", "").replace("+", "")
    if phone.startswith("0"):
        phone = "62" + phone[1:]
    # ambil hanya angka
    phone = "".join(c for c in phone if c.isdigit())
    if phone.startswith("62") == False and len(phone) > 10:
        phone = "62" + phone.lstrip("0")

    contact = db.query(Contact).filter(Contact.phone == phone).first()
    if not contact:
        contact = Contact(phone=phone, name=name or phone, status="baru")
        db.add(contact)
        db.commit()
        db.refresh(contact)
    elif name and contact.name == contact.phone:
        contact.name = name

    # Auto deteksi status dari keyword
    lower = message.lower()
    if any(k in lower for k in ["sudah transfer", "sudah bayar", "udah tf", "bukti transfer"]):
        contact.status = "sudah_bayar"
    elif any(k in lower for k in ["komplain", "rusak", "salah", "kecewa"]):
        contact.status = "komplain"

    contact.last_message_at = datetime.utcnow()
    # jika ada follow-up terjadwal, batalkan jika customer sudah balas
    contact.follow_up_at = None

    msg = Message(contact_id=contact.id, direction="in", content=message, is_auto=False)
    db.add(msg)
    db.commit()
    return {"ok": True, "contact_id": contact.id, "message_id": msg.id}

@router.get("/inbox")
def inbox(db: Session = Depends(get_db)):
    """Inbox ringkas: kontak + pesan terakhir"""
    contacts = db.query(Contact).order_by(Contact.last_message_at.desc()).limit(50).all()
    result = []
    for c in contacts:
        last_msg = db.query(Message).filter(Message.contact_id == c.id).order_by(Message.created_at.desc()).first()
        result.append({
            "id": c.id,
            "phone": c.phone,
            "name": c.name,
            "status": c.status,
            "last_message": last_msg.content if last_msg else "",
            "last_direction": last_msg.direction if last_msg else "",
            "last_message_at": c.last_message_at,
            "follow_up_at": c.follow_up_at
        })
    return result
