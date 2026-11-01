"""Read live authority evidence without converting transport faults to denials.

This helper grants nothing and never retries. Callers must keep their existing
identity, current-Turn, permission, expiry and compare-and-swap checks.
"""

import json
import urllib.error
import urllib.request


class AuthorityReadUnavailable(RuntimeError):
    """Authority could not be established; dependent writes must stop."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(f"material authority read unavailable ({reason}); no authorization established")


class AuthorityReadDenied(RuntimeError):
    """The authority endpoint explicitly rejected access; do not retry it."""

    def __init__(self, status):
        self.status = status
        super().__init__(f"material authority read denied (HTTP {status}); no authorization established")


def read_authority_json(url, *, timeout=60, opener=None):
    """Return one verified-success JSON response or a public-safe typed error.

    Do not expose URLs, server response bodies or transport exception messages:
    they can contain private selectors or credentials. These RuntimeError
    subclasses intentionally survive legacy ``except (OSError, ValueError)``
    verifier fences, so SDK callers see uncertainty rather than a false denial.
    """
    open_url = urllib.request.urlopen if opener is None else opener
    try:
        with open_url(url, timeout=timeout) as response:
            value = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise AuthorityReadDenied(exc.code) from None
        raise AuthorityReadUnavailable(f"http_{exc.code}") from None
    except urllib.error.URLError as exc:
        reason = "timeout" if isinstance(exc.reason, TimeoutError) else "connection"
        raise AuthorityReadUnavailable(reason) from None
    except TimeoutError:
        raise AuthorityReadUnavailable("timeout") from None
    except OSError:
        raise AuthorityReadUnavailable("connection") from None
    except (json.JSONDecodeError, UnicodeError):
        raise AuthorityReadUnavailable("invalid_json") from None
    if not isinstance(value, dict) or value.get("ok") is not True:
        raise AuthorityReadUnavailable("unsuccessful_response")
    return value
