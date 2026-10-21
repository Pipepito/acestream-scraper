"""File delivery for HLS segments that FFmpeg or session cleanup can remove."""
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse
from starlette.types import Message, Receive, Scope, Send


class HLSFileResponse(FileResponse):
    """Delay headers until FileResponse has opened and read the segment.

    A stat_result avoids a second stat, but does not keep the file alive until
    FileResponse opens it. Buffer only the start message so a missing file can
    still become a 404. Once delivery starts, FileResponse owns the open file
    through bounded reads, range handling and cancellation cleanup.
    """

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # A server receiving pathsend would reopen the pathname after our checks.
        # Keep file ownership in FileResponse throughout the transfer instead.
        scope = {**scope, "extensions": {
            key: value for key, value in scope.get("extensions", {}).items()
            if key != "http.response.pathsend"
        }}
        pending_start: Message | None = None
        headers_sent = False

        async def send_after_open(message: Message) -> None:
            nonlocal pending_start, headers_sent
            if message["type"] == "http.response.start":
                pending_start = message
                return
            if pending_start is not None:
                headers_sent = True
                await send(pending_start)
                pending_start = None
            await send(message)

        try:
            await super().__call__(scope, receive, send_after_open)
        except OSError:
            if headers_sent:
                raise
            raise HTTPException(status_code=404, detail="Segment not ready") from None
