from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class ContactStatus(str, enum.Enum):
    BARU = "baru"
    BELUM_BAYAR = "belum_bayar"
    SUDAH_BAYAR = "sudah_bayar"
    DIKIRIM = "dikirim"
    SELESAI = "selesai"
    KOMPLAIN = "komplain"

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    status = Column(String(20), default=ContactStatus.BARU)
    notes = Column(Text, nullable=True)
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())
    follow_up_at = Column(DateTime(timezone=True), nullable=True)
    follow_up_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    messages = relationship("Message", back_populates="contact", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    direction = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    wa_message_id = Column(String(100), nullable=True)
    is_auto = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    contact = relationship("Contact", back_populates="messages")

class FollowUpTemplate(Base):
    __tablename__ = "followup_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    trigger_status = Column(String(20), default=ContactStatus.BELUM_BAYAR)
    delay_minutes = Column(Integer, default=120)
    message_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Broadcast(Base):
    __tablename__ = "broadcasts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    total_target = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
