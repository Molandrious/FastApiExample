from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, AnyUrl, BaseModel, DirectoryPath, Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from singleton_decorator import singleton

UpperStr = Annotated[str, AfterValidator(lambda v: v.upper())]

# https://docs.pydantic.dev/latest/concepts/pydantic_settings/#environment-variable-names


class _BaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='../.env',
        extra='ignore',
        str_strip_whitespace=True,
        validate_default=True,
        case_sensitive=False,
    )


class LoggerSettings(_BaseSettings):
    path: Path = Field(default=Path('../logs/app.log'))
    rotation: str = Field(default='1 day')
    retention: str = Field(default='1 month')
    compression: str = Field(default='zip')
    encoding: str = Field(default='utf-8')
    level: UpperStr = Field(default='trace')


class BackendSettings(_BaseSettings):
    host: str = Field(default='127.0.0.1')
    port: int = Field(default=8000)
    session_secret_key: str


class PostgresSettings(_BaseSettings):
    driver: str = Field()
    host: str = Field()
    port: int = Field()
    user: str = Field()
    password: str = Field()
    database: str = Field()


class S3Settings(_BaseSettings):
    service_name: str = Field(default='s3')
    access_key_id: str = Field(serialization_alias='aws_access_key_id')
    secret_access_key: str = Field(serialization_alias='aws_secret_access_key')
    bucket_name: str
    endpoint_url: str
    region_name: str
    public_url: str


class OryKratosSettings(_BaseSettings):
    public_url: str = Field()
    admin_url: str = Field()
    session_cookie: str = Field()
    admin_schema: str = Field()


class TinkoffIntegrationSettings(_BaseSettings):
    terminal_key: str
    password: str
    url: str


class CDEKIntegrationSettings(_BaseSettings):
    client_id: str
    password: str
    url: str


class EnvSettings(_BaseSettings):
    environment: str
    backend: BackendSettings = BackendSettings(_env_prefix='BACKEND_')
    postgres: PostgresSettings = PostgresSettings(_env_prefix='POSTGRES_')
    logger: LoggerSettings = LoggerSettings(_env_prefix='LOGURU_')
    ory_kratos: OryKratosSettings = OryKratosSettings(_env_prefix='ORY_KRATOS_')
    tinkoff_integration: TinkoffIntegrationSettings = TinkoffIntegrationSettings(_env_prefix='TINKOFF_INTEGRATION_')
    cdek_integration: CDEKIntegrationSettings = CDEKIntegrationSettings(_env_prefix='CDEK_INTEGRATION_')
    s3: S3Settings = S3Settings(_env_prefix='S3_')
    redis_dsn: RedisDsn = Field()
    sentry_dsn: str = Field()
    debug: bool = Field(default=False)
    debug_sql_alchemy: bool = Field(default=False)
    use_test_db: bool = Field(default=False)
    public_host: AnyUrl


@singleton
class Settings(BaseModel):
    env: EnvSettings = EnvSettings()
    root_path: DirectoryPath = Path(__file__).parent.parent.resolve()
    logs_path: DirectoryPath = root_path.joinpath('logs')
    trace_id_header: str = 'X-Request-ID'
    sentry_id_header: str = 'X-Sentry-ID'
