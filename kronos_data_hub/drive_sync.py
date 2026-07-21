"""
DRIVE_SYNC - Google Drive kalicilik katmani
Render'in geçici (ephemeral) diski her deploy/restart'ta sifirlandigi icin,
SQLite veritabanini Google Drive'da kalici olarak saklamak icin kullanilir.

Ortam degiskenleri (Render'da tanimli olmali):
- GOOGLE_SERVICE_ACCOUNT_JSON : service account kimlik bilgisi (JSON, tek satir)
- GOOGLE_DRIVE_FOLDER_ID      : dosyanin saklanacagi Drive klasorunun ID'si
"""
import os
import json
import io
import logging

logger = logging.getLogger("drive_sync")

DB_FILENAME = "kronos.db"
_drive_service = None


def _get_drive_service():
    global _drive_service
    if _drive_service is not None:
        return _drive_service

    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON tanimli degil, Drive senkronizasyonu atlaniyor.")
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/drive"]
        )
        _drive_service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return _drive_service
    except Exception as e:
        logger.error(f"Drive servisi baslatilamadi: {e}")
        return None


def _find_existing_file_id(service, folder_id):
    query = f"'{folder_id}' in parents and name = '{DB_FILENAME}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def download_db_from_drive(local_path):
    """Uygulama baslarken cagrilir. Drive'da dosya varsa indirir, yoksa sessizce gecer."""
    service = _get_drive_service()
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if not service or not folder_id:
        logger.info("Drive yapilandirilmamis, yerel/bos veritabani ile devam ediliyor.")
        return False

    try:
        from googleapiclient.http import MediaIoBaseDownload

        file_id = _find_existing_file_id(service, folder_id)
        if not file_id:
            logger.info("Drive'da mevcut kronos.db bulunamadi (ilk calistirma olabilir).")
            return False

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(local_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.close()
        logger.info(f"kronos.db Drive'dan indirildi -> {local_path}")
        return True
    except Exception as e:
        logger.error(f"Drive'dan indirme basarisiz: {e}")
        return False


def upload_db_to_drive(local_path):
    """/collect bittikten sonra cagrilir. Guncel dosyayi Drive'a yukler/gunceller."""
    service = _get_drive_service()
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if not service or not folder_id:
        return False

    if not os.path.exists(local_path):
        logger.warning(f"Yuklenecek dosya bulunamadi: {local_path}")
        return False

    try:
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(local_path, mimetype="application/x-sqlite3", resumable=True)
        file_id = _find_existing_file_id(service, folder_id)

        if file_id:
            service.files().update(fileId=file_id, media_body=media).execute()
            logger.info("kronos.db Drive'da guncellendi.")
        else:
            metadata = {"name": DB_FILENAME, "parents": [folder_id]}
            service.files().create(body=metadata, media_body=media, fields="id").execute()
            logger.info("kronos.db Drive'a ilk kez yuklendi.")
        return True
    except Exception as e:
        logger.error(f"Drive'a yukleme basarisiz: {e}")
        return False
