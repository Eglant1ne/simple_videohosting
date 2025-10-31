from sqlalchemy import Column, BigInteger, String, TIMESTAMP
from sqlalchemy.sql import func

from .base import _Base


class User(_Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, index=True, name='id')
    username = Column(String(32), unique=True, index=True, nullable=False, name='username')
    email = Column(String(254), unique=True, index=True, nullable=False, name='email')
    password_hash = Column(String, nullable=False, name='password_hash')
    created_at = Column(TIMESTAMP, server_default=func.now(), name='created_at')
    avatar_path = Column(String, nullable=True, name='avatar_path')
    token_version = Column(BigInteger, nullable=False, name='token_version', server_default='0')
