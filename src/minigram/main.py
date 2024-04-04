import asyncio
import re
from copy import deepcopy
from typing import Optional, Any

from .request import req
from .ass import ass


def parse_markdown(text: str, p: bool = False) -> str:
    text = re.sub(r"&", "&amp;", text)
    text = re.sub(r"<", "&lt;", text)
    text = re.sub(r">", "&gt;", text)

    patterns = [
        (r'(http[s]?://[^(\s|")]+)', '<a href="\\1">\\1</a>'),
        (r"^# (.*)$", "<h1>\\1</h1>"),
        (r"\*\*(.+?)\*\*", "<b>\\1</b>"),
        (r"__(.+?)__", "<i>\\1</i>"),
        (r"```(\w+)\n(.*?)```", '<pre><code class="language-\\1">\\2</code></pre>'),
        (r"```\n(.*?)```", "<pre><code>\\1</code></pre>"),
        (r"`([^`]+)`", "<code>\\1</code>"),
        (r"^> (.*)", "<blockquote>\\1</blockquote>"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.DOTALL)

    if p:
        lines = text.split("\n")
        in_code = False
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("<pre"):
                in_code = True
            if "</pre>" in line:
                in_code = False
                continue
            if not in_code:
                lines[i] = "<p>" + line + "</p>"

        text = "\n".join(lines)

    return text


def extract_value(data: dict[str, Any], dotted: str, default: Any = None) -> Any:
    if "." not in dotted:
        return data.get(dotted, default)
    segment, other = dotted.split(".", 1)
    if segment not in data:
        return default
    return extract_value(data[segment], other)


class MiniGramMessage:
    def __init__(self, data: dict):
        self.data = deepcopy(data)
        if "message" not in self.data:
            raise ValueError("no `message` in your data!")
        msg = self.data["message"]
        self.chat_id = extract_value(msg, "chat.id")
        self.text = extract_value(msg, "text")
        self.message_id = extract_value(msg, "message_id")
        self.from_user = extract_value(msg, "from", {})
        self.from_id = self.from_user.get("id")

    def __repr__(self):
        return f"<MiniGramMessage from {self.from_id}/{self.from_user} {self.chat_id} {self.message_id} {self.text}>"

    def reply(self, text: str) -> "MiniGramMessage":
        self.text = text
        return self


class MiniGram:
    def __init__(self, key: str):
        global CURRENT
        self.key = key
        self.last_updated_id = 0
        self.post_init()
        CURRENT = self

    def post_init(self):
        pass

    @ass
    async def shutdown(self):
        await self.delete_webhook()

    @ass
    async def incoming(self, msg: MiniGramMessage) -> Optional[MiniGramMessage]:
        pass

    @classmethod
    def current(cls) -> "MiniGram":
        global CURRENT
        if CURRENT is None:
            raise ValueError("No current MiniGram")
        return CURRENT

    @ass
    async def req(self, method: str, **kwargs) -> dict:
        url = f"https://api.telegram.org/bot{self.key}/{method}"
        code, response = await req(url, kwargs)
        return response

    @ass
    async def start_polling(self):
        while True:
            updates = await self.get_updates()
            for update in updates.get("result", []):
                msg = MiniGramMessage(update)
                res = await self.incoming(msg)
                if res:
                    await self.reply_to_message(res)
                self.last_updated_id = update["update_id"]
            await asyncio.sleep(0.1)

    @ass
    async def get_updates(self) -> dict:
        if self.last_updated_id != 0:
            return await self.req(
                "getUpdates", offset=self.last_updated_id + 1, timeout=60
            )
        return await self.req("getUpdates", timeout=60)

    @ass
    async def send_text(
        self, chat_id: int, text: str, parse_mode: str = "HTML", **kwargs
    ) -> dict:
        return await self.req(
            "sendMessage", chat_id=chat_id, text=text, parse_mode=parse_mode, **kwargs
        )

    @ass
    async def reply_to_message(self, reply: MiniGramMessage):
        reply_params = {
            "chat_id": reply.chat_id,
            "text": reply.text,
            "reply_to_message_id": reply.message_id,
        }
        return await self.req("sendMessage", **reply_params)

    @ass
    async def set_webhook(self, url: str) -> dict:
        return await self.req("setWebhook", url=url)

    @ass
    async def delete_webhook(self) -> dict:
        return await self.req("deleteWebhook")

    @ass
    async def get_webhook_info(self) -> dict:
        return await self.req("getWebhookInfo")

    async def async_handler(self, data: dict) -> None:
        msg = MiniGramMessage(data)
        res = await self.incoming(msg)
        if res:
            await self.reply_to_message(res)

    def sync_handler(self, data: dict) -> None:
        msg = MiniGramMessage(data)
        res = self.incoming(msg)
        if res:
            self.reply_to_message(res)


CURRENT: MiniGram | None = None
