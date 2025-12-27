"""WhatsNext server application.

Requires: pip install whatsnext[server]
"""

from whatsnext.api.server.main import app as app

__all__ = ["app"]
