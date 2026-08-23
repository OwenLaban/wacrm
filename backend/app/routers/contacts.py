from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models import Contact, Message, ContactStatus

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

class ContactCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    status: Optional[str] = "baru"
    notes: Optional[str] = None

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ContactOut(BaseModel):
    id: int
    phone: str
    name: Optional[str]
    status: str
    notes: Optional[str]
    last_message_at: Optional[datetime]
    follow_up_count: int
    created_at: Optional[datetime]
    class Config:
        from_attributes = True

@router.get("", response_model=List[ContactOut])
def list_contacts(status: Optional[str] = None, q: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Contact).order_by(Contact.last_message_at.desc())
    if status:
        query = query.filter(Contact.status == status)
    if q:
        query = query.filter((Contact.phone.contains(q)) | (Contact.name.contains(q)))
    return query.limit(100).all()

@router.post("", response_model=ContactOut)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    phone = payload.phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    if phone.startswith("0"):
        phone = "62" + phone[1:]
    existing = db.query(Contact).filter(Contact.phone == phone).first()
    if existing:
        raise HTTPException(400, "Kontak dengan nomor ini sudah ada")
    c = Contact(phone=phone, name=payload.name, status=payload.status, notes=payload.notes)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.get("/{contact_id}", response_model=ContactOut)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    c = db.query(Contact).get(contact_id)
    if not c:
        raise HTTPException(404, "Kontak tidak ditemukan")
    return c

@router.patch("/{contact_id}", response_model=ContactOut)
def update_contact(contact_id: int, payload: ContactUpdate, db: Session = Depends(get_db)):
    c = db.query(Contact).get(contact_id)
    if not c:
        raise HTTPException(404, "Kontak tidak ditemukan")
    if payload.name is not None:
        c.name = payload.name
    if payload.status is not None:
        if payload.status not in [e.value for e in ContactStatus]:
            raise HTTPException(400, f"Status tidak valid: {payload.status}")
        c.status = payload.status
        # reset follow_up jika status berubah jadi sudah_bayar/dikirim
        if payload.status in ["sudah_bayar", "dikirim", "selesai"]:
            c.follow_up_at = None
    if payload.notes is not None:
        c.notes = payload.notes
    db.commit()
    db.refresh(c)
    return c

@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    c = db.query(Contact).get(contact_id)
    if not c:
        raise HTTPException(404, "Kontak tidak ditemukan")
    db.delete(c)
    db.commit()
    return {"ok": True}

@router.get("/{contact_id}/messages")
def get_messages(contact_id: int, db: Session = Depends(get_db)):
    c = db.query(Contact).get(contact_id)
    if not c:
        raise HTTPException(404, "Kontak tidak ditemukan")
    msgs = db.query(Message).filter(Message.contact_id == contact_id).order_by(Message.created_at.asc()).all()
    return [{"id": m.id, "direction": m.direction, "content": m.content, "is_auto": m.is_auto, "created_at": m.created_at} for m in msgs]
