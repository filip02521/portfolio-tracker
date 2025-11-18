from __future__ import annotations

import datetime as dt
import logging
import os
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Minimal GitHub REST client for repository statistics.

    Supports optional personal access token via GITHUB_TOKEN for higher rate limits.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None, session: Optional[requests.Session] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self._session = session or requests.Session()

    def _headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "due-diligence-collector",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_recent_commit_count(self, owner: str, repo: str, days: int = 30) -> Optional[int]:
        """
        Returns number of commits in the last `days` days (best-effort, limited to first 100 results).
        """
        if not owner or not repo:
            return None
        since = (dt.datetime.utcnow() - dt.timedelta(days=days)).isoformat(timespec="seconds") + "Z"
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/commits"
        params = {"since": since, "per_page": 100}
        try:
            response = self._session.get(url, headers=self._headers(), params=params, timeout=8)
            if response.status_code != 200:
                return None
            data = response.json()
            if isinstance(data, list):
                return len(data)
        except Exception as exc:  # pragma: no cover - network failure
            logger.debug("GitHub commits fetch failed for %s/%s: %s", owner, repo, exc)
        return None

    def get_contributor_count(self, owner: str, repo: str) -> Optional[int]:
        """
        Returns the number of unique contributors (first page up to 100 users).
        """
        if not owner or not repo:
            return None
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contributors"
        params = {"per_page": 100, "anon": "true"}
        try:
            response = self._session.get(url, headers=self._headers(), params=params, timeout=8)
            if response.status_code != 200:
                return None
            data = response.json()
            if isinstance(data, list):
                return len(data)
        except Exception as exc:  # pragma: no cover
            logger.debug("GitHub contributors fetch failed for %s/%s: %s", owner, repo, exc)
        return None

    @staticmethod
    def extract_owner_repo(url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse a GitHub repository URL and return (owner, repo).
        """
        if not url or "github.com" not in url:
            return None, None
        try:
            path = url.split("github.com/", 1)[1]
            parts = path.strip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1].replace(".git", "")
                return owner, repo
        except Exception:
            pass
        return None, None

