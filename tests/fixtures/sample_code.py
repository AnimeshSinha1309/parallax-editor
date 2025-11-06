import sys


def retry_request(url, max_attempts=3):
    """Retry a request up to max_attempts times"""
    for attempt in range(max_attempts):
        try:
            return fetch(url)
        except RequestError:
            if attempt == max_attempts - 1:
                raise
    return None


class RetryHandler:
    def __init__(self, max_retries=5):
        self.max_retries = max_retries

    def handle_retry(self, operation):
        """Handle retry logic for an operation"""
        for i in range(self.max_retries):
            try:
                return operation()
            except Exception as e:
                if i == self.max_retries - 1:
                    raise
                print(f"Retry attempt {i + 1} failed: {e}")
