import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ['POSTGRES_DB'] = 'test_auth_db'
os.environ['POSTGRES_USER'] = 'test_auth_user'
os.environ['POSTGRES_PASSWORD'] = 'test_auth_password'
os.environ['DEBUG_MODE'] = 'True'
os.environ['AUTH_SERVICE_WORKERS'] = '1'
os.environ['CHANNEL_ACTIONS_SERVICE_WORKERS'] = '1'
os.environ['RSA_PUBLIC_KEY'] = 'mock_public_key_1234567890'
os.environ['RSA_PRIVATE_KEY'] = 'mock_private_key_1234567890'
os.environ['REDIS_PASSWORD'] = 'test_redis_password'

os.environ['RABBITMQ_DEFAULT_USER'] = 'test_user'
os.environ['RABBITMQ_DEFAULT_PASS'] = 'test_password'
os.environ['RABBITMQ_HOST'] = 'localhost'
os.environ['RABBITMQ_PORT'] = '5672'

import unittest
from fastapi.testclient import TestClient
from main import app


class TestVideoEndpoints(unittest.TestCase):
    """Тесты для эндпоинтов видео с использованием unittest"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.client = TestClient(app)
    
    def test_get_author_videos_success(self):
        """Тест получения видео не существующего автора автора"""
        with patch('get_info.videos.async_session') as mock_session:
            mock_session_ctx = AsyncMock()
            mock_session.return_value = mock_session_ctx
            
            mock_execute = AsyncMock()
            mock_session_ctx.__aenter__.return_value.execute = mock_execute
            
            mock_video = MagicMock()
            mock_video.to_dict.return_value = {"uuid": "test-uuid", "author_id": 1}
            
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_video]
            mock_execute.return_value = mock_result
            
            response = self.client.get("/videos/author/53253252")
            
            self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()