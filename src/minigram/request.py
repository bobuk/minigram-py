import asyncio
import asyncio.exceptions
import importlib.util
import json
import ssl
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

if importlib.util.find_spec("aiohttp"):
    import aiohttp

    async def async_req(url: str, data: Optional[dict] = None) -> Tuple[int, dict]:
        try:
            async with aiohttp.ClientSession() as client:
                async with client.post(
                    url, json=data, headers={"content-type": "application/json"}
                ) as response:
                    return response.status, await response.json()
        except asyncio.exceptions.TimeoutError:
            return 200, {"result": []}

elif importlib.util.find_spec("httpx"):
    import httpx

    async def async_req(url: str, data: Optional[dict] = None) -> Tuple[int, dict]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=data,
                    headers={"content-type": "application/json"},
                    timeout=180,
                )
                return response.status_code, response.json()
        except httpx.ReadTimeout:
            return 200, {"result": []}

    def sync_req(url: str, data: Optional[dict] = None) -> Tuple[int, dict]:
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json=data,
                    headers={"content-type": "application/json"},
                    timeout=180,
                )
                return response.status_code, response.json()
        except httpx.ReadTimeout:
            return 200, {"result": []}

else:

    async def async_req(url: str, data: Optional[Dict] = None) -> Tuple[int, Dict]:
        parsed_url = urlparse(url)
        host, port = (
            parsed_url.hostname,
            parsed_url.port or (443 if parsed_url.scheme == "https" else 80),
        )

        headers = {"Host": host, "Content-Type": "application/json"}

        if data is None:
            data = {}

        body = json.dumps(data).encode("utf-8")
        content_length = len(body)
        headers["Content-Length"] = str(content_length)

        rb = f"POST {parsed_url.path or '/'} HTTP/1.1\r\n"
        rb += "\r\n".join(f"{key}: {value}" for key, value in headers.items())
        rb += "\r\n\r\n"
        request = rb.encode("utf-8") + body

        scheme = (
            ssl._create_unverified_context() if parsed_url.scheme == "https" else None
        )
        reader, writer = await asyncio.open_connection(host, port, ssl=scheme)
        writer.write(request)
        await writer.drain()

        status_line = await reader.readline()
        status_code = int(status_line.split()[1])

        headers = {}
        while True:
            line = await reader.readline()
            if line == b"\r\n":
                break
            key, value = line.decode("utf-8").strip().split(": ", 1)
            headers[key] = value

        response_data = b""
        content_length = int(str(headers.get("Content-Length", "0")))
        while True:
            chunk = await reader.read(1024)
            response_data += chunk
            if len(response_data) >= content_length or not chunk:
                break

        writer.close()
        await writer.wait_closed()

        response_json = json.loads(response_data.decode("utf-8"))
        return status_code, response_json

    import urllib.request
    import urllib.error

    def sync_req(url: str, data: Optional[dict] = None) -> Tuple[int, dict]:
        headers = {"content-type": "application/json"}
        try:
            ssl_context = ssl._create_unverified_context()
            req = urllib.request.Request(
                url, data=json.dumps(data).encode("utf-8"), headers=headers
            )
            with urllib.request.urlopen(
                req, timeout=180, context=ssl_context
            ) as response:
                status_code = response.getcode()
                response_data = response.read()
                return status_code, json.loads(response_data.decode("utf-8"))
        except urllib.error.URLError as e:
            return e.code, {"result": e.reason}
