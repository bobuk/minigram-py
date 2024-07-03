import asyncio
import re
import time
from copy import deepcopy
from typing import Optional, Tuple, Any

from .request import sync_req, async_req


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

class BaseMiniGram:
    def __init__(self, key: str):
        self.key = key
        self.last_updated_id = 0
        self.post_init()
        self.allowed_updates = [
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "inline_query",
            "chosen_inline_result",
            "callback_query",
            "shipping_query",
            "pre_checkout_query",
            "poll",
            "poll_answer",
            "my_chat_member",
            "chat_member",
            "chat_join_request",
            "message_reaction",
            "message_reaction_count",
            "chat_boost",
            "removed_chat_boost"
        ]

    def post_init(self):
            pass


class AsyncMiniGram(BaseMiniGram):
    def __init__(self, key: str):
        global CURRENT_ASYNC
        super().__init__(key)
        CURRENT_ASYNC = self

    async def shutdown(self):
        await self.delete_webhook()

    async def incoming(self, msg: MiniGramMessage) -> Optional[MiniGramMessage]:
        pass

    async def edited(self, msg: MiniGramMessage) -> Optional[MiniGramMessage]:
        pass

    @classmethod
    def current(cls) -> "AsyncMiniGram":
        global CURRENT_ASYNC
        if CURRENT_ASYNC is None:
            raise ValueError("No current MiniGram")
        return CURRENT_ASYNC

    async def req(self, method: str, **kwargs) -> dict:
        url = f"https://api.telegram.org/bot{self.key}/{method}"
        code, response = await async_req(url, kwargs)
        return response

    async def start_polling(self):
        while True:
            updates = await self.get_updates()
            for update in updates.get("result", []):
                update_type, update_data = self._identify_update_type(update)
                if update_type:
                    await self._process_update(update_type, update_data)
                self.last_updated_id = update["update_id"]
            await asyncio.sleep(0.1)

    def _identify_update_type(self, update: dict) -> Tuple[Optional[str], Optional[dict]]:
        update_types = self.allowed_updates
        for update_type in update_types:
            if update_type in update:
                return update_type, update[update_type]
        return None, None

    async def _process_update(self, update_type: str, update_data: dict):
        handler_method = f"handle_{update_type}"
        if hasattr(self, handler_method):
            await getattr(self, handler_method)(update_data)
        else:
            print(f"No handler implemented for update type: {update_type}")

    async def handle_message(self, message_data: dict):
        msg = MiniGramMessage({"message": message_data})
        res = await self.incoming(msg)
        if res:
            await self.reply_to_message(res)

    async def handle_edited_message(self, message_data: dict):
        msg = MiniGramMessage({"message": message_data})
        res = await self.edited(msg)
        if res:
            await self.reply_to_message(res)

    async def get_updates(self) -> dict:
        params = {
            "timeout": 60,
            "allowed_updates": self.allowed_updates
        }
        if self.last_updated_id != 0:
            params["offset"] = self.last_updated_id + 1
        return await self.req("getUpdates", **params)

    async def send_text(
        self, chat_id: int, text: str, parse_mode: str = "HTML", **kwargs
    ) -> dict:
        return await self.req(
            "sendMessage", chat_id=chat_id, text=text, parse_mode=parse_mode, **kwargs
        )

    async def reply_to_message(self, reply: MiniGramMessage):
        reply_params = {
            "chat_id": reply.chat_id,
            "text": reply.text,
            "reply_to_message_id": reply.message_id,
        }
        return await self.req("sendMessage", **reply_params)

    async def set_webhook(self, url: str) -> dict:
        return await self.req("setWebhook", url=url)

    async def delete_webhook(self) -> dict:
        return await self.req("deleteWebhook")

    async def get_webhook_info(self) -> dict:
        return await self.req("getWebhookInfo")

    async def async_handler(self, data: dict) -> None:
        msg = MiniGramMessage(data)
        res = await self.incoming(msg)
        if res:
            await self.reply_to_message(res)


class MiniGram(BaseMiniGram):
    def __init__(self, key: str):
        global CURRENT_SYNC
        super().__init__(key)
        CURRENT_SYNC = self

    def shutdown(self):
        self.delete_webhook()

    def incoming(self, msg: MiniGramMessage) -> Optional[MiniGramMessage]:
        pass

    def edited(self, msg: MiniGramMessage) -> Optional[MiniGramMessage]:
        pass

    @classmethod
    def current(cls) -> "MiniGram":
        global CURRENT_SYNC
        if CURRENT_SYNC is None:
            raise ValueError("No current MiniGram")
        return CURRENT_SYNC

    def req(self, method: str, **kwargs) -> dict:
        url = f"https://api.telegram.org/bot{self.key}/{method}"
        code, response = sync_req(url, kwargs)
        return response

    def start_polling(self):
        while True:
            updates = self.get_updates()
            for update in updates.get("result", []):
                update_type, update_data = self._identify_update_type(update)
                if update_type:
                    self._process_update(update_type, update_data)
                self.last_updated_id = update["update_id"]
            time.sleep(0.01)

    def _identify_update_type(self, update: dict) -> Tuple[Optional[str], Optional[dict]]:
        update_types = self.allowed_updates
        for update_type in update_types:
            if update_type in update:
                return update_type, update[update_type]
        return None, None

    def _process_update(self, update_type: str, update_data: dict):
        handler_method = f"handle_{update_type}"
        if hasattr(self, handler_method):
            getattr(self, handler_method)(update_data)
        else:
            print(f"No handler implemented for update type: {update_type}")

    def handle_message(self, message_data: dict):
        msg = MiniGramMessage({"message": message_data})
        res = self.incoming(msg)
        if res:
            self.reply_to_message(res)

    def handle_edited_message(self, message_data: dict):
        msg = MiniGramMessage({"message": message_data})
        res = self.edited(msg)
        if res:
            self.reply_to_message(res)

    def get_updates(self) -> dict:
        params = {
            "timeout": 60,
            "allowed_updates": self.allowed_updates
        }
        if self.last_updated_id != 0:
            params["offset"] = self.last_updated_id + 1
        return self.req("getUpdates", **params)

    def send_text(
        self, chat_id: int, text: str, parse_mode: str = "HTML", **kwargs
    ) -> dict:
        return self.req(
            "sendMessage", chat_id=chat_id, text=text, parse_mode=parse_mode, **kwargs
        )

    def reply_to_message(self, reply: MiniGramMessage):
        reply_params = {
            "chat_id": reply.chat_id,
            "text": reply.text,
            "reply_to_message_id": reply.message_id,
        }
        return self.req("sendMessage", **reply_params)

    def set_webhook(self, url: str) -> dict:
        return self.req("setWebhook", url=url)

    def delete_webhook(self) -> dict:
        return self.req("deleteWebhook")

    def get_webhook_info(self) -> dict:
        return self.req("getWebhookInfo")

    def sync_handler(self, data: dict) -> None:
        msg = MiniGramMessage(data)
        res = self.incoming(msg)
        if res:
            self.reply_to_message(res)


CURRENT_ASYNC: AsyncMiniGram | None = None
CURRENT_SYNC: MiniGram | None = None
