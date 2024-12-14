from fastapi import Request
from fastapi.responses import JSONResponse
from .main import AsyncMiniGram

class FastAPIMiniGram(AsyncMiniGram):
    async def fastapi_handler(self, request: Request) -> JSONResponse:
        try:
            data = await request.json()
            await self.async_handler(data)
        except Exception as e:
            print("Error in http_handler, fastapi", e)
        return JSONResponse({"status": "ok"})
