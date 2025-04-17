from pydantic import BaseModel, UUID4


class UnprocessedVideoUploaded(BaseModel):
    user_id: int
    video_path: str


class ConfirmVideoHlsConverting(BaseModel):
    uuid: UUID4
