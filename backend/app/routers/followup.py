from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from app.database import get_db
from app.models import FollowUpTemplate, Contact, Message
from app.services.wa_gateway import wa_gateway

router = APIRouter(prefix="/api/followup", tags=["followup"])

class TemplateCreate(BaseModel):
    name: str
    trigger_status: str = "belum_bayar"
    delay_minutes: int = 120
    message_template: str
    is_active: bool = True

class TemplateOut(BaseModel):
    id: int
    name: str
    trigger_status: str
    delay_minutes: int
    message_template: str
    is_active: bool
    class Config:
        from_attributes = True

@router.get("/templates", response_model=List[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.query(FollowUpTemplate).order_by(FollowUpTemplate.id.asc()).all()

@router.post("/templates", response_model=TemplateOut)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    t = FollowUpTemplate(**payload.dict())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@router.patch("/templates/{tid}", response_model=TemplateOut)
def update_template(tid: int, payload: TemplateCreate, db: Session = Depends(get_db)):
    t = db.query(FollowUpTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Template tidak ditemukan")
    for k, v in payload.dict().items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t

@router.delete("/templates/{tid}")
def delete_template(tid: int, db: Session = Depends(get_db)):
    t = db.query(FollowUpTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Template tidak ditemukan")
    db.delete(t)
    db.commit()
    return {"ok": True}

@router.post("/trigger/{contact_id}")
async def trigger_followup(contact_id: int, db: Session = Depends(get_db)):
    """Trigger manual follow-up untuk testing"""
    contact = db.query(Contact).get(contact_id)
    if not contact:
        raise HTTPException(404, "Kontak tidak ditemukan")
    template = db.query(FollowUpTemplate).filter(
        FollowUpTemplate.trigger_status == contact.status,
        FollowUpTemplate.is_active == True
    ).first()
    if not template:
        raise HTTPException(404, f"Tidak ada template aktif untuk status {contact.status}")

    msg_text = template.message_template.replace("{nama}", contact.name or "Kak").replace("{phone}", contact.phone)
    result = await wa_gateway.send_message(contact.phone, msg_text)
    if not result["success"]:
        raise HTTPException(502, f"Gagal kirim: {result.get('error')}")

    msg = Message(contact_id=contact.id, direction="out", content=msg_text, is_auto=True, wa_message_id=result.get("id"))
    contact.follow_up_count += 1
    contact.follow_up_at = None
    db.add(msg)
    db.commit()
    return {"ok": True, "sent": msg_text}

@router.post("/schedule/{contact_id}")
def schedule_followup(contact_id: int, delay_minutes: int = 120, db: Session = Depends(get_db)):
    """Jadwalkan follow-up otomatis"""
    contact = db.query(Contact).get(contact_id)
    if not contact:
        raise HTTPException(404, "Kontak tidak ditemukan")
    contact.follow_up_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
    db.commit()
    return {"ok": True, "follow_up_at": contact.follow_up_at}

# Background job akan dipanggil oleh scheduler di main.py
async def run_followup_job(db: Session):
    now = datetime.utcnow()
    contacts = db.query(Contact).filter(
        Contact.follow_up_at != None,
        Contact.follow_up_at <= now
    ).all()
    templates = {t.trigger_status: t for t in db.query(FollowUpTemplate).filter(FollowUpTemplate.is_active==True).all()}

    sent = 0
    for c in contacts:
        template = templates.get(c.status)
        if not template:
            c.follow_up_at = None
            continue
        msg_text = template.message_template.replace("{nama}", c.name or "Kak").replace("{phone}", c.phone)
        result = await wa_gateway.send_message(c.phone, msg_text)
        if result["success"]:
            msg = Message(contact_id=c.id, direction="out", content=msg_text, is_auto=True, wa_message_id=result.get("id"))
            c.follow_up_count += 1
            c.follow_up_at = None
            db.add(msg)
            sent += 1
        else:
            # retry 10 menit lagi
            c.follow_up_at = now + timedelta(minutes=10)
    db.commit()
    return sent
