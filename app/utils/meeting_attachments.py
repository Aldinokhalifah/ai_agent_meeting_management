import urllib3
from minio import Minio

from db.postgres import execute_query
from core.config import (
    MINIO_ENDPOINT,
    MINIO_PORT,
    MINIO_USE_SSL,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
    MINIO_REGION,
)

_client: Minio | None = None


def _get_client() -> Minio:
    global _client

    if _client is None:
        if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
            raise Exception("MINIO_ACCESS_KEY / MINIO_SECRET_KEY tidak dikonfigurasi di .env")

        _client = Minio(
            f"{MINIO_ENDPOINT}:{MINIO_PORT}",
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_USE_SSL,
            # region eksplisit: tidak perlu menghubungi MinIO hanya untuk mencari region
            region=MINIO_REGION,
            # timeout pendek supaya MinIO yang mati tidak membuat proses menggantung lama
            http_client=urllib3.PoolManager(
                timeout=urllib3.Timeout(connect=5, read=15),
                retries=urllib3.Retry(total=2, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504]),
            ),
        )

    return _client


def get_meeting_object_keys(meeting_id: str) -> list[str]:
    """
    Ambil key objek MinIO milik sebuah meeting (semua status, termasuk 'pending').
    Harus dipanggil SEBELUM meeting dihapus: DELETE meeting menghapus baris
    meeting_attachments lewat cascade, tetapi tidak menghapus file di MinIO.
    """
    rows = execute_query(
        "SELECT object_key FROM meeting_attachments WHERE meeting_id = %s",
        (meeting_id,),
        fetch="all",
    ) or []

    return [row["object_key"] for row in rows]


def remove_meeting_objects(object_keys: list[str]) -> None:
    """
    Hapus objek satu per satu. Tidak pernah melempar error: kegagalan hanya di-log,
    karena meeting sudah terhapus dan sisa objek yatim tidak terlihat oleh user.
    """
    for object_key in object_keys:
        try:
            _get_client().remove_object(MINIO_BUCKET, object_key)
        except Exception as e:
            print(f"[MINIO ERROR] gagal menghapus objek {object_key}: {str(e)}")
