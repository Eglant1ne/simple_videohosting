import asyncio
import aiofiles
import json
import boto3
from botocore.config import Config


class S3Service:
    def __init__(self, config):
        self.config = config
        self.client = boto3.client(
            's3',
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region,
            config=Config(signature_version='s3v4')
        )
        self.video_files_folder = "video_files"
        self._ensure_bucket_and_policy()
        
    def _ensure_bucket_and_policy(self):
        """Создает bucket и настраивает политику доступа как в Go коде."""
        try:
            # Проверяем существует ли bucket
            self.client.head_bucket(Bucket=self.config.bucket)
            print(f"Bucket {self.config.bucket} already exists")
        except Exception:
            # Создаем bucket если не существует
            self.client.create_bucket(Bucket=self.config.bucket)
            print(f"Created bucket {self.config.bucket}")
        
        # Создаем папку video_files как в Go коде
        try:
            self.client.put_object(
                Bucket=self.config.bucket,
                Key=f"{self.video_files_folder}/",
                Body=b''
            )
            print(f"Created folder {self.video_files_folder}/")
        except Exception as e:
            print(f"Folder {self.video_files_folder} already exists or error: {e}")
        
        # Настраиваем политику доступа для публичного чтения video_files/*
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.config.bucket}/{self.video_files_folder}/*"
                }
            ]
        }
        
        try:
            self.client.put_bucket_policy(
                Bucket=self.config.bucket,
                Policy=json.dumps(policy)
            )
            print("Bucket policy set for public read access to video_files/*")
        except Exception as e:
            print(f"Error setting bucket policy: {e}")
        
    async def download_file(self, s3_path: str, local_path: str):
        """Скачивание файла из S3 (аналог FGetObject)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: self.client.download_file(self.config.bucket, s3_path, local_path)
        )

    async def upload_file(self, local_path: str, s3_path: str):
        """Загрузка файла в S3 (аналог FPutObject)."""
        loop = asyncio.get_event_loop()
        
        # Определяем content_type как в Go
        content_type = self._get_content_type(local_path)
        
        await loop.run_in_executor(
            None,
            lambda: self.client.upload_file(
                local_path, 
                self.config.bucket, 
                s3_path,
                ExtraArgs={'ContentType': content_type}
            )
        )

    async def delete_file(self, s3_path: str):
        """Удаление файла из S3 (аналог RemoveObject)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.client.delete_object(Bucket=self.config.bucket, Key=s3_path)
        )
    
    def _get_content_type(self, filename: str) -> str:
        """Определение content type как в Go."""
        if filename.endswith('.m3u8'):
            return 'application/vnd.apple.mpegurl'
        elif filename.endswith('.ts'):
            return 'video/MP2T'
        else:
            return 'application/octet-stream'