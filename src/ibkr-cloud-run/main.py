"""Run the IBKR Flex Query export pipeline on Google Cloud Run.

The service downloads an Interactive Brokers report, uploads the resulting
CSV file to Google Drive, and optionally sends a Slack notification. Cloud
Scheduler triggers the pipeline through the ``/run`` endpoint.
"""

# ================================================================================
#                                     PACKAGES
# ================================================================================

import os
import time
import xml.etree.ElementTree as ET

import requests
from flask import Flask, Response, jsonify
from google.cloud import secretmanager
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload


# ================================================================================
#                               APPLICATION SETUP
# ================================================================================

app = Flask(__name__)


# ================================================================================
#                                  CONFIGURATION
# ================================================================================

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
DRIVE_FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]
OUTPUT_FILE_NAME = os.getenv("OUTPUT_FILE_NAME", "ibkr_extract.csv")

IBKR_FLEX_TOKEN_SECRET = "ibkr-flex-token"
IBKR_FLEX_QUERY_ID_SECRET = "ibkr-flex-query-id"
GOOGLE_REFRESH_TOKEN_SECRET = "google-refresh-token"
GOOGLE_CLIENT_ID_SECRET = "google-client-id"
GOOGLE_CLIENT_SECRET_SECRET = "google-client-secret"
SLACK_WEBHOOK_URL_SECRET = "slack-webhook-url"

IBKR_SEND_URL = (
    "https://ndcdyn.interactivebrokers.com/"
    "AccountManagement/FlexWebService/SendRequest"
)

DEFAULT_IBKR_GET_URL = (
    "https://ndcdyn.interactivebrokers.com/"
    "AccountManagement/FlexWebService/GetStatement"
)

IBKR_USER_AGENT = "Python/3 CloudRun IBKRAutomation"
IBKR_REPORT_MAX_ATTEMPTS = 10
IBKR_REPORT_RETRY_DELAY_SECONDS = 5


# ================================================================================
#                              SECRET MANAGER ACCESS
# ================================================================================


def get_secret(secret_id: str) -> str:
    """Return the latest value of a Google Secret Manager secret."""
    client = secretmanager.SecretManagerServiceClient()

    secret_name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"

    response = client.access_secret_version(request={"name": secret_name})

    return response.payload.data.decode("utf-8")


# ================================================================================
#                              DOWNLOAD IBKR REPORT
# ================================================================================


def download_ibkr_report() -> bytes:
    """Execute the configured IBKR Flex Query and return its CSV content."""
    token = get_secret(IBKR_FLEX_TOKEN_SECRET)
    query_id = get_secret(IBKR_FLEX_QUERY_ID_SECRET)

    headers = {"User-Agent": IBKR_USER_AGENT}

    request_params = {
        "t": token,
        "q": query_id,
        "v": "3",
    }

    request_response = requests.get(
        IBKR_SEND_URL,
        params=request_params,
        headers=headers,
        timeout=30,
    )
    request_response.raise_for_status()

    root = ET.fromstring(request_response.text)

    status = root.findtext("Status")
    if status != "Success":
        error_code = root.findtext("ErrorCode")
        error_message = root.findtext("ErrorMessage")

        raise RuntimeError(
            f"IBKR SendRequest a échoué : "
            f"{error_code} - {error_message}"
        )

    reference_code = root.findtext("ReferenceCode")
    get_statement_url = (
        root.findtext("Url")
        or root.findtext("url")
        or DEFAULT_IBKR_GET_URL
    )

    if not reference_code:
        raise RuntimeError(
            "IBKR n'a retourné aucun ReferenceCode."
        )

    statement_params = {
        "t": token,
        "q": reference_code,
        "v": "3",
    }

    # IBKR may need a few seconds to generate the requested report.
    for _ in range(IBKR_REPORT_MAX_ATTEMPTS):
        statement_response = requests.get(
            get_statement_url,
            params=statement_params,
            headers=headers,
            timeout=60,
        )
        statement_response.raise_for_status()

        content = statement_response.content
        text_preview = statement_response.text[:500]

        if "<Status>Fail</Status>" in text_preview:
            try:
                error_root = ET.fromstring(statement_response.text)
                error_code = error_root.findtext("ErrorCode")
                error_message = error_root.findtext("ErrorMessage")
            except ET.ParseError:
                error_code = None
                error_message = statement_response.text[:200]

            # Error 1019 indicates that the report is still being generated.
            if error_code == "1019":
                time.sleep(IBKR_REPORT_RETRY_DELAY_SECONDS)
                continue

            raise RuntimeError(
                f"IBKR GetStatement a échoué : "
                f"{error_code} - {error_message}"
            )

        if not content:
            raise RuntimeError("Le rapport IBKR téléchargé est vide.")

        return content

    raise TimeoutError(
        "Le rapport IBKR n'était toujours pas prêt après "
        f"{IBKR_REPORT_MAX_ATTEMPTS} essais."
    )


