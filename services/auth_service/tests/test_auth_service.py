import unittest
import os
import sys
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env.test')
load_dotenv(env_path)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from auth.schemas import UserCreate, UserLogin, ChangePassword, TokenBody


class TestAuthService(unittest.TestCase):
    """Тесты для сервиса аутентификации"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.client = TestClient(app)
    
    def test_health_check(self):
        """Тест health-check эндпоинта"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"msg": "healthy"})
    


class TestSchemasValidation(unittest.TestCase):
    """Тесты валидации Pydantic схем"""
    
    def test_user_login_schema_validation(self):
        """Тест валидации схемы UserLogin"""
        # Валидные данные
        valid_data = [
            {"login": "user@example.com", "password": "pass123"},
            {"login": "username123", "password": "pass123"}
        ]
        
        for data in valid_data:
            try:
                UserLogin(**data)
            except Exception as e:
                self.fail(f"Validation failed for valid data {data}: {e}")
        
        # Невалидные данные
        invalid_data = [
            {"login": "ab", "password": "pass123"},  # Слишком короткий username
            {"login": "user@name", "password": "pass123"},  # Недопустимые символы
        ]
        
        for data in invalid_data:
            with self.assertRaises(Exception):
                UserLogin(**data)
    
    def test_user_create_schema_validation(self):
        """Тест валидации схемы UserCreate"""
        # Валидные данные
        valid_data = {
            "email": "valid@example.com",
            "username": "valid_user123", 
            "password": "password123"
        }
        
        try:
            UserCreate(**valid_data)
        except Exception as e:
            self.fail(f"Validation failed for valid data: {e}")
        
        # Невалидные данные
        invalid_data = [
            {
                "email": "invalid-email",
                "username": "validuser",
                "password": "password123"
            },
            {
                "email": "valid@example.com",
                "username": "ab",  # Слишком короткий
                "password": "password123"
            }
        ]
        
        for data in invalid_data:
            with self.assertRaises(Exception):
                UserCreate(**data)
    
    def test_change_password_schema_validation(self):
        """Тест валидации схемы ChangePassword"""
        valid_data = {
            "old_password": "oldpass123",
            "new_password": "newpass456"
        }
        
        try:
            ChangePassword(**valid_data)
        except Exception as e:
            self.fail(f"Validation failed for valid data: {e}")
    
    def test_token_body_schema_validation(self):
        """Тест валидации схемы TokenBody"""
        valid_data = {
            "token": "mock.jwt.token"
        }
        
        try:
            TokenBody(**valid_data)
        except Exception as e:
            self.fail(f"Validation failed for valid data: {e}")


class TestPasswordUtils(unittest.TestCase):
    """Тесты утилит для работы с паролями"""
    
    def test_verify_password(self):
        """Тест проверки пароля"""
        from auth.utils import verify_password, generate_hashed_password
        
        password = "my_secret_password"
        hashed_password = generate_hashed_password(password)
        
        # Правильный пароль
        self.assertTrue(verify_password(password, hashed_password))
        
        # Неправильный пароль
        self.assertFalse(verify_password("wrong_password", hashed_password))
    
    def test_generate_hashed_password(self):
        """Тест генерации хеша пароля"""
        from auth.utils import generate_hashed_password
        
        password = "test_password"
        hashed = generate_hashed_password(password)
        
        # Хеш должен быть строкой
        self.assertIsInstance(hashed, str)
        # Хеш не должен быть равен оригинальному паролю
        self.assertNotEqual(hashed, password)
        # Хеш должен быть достаточно длинным
        self.assertGreater(len(hashed), 10)


class TestJWTUtils(unittest.TestCase):
    """Тесты утилит для работы с JWT"""
    
    def test_token_payload_type_check(self):
        """Тест проверки типа токена"""
        from jwt_tokens.utils import token_payload_is_access, token_payload_is_refresh
        
        access_payload = {"token_type": "access"}
        refresh_payload = {"token_type": "refresh"}
        invalid_payload = {"token_type": "invalid"}
        
        self.assertTrue(token_payload_is_access(access_payload))
        self.assertFalse(token_payload_is_access(refresh_payload))
        
        self.assertTrue(token_payload_is_refresh(refresh_payload))
        self.assertFalse(token_payload_is_refresh(access_payload))
        
        self.assertFalse(token_payload_is_access(invalid_payload))
        self.assertFalse(token_payload_is_refresh(invalid_payload))


if __name__ == '__main__':
    unittest.main(verbosity=2)