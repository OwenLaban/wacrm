from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from app.database import get_db, SessionLocal
from app.models import Broadcast, Contact, Message
from app.services.wa_gateway import wa_gateway

router = APIRouter(prefix="/api/broadcast", tags=["broadcast"])

class BroadcastCreate(BaseModel):
    title: str
    message: str
    target_status: Optional[str] = None  # jika diisi, hanya kirim ke status tertentu
    target_ids: Optional[List[int]] = None  # atau ids spesifik

class BroadcastOut(BaseModel):
    id: int
    title: str
    message: str
    total_target: int
    sent_count: int
    failed_count: int
    status: str
    class Config:
        from_attributes = True

@router.get("", response_model=List[BroadcastOut])
def list_broadcasts(db: Session = Depends(get_db)):
    return db.query(Broadcast).order_by(Broadcast.id.desc()).all()

@router.post("", response_model=BroadcastOut)
def create_broadcast(payload: BroadcastCreate, db: Session = Depends(get_db)):
    b = Broadcast(title=payload.title, message=payload.message, status="draft")
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

async def _do_broadcast(broadcast_id: int, target_phones: list):
    db = SessionLocal()
    try:
        b = db.query(Broadcast).get(broadcast_id)
        if not b:
            return
        b.status = "sending"
        b.total_target = len(target_phones)
        db.commit()

        for item in target_phones:
            phone = item["phone"]
            contact_id = item["contact_id"]
            # jeda random 2-5 detik biar tidak ke-detect spam
            await asyncio.sleep(2 + (hash(phone) % 3))
            result = await wa_gateway.send_message(phone, b.message)
            if result["success"]:
                b.sent_count += 1
                # simpan ke messages
                msg = Message(contact_id=contact_id, direction="out", content=b.message, is_auto=True, wa_message_id=result.get("id"))
                db.add(msg)
            else:
                b.failed_count += 1
            db.commit()

        b.status = "done"
        db.commit()
    finally:
        db.close()

@router.post("/{broadcast_id}/send")
async def send_broadcast(broadcast_id: int, background_tasks: BackgroundTasks, payload: BroadcastCreate, db: Session = Depends(get_db)):
    """
    Kirim broadcast. Payload bisa override message/title jika mau.
    Untuk simpel, kita ambil target dari DB.
    """
    b = db.query(Broadcast).get(broadcast_id)
    if not b:
        raise HTTPException(404, "Broadcast tidak ditemukan")
    if b.status == "sending":
        raise HTTPException(400, "Broadcast sedang dikirim")

    # Tentukan target
    query = db.query(Contact)
    if payload.target_status:
        query = query.filter(Contact.status == payload.target_status)
    if payload.target_ids:
        query = query.filter(Contact.id.in_(payload.target_ids))

    contacts = query.all()
    if not contacts:
        raise HTTPException(400, "Tidak ada kontak target")

    # Update message jika ada override
    if payload.message and payload.message != b.message:
        b.message = payload.message
    if payload.title and payload.title != b.title:
        b.title = payload.title
    db.commit()

    targets = [{"phone": c.phone, "contact_id": c.id} for c in contacts]
    background_tasks.add_task(_do_broadcast, b.id, targets)

    return {"ok": True, "total_target": len(targets), "status": "sending"}

@router.get("/{broadcast_id}", response_model=BroadcastOut)
def get_broadcast(broadcast_id: int, db: Session = Depends(get_db)):
    b = db.query(Broadcast).get(broadcast_id)
    if not b:
        raise HTTPException(404, "Broadcast tidak ditemukan")
    return b