# ================================================================================
#                             GOOGLE DRIVE INTEGRATION
# ================================================================================


def get_google_credentials() -> Credentials:
    """Build Google OAuth credentials from Secret Manager values.

    The refresh token grants offline access to a personal Google Drive
    account without requiring an interactive authentication flow.
    """
    return Credentials(
        token=None,
        refresh_token=get_secret(GOOGLE_REFRESH_TOKEN_SECRET),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=get_secret(GOOGLE_CLIENT_ID_SECRET),
        client_secret=get_secret(GOOGLE_CLIENT_SECRET_SECRET),
        scopes=[
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )


def upload_to_drive(content: bytes) -> str:
    """Create or update the configured IBKR CSV file in Google Drive."""
    credentials = get_google_credentials()

    drive_service = build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )

    escaped_name = OUTPUT_FILE_NAME.replace("'", "\\'")

    query = (
        f"name = '{escaped_name}' "
        f"and '{DRIVE_FOLDER_ID}' in parents "
        f"and trashed = false"
    )

    existing_files = (
        drive_service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id,name)",
            pageSize=10,
        )
        .execute()
        .get("files", [])
    )

    media = MediaInMemoryUpload(
        content,
        mimetype="text/csv",
        resumable=False,
    )

    if existing_files:
        file_id = existing_files[0]["id"]

        updated_file = (
            drive_service.files()
            .update(
                fileId=file_id,
                media_body=media,
                fields="id,name,modifiedTime",
            )
            .execute()
        )

        return updated_file["id"]

    file_metadata = {
        "name": OUTPUT_FILE_NAME,
        "parents": [DRIVE_FOLDER_ID],
        "mimeType": "text/csv",
    }

    created_file = (
        drive_service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id,name",
        )
        .execute()
    )

    return created_file["id"]


# ================================================================================
#                               SLACK NOTIFICATIONS
# ================================================================================


def notify_slack(message: str) -> None:
    """Send a Slack message when the optional webhook secret is available."""
    try:
        webhook_url = get_secret(SLACK_WEBHOOK_URL_SECRET)
    except Exception:
        # Slack notifications are optional and must not block the pipeline.
        return

    response = requests.post(
        webhook_url,
        json={"text": message},
        timeout=15,
    )
    response.raise_for_status()


# ================================================================================
#                                  HTTP ENDPOINTS
# ================================================================================


@app.post("/run")
def run_pipeline() -> tuple[Response, int]:
    """Run the IBKR-to-Drive pipeline when called by Cloud Scheduler."""
    try:
        report_content = download_ibkr_report()
        drive_file_id = upload_to_drive(report_content)

        notify_slack(
            "✅ Le rapport IBKR a été téléchargé et enregistré "
            f"dans Google Drive. File ID : {drive_file_id}"
        )

        return jsonify(
            {
                "status": "success",
                "drive_file_id": drive_file_id,
                "size_bytes": len(report_content),
            }
        ), 200

    except Exception as error:
        app.logger.exception("Échec du pipeline IBKR")

        try:
            notify_slack(
                f"❌ Échec du pipeline IBKR : {error}"
            )
        except Exception:
            pass

        return jsonify(
            {
                "status": "error",
                "error": str(error),
            }
        ), 500


@app.get("/health")
def health() -> tuple[Response, int]:
    """Return a lightweight health check for Cloud Run."""
    return jsonify({"status": "ok"}), 200
