from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from .main import AsyncMiniGram


class StarletteMiniGram(AsyncMiniGram):
    async def starlette_handler(self, request: Request) -> Response:
        try:
            data = await request.json()
            await self.async_handler(data)
        except Exception as e:
            print("Error in http_handler, starlette", e)
        return JSONResponse({"status": "ok"})
