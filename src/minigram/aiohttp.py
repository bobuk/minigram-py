import aiohttp.web

from .main import AsyncMiniGram


class AioMiniGram(AsyncMiniGram):
    async def aiohttp_handler(
        self, request: aiohttp.web.Request
    ) -> aiohttp.web.Response:
        try:
            data = await request.json()
            await self.async_handler(data)
        except Exception as e:
            print("Error in http_handler, aiohttp", e)
        return aiohttp.web.Response()
