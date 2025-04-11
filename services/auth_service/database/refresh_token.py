from sqlalchemy import Column, BigInteger, String, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .user import User
from .base import _Base


class RefreshToken(_Base):
    __tablename__ = 'refresh_tokens'

    id = Column(BigInteger, primary_key=True, name='id')
    user_id = Column(ForeignKey(User.id, ondelete='CASCADE'), nullable=False, index=True, name='user_id')
    token = Column(String(254), nullable=False, unique=True, index=True, name='token')
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, name='created_at')
    expires_at = Column(TIMESTAMP, nullable=False, name='expires_at')
    is_revoked = Column(Boolean, default=False, name='is_revoked')

    user = relationship(User, back_populates="refresh_tokens")
