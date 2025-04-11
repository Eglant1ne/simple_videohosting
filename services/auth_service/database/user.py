from sqlalchemy import Column, BigInteger, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True, index=True, name='id')
    username = Column(String(32), unique=True, index=True, nullable=False)
    email = Column(String(254), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    date_joined = Column(TIMESTAMP, server_default=func.now())
    avatar = Column(String, nullable=True)
