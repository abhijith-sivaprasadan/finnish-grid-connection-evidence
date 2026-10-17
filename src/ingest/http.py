"""Bounded HTTP retries with credential-safe errors."""
import time
import requests


class SourceError(RuntimeError):
    pass


class HttpClient:
    def __init__(self, session=None, min_interval=2.1, sleep=time.sleep, clock=time.monotonic):
        self.session = session or requests.Session()
        self.min_interval = min_interval
        self.sleep = sleep
        self.clock = clock
        self.last_request = None

    def get(self, url, **kwargs):
        for attempt in range(4):
            if self.last_request is not None:
                self.sleep(max(0, self.min_interval - (self.clock() - self.last_request)))
            self.last_request = self.clock()
            try:
                response = self.session.get(url, timeout=(10, 45), allow_redirects=False, **kwargs)
            except requests.RequestException:
                if attempt == 3:
                    raise SourceError("Source request failed after four attempts; check network access") from None
                self.sleep(2 ** attempt)
                continue
            if response.status_code == 200:
                return response
            if response.status_code in {401, 403}:
                raise SourceError("Source rejected credentials; check your API subscription and key")
            if response.status_code == 429 or response.status_code >= 500:
                retry = response.headers.get("Retry-After", "")
                if attempt < 3:
                    # Never retry earlier than a numeric Retry-After; long waits are surfaced.
                    delay = float(retry) if retry.isdigit() else 2 ** attempt
                    if delay > 60:
                        raise SourceError("Source requested a long retry delay; try this ingestion later")
                    self.sleep(max(2.1, delay))
                    continue
            # Do not expose response bodies, request URLs, or tokens embedded in ENTSO-E URLs.
            raise SourceError(f"Source returned HTTP {response.status_code}; no records imported")
        raise SourceError("Source retry budget exhausted")
