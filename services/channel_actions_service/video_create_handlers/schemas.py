from pydantic import BaseModel


class UnprocessedVideoUploaded(BaseModel):
    user_id: int
    video_path: str
