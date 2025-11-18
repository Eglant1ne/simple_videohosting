from sqlalchemy import BIGINT, String, Column, TIMESTAMP, Boolean, UUID
from sqlalchemy.sql import func

from .base import _Base


class VideoInfo(_Base):
    __tablename__ = 'videos_info'

    uuid = Column(UUID(as_uuid=True), primary_key=True, index=True, name='uuid')
    author_id = Column(BIGINT, nullable=False, index=True, name='author_id')
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), name='created_at')
    is_complete = Column(Boolean, nullable=False, server_default='0', name='is_complete')
    likes_count = Column(BIGINT, nullable=False, server_default='0', name='likes_count')
    dislikes_count = Column(BIGINT, nullable=False, server_default='0', name='dislikes_count')
    views_count = Column(BIGINT, nullable=False, server_default='0', name='views_count')
    
    def to_dict(self):
        """Преобразует объект в словарь для JSON сериализации"""
        return {
            'uuid': str(self.uuid),
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_complete': self.is_complete,
            'likes_count': self.likes_count,
            'dislikes_count': self.dislikes_count,
            'views_count': self.views_count
        }