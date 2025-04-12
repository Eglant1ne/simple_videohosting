from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    database: str = Field(alias='POSTGRES_DB')
    user: str = Field(alias='POSTGRES_USER')
    password: str = Field(alias='POSTGRES_PASSWORD')


class DebugMode(BaseSettings):
    debug_mode: bool = Field(alias='DEBUG_MODE')


class RSAKeys(BaseSettings):
    public_key: str = Field(alias="RSA_PUBLIC_KEY")
    private_key: str = Field(alias="RSA_PRIVATE_KEY")


DATABASE_SETTINGS = DatabaseSettings()
DEBUG_MODE = DebugMode()
RSA_KEYS = RSAKeys()
