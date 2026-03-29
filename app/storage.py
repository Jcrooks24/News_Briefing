import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from app import config

log = logging.getLogger(__name__)


def _client():
    return boto3.client(
        "s3",
        endpoint_url=config.R2_ENDPOINT_URL,
        aws_access_key_id=config.R2_ACCESS_KEY_ID,
        aws_secret_access_key=config.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )


def _key(audio_token: str) -> str:
    return f"{audio_token}/latest.mp3"


def upload_audio(audio_bytes: bytes, audio_token: str) -> None:
    _client().put_object(
        Bucket=config.R2_BUCKET_NAME,
        Key=_key(audio_token),
        Body=audio_bytes,
        ContentType="audio/mpeg",
    )
    log.info("Uploaded audio to R2: %s (%d KB)", _key(audio_token), len(audio_bytes) // 1024)


def download_audio(audio_token: str) -> bytes:
    obj = _client().get_object(Bucket=config.R2_BUCKET_NAME, Key=_key(audio_token))
    return obj["Body"].read()


def audio_exists(audio_token: str) -> bool:
    try:
        _client().head_object(Bucket=config.R2_BUCKET_NAME, Key=_key(audio_token))
        return True
    except ClientError:
        return False
