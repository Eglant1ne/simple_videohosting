import asyncio
import json
import os
import tempfile
from typing import Dict, Any

import aio_pika

from services.s3 import S3Service


class VideoProcessor:
    def __init__(self, rabbitmq_config, minio_config):
        self.rabbitmq_config = rabbitmq_config
        self.minio_config = minio_config
        self.s3_service = S3Service(minio_config)
        self.connection = None
        self.channel = None
        
    async def start(self):
        """Запуск процессора - подключение к RabbitMQ и запуск потребителей."""
        self.connection = await aio_pika.connect_robust(self.rabbitmq_config.url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        
        # Объявляем очереди как в Go коде
        await self.channel.declare_queue("convert_video_to_hls", durable=True)
        await self.channel.declare_queue("confirm_video_hls_converting", durable=True)
        
        queue = await self.channel.declare_queue("convert_video_to_hls", durable=True)
        await queue.consume(self.process_message)
        
        print("Video processor started and listening for messages...")
        
    async def stop(self):
        """Остановка процессора - закрытие соединений."""
        if self.connection:
            await self.connection.close()
    
    async def process_message(self, message: aio_pika.IncomingMessage):
        """Обработка входящего сообщения из RabbitMQ."""
        try:
            message_body = message.body.decode()
            print(f"Received message: {message_body}")
            
            # Парсим JSON как в Go коде
            data = json.loads(message_body)
            
            # Проверяем обязательные поля как в Go
            if 'video_path' not in data or 'uuid' not in data:
                print(f"Missing required fields: {data}")
                await message.ack()
                return
                
            success = await self.process_video(data)
            
            if success:
                await message.ack()
                print(f"Video processed successfully: {data['uuid']}")
            else:
                await message.nack(requeue=False)
                print(f"Video processing failed: {data['uuid']}")
                
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            await message.ack()
        except Exception as e:
            print(f"Error processing message: {e}")
            await message.nack(requeue=False)
    
    async def process_video(self, data: Dict[str, Any]):
        """Основной метод обработки видео (аналог Go processVideo)."""
        try:
            video_path = data['video_path']
            video_uuid = data['uuid']
            
            print(f"Starting video processing: {video_path} for UUID: {video_uuid}")
            
            with tempfile.TemporaryDirectory(prefix=video_uuid) as temp_dir:
                input_file = os.path.join(temp_dir, os.path.basename(video_path))
                
                # 1. Скачиваем видео из MinIO (аналог FGetObject)
                print(f"Downloading video from MinIO: {video_path}")
                await self.s3_service.download_file(video_path, input_file)
                
                # 2. Получаем информацию о видео (аналог getVideoResolution)
                print("Getting video resolution...")
                width, height = await self.get_video_resolution(input_file)
                print(f"Video resolution: {width}x{height}")
                
                # 3. Определяем поддерживаемые разрешения как в Go
                resolutions = [
                    (3840, 2160),  # 4k
                    (2560, 1440),  # 2k
                    (1920, 1080),  # 1080p
                    (1280, 720),   # 720p
                    (854, 480),    # 480p
                    (640, 360),    # 360p
                    (426, 240),    # 240p
                ]
                
                supported_res = ["256:144"]  # 144p всегда включаем
                for w, h in resolutions:
                    if w <= width and h <= height:
                        supported_res.append(f"{w}:{h}")
                
                print(f"Supported resolutions: {supported_res}")
                
                # 4. Конвертируем в HLS для каждого разрешения
                output_dir = os.path.join(temp_dir, "hls")
                os.makedirs(output_dir, exist_ok=True)
                
                for resolution in supported_res:
                    await self.convert_to_hls(input_file, video_uuid, resolution, output_dir)
                
                # 5. Создаем мастер-плейлист
                await self.create_master_playlist(video_uuid, supported_res, output_dir)
                
                # 6. Загружаем HLS файлы в MinIO (аналог FPutObject)
                print("Uploading HLS files to MinIO...")
                for filename in os.listdir(output_dir):
                    local_path = os.path.join(output_dir, filename)
                    # Путь как в Go: VideoFilesFolder/uuid/filename
                    s3_path = f"video_files/{video_uuid}/{filename}"
                    await self.s3_service.upload_file(local_path, s3_path)
                    print(f"Uploaded: {s3_path}")
                
                # 7. Удаляем оригинальное видео (аналог RemoveObject)
                print(f"Removing original video: {video_path}")
                await self.s3_service.delete_file(video_path)
                
                # 8. Отправляем подтверждение (аналог sendConfirmation)
                await self.send_confirmation(video_uuid)
                
                print(f"Video processing completed successfully: {video_uuid}")
                return True
                
        except Exception as e:
            print(f"Error in process_video: {e}")
            return False
    
    async def get_video_resolution(self, file_path: str) -> tuple[int, int]:
        """Получение разрешения видео через ffprobe (аналог getVideoResolution в Go)."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                file_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise Exception(f"ffprobe failed: {error_msg}")
            
            output = stdout.decode().strip()
            width_str, height_str = output.split(',')
            
            return int(width_str), int(height_str)
            
        except Exception as e:
            print(f"Error getting video resolution: {e}")
            raise
    
    async def convert_to_hls(self, input_file: str, video_uuid: str, resolution: str, output_dir: str):
        """Конвертация в HLS используя прямое выполнение команд FFmpeg как в Go."""
        try:
            res_parts = resolution.split(":")
            res_name = f"{res_parts[1]}p-{video_uuid}"
            output_file = os.path.join(output_dir, f"{res_name}.m3u8")
            
            print(f"Converting to {resolution} -> {res_name}")
            
            # Строим команду как в Go коде
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-vf', f'scale={resolution}',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-profile:v', 'baseline',
                '-level', '3.0',
                '-loglevel', 'warning',
                '-start_number', '0',
                '-hls_time', '5',
                '-hls_list_size', '0',
                '-f', 'hls',
                output_file
            ]
            
            print(f"Running FFmpeg command for {resolution}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_output = stderr.decode() if stderr else "No error output"
                print(f"FFmpeg error output: {error_output}")
                raise Exception(f"FFmpeg command failed with return code {process.returncode}")
            
            # Проверяем что выходной файл создан
            if not os.path.exists(output_file):
                raise FileNotFoundError(f"Output file {output_file} was not created")
                
            print(f"Successfully converted to {resolution}")
            
        except Exception as e:
            print(f"Error converting {resolution}: {e}")
            raise
    
    async def create_master_playlist(self, video_uuid: str, resolutions: list, output_dir: str):
        """Создание мастер-плейлиста."""
        master_content = "#EXTM3U\n#EXT-X-VERSION:3\n"
        
        for resolution in resolutions:
            res_parts = resolution.split(":")
            res_name = f"{res_parts[1]}p-{video_uuid}"
            bandwidth = self._get_bandwidth(resolution)
            master_content += f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={resolution}\n{res_name}.m3u8\n'
        
        master_file = os.path.join(output_dir, "master.m3u8")
        with open(master_file, 'w') as f:
            f.write(master_content)
        print("Created master playlist")
    
    def _get_bandwidth(self, resolution: str) -> int:
        """Определение битрейта для разрешения."""
        height = int(resolution.split(':')[1])
        bitrates = {
            144: 500000, 240: 750000, 360: 1000000, 
            480: 1500000, 720: 2500000, 1080: 5000000, 
            1440: 8000000, 2160: 16000000
        }
        return bitrates.get(height, 500000)
    
    async def send_confirmation(self, video_uuid: str):
        """Отправка подтверждения (аналог sendConfirmation в Go)."""
        message = {"uuid": video_uuid}
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=video_uuid
            ),
            routing_key="confirm_video_hls_converting"
        )
        print(f"Sent confirmation for: {video_uuid}")
