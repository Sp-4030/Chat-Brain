"""YouTube API Client and Authentication Manager.

Manages OAuth 2.0 credentials lifecycle, token refresh, and YouTube Data API v3 service initialization.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from config.settings import Settings, get_settings
from utils.logger import get_logger

logger = get_logger("YouTubeClient")


class YouTubeClientManager:
    """Handles Google OAuth authentication and YouTube Data API client creation."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._service: Optional[Resource] = None
        self._channel_id: Optional[str] = None
        self._channel_title: Optional[str] = None

    def get_service(self) -> Resource:
        """Obtain authenticated YouTube Data API v3 resource."""
        if self._service is not None:
            return self._service

        credentials = self._authenticate()
        self._service = build(
            "youtube",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )
        return self._service

    def _authenticate(self) -> Credentials:
        """Load, refresh, or initiate Google OAuth desktop flow."""
        credentials: Optional[Credentials] = None
        token_path = Path(self.settings.TOKEN_FILE)
        secret_path = Path(self.settings.CLIENT_SECRET_FILE)

        # 1. Try loading cached token
        if token_path.exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(token_path),
                    self.settings.SCOPES,
                )
                logger.info("Loaded cached credentials from %s", token_path)
            except Exception as err:
                logger.warning("Could not load token file: %s", err)
                credentials = None

        # 2. Refresh expired token
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                logger.info("Refreshing expired Google OAuth token...")
                credentials.refresh(Request())
                with open(token_path, "w", encoding="utf-8") as token_file:
                    token_file.write(credentials.to_json())
                logger.info("Successfully refreshed and saved OAuth token.")
            except Exception as err:
                logger.warning("Token refresh failed: %s", err)
                credentials = None

        # 3. Interactive OAuth login if invalid
        if not credentials or not credentials.valid:
            if not secret_path.exists():
                raise FileNotFoundError(
                    f"OAuth client secret file not found: {secret_path}. "
                    "Download client_secret.json from Google Cloud Console and place it in the project root."
                )

            logger.info("Initiating Google OAuth login flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(secret_path),
                self.settings.SCOPES,
            )
            credentials = flow.run_local_server(port=0)

            with open(token_path, "w", encoding="utf-8") as token_file:
                token_file.write(credentials.to_json())
            logger.info("OAuth login completed and token saved to %s", token_path)

        return credentials

    def get_authenticated_channel_info(self) -> Tuple[Optional[str], Optional[str]]:
        """Fetch channel ID and title for the authenticated user."""
        if self._channel_id and self._channel_title:
            return self._channel_id, self._channel_title

        service = self.get_service()
        try:
            response = service.channels().list(part="id,snippet", mine=True).execute()
            items = response.get("items", [])
            if items:
                self._channel_id = items[0].get("id")
                self._channel_title = items[0].get("snippet", {}).get("title")
                return self._channel_id, self._channel_title
        except Exception as err:
            logger.warning("Could not fetch authenticated channel info: %s", err)

        return None, None
