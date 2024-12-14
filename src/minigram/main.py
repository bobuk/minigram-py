import asyncio
import importlib.util
import json
import re
import time

from copy import deepcopy
from typing import Any

from .request import async_req

if not importlib.util.find_spec("aiohttp"):
    from .request import sync_req
    

DEBUG = False
ALLOWED_UPDATES = [
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
    "removed_chat_boost",
]

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"  # Reset to default color


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


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def debug(color, title, data):
    if DEBUG:
        print(f"\n{color}{now()} - {title}{RESET}\n{json.dumps(data, indent=2)}")


class MiniGramUpdate:
    def __init__(self, data: dict):
        for update_type in ALLOWED_UPDATES:
            if update_type in data:
                self.update_type = update_type
                self.payload = deepcopy(data[update_type])
                break
        if not hasattr(self, "update_type"):
            raise ValueError("unknown or unallowed update_type")

        self.update_id = extract_value(data, "update_id")
        self.chat_id = extract_value(self.payload, "chat.id")
        self.text = extract_value(self.payload, "text")
        self.message_id = extract_value(self.payload, "message_id")
        self.from_user = extract_value(self.payload, "from", {})
        self.user = extract_value(self.payload, "user", {})
        if len(self.from_user) > 0:
            self.from_id = self.from_user.get("id")
        else:
            self.from_id = self.user.get("id")

        debug(RED, "raw update:", data)
        delattr(self, "payload")
        print(self)

    def __repr__(self):
        return f"<MiniGramUpdate with type `{self.update_type}` from {self.from_id}/{self.from_user} {self.chat_id} {self.message_id} {self.text}>"


class BaseMiniGram:
    def __init__(self, key: str):
        self.key = key
        self.last_updated_id = 0
        self.post_init()
        self.allowed_updates = ALLOWED_UPDATES
        print(f"Start time: {now()}\nDEBUG is {DEBUG}")

    def post_init(self):
        pass


class AsyncMiniGram(BaseMiniGram):
    def __init__(self, key: str):
        global CURRENT_ASYNC
        super().__init__(key)
        CURRENT_ASYNC = self

    async def shutdown(self):
        await self.delete_webhook()

    @classmethod
    def current(cls) -> "AsyncMiniGram":
        global CURRENT_ASYNC
        if CURRENT_ASYNC is None:
            raise ValueError("No current MiniGram")
        return CURRENT_ASYNC

    async def req(self, method: str, **kwargs) -> dict:
        if method != "getUpdates" and DEBUG:
            tmp = deepcopy(kwargs)
            tmp["method"] = method
            debug(YELLOW, "send request:", tmp)

        url = f"https://api.telegram.org/bot{self.key}/{method}"
        code, response = await async_req(url, kwargs)

        if method != "getUpdates" and DEBUG:
            tmp = deepcopy(response)
            tmp["code"] = code
            debug(GREEN, "get response:", tmp)

        return response

    async def get_updates(self) -> dict:
        params = {"timeout": 60, "allowed_updates": self.allowed_updates}
        if self.last_updated_id != 0:
            params["offset"] = self.last_updated_id + 1
        return await self.req("getUpdates", **params)

    async def start_polling(self):
        while True:
            updates = await self.get_updates()
            for update in updates.get("result", []):
                if update["update_id"] > self.last_updated_id:
                    await self.handle_update(MiniGramUpdate(update))
                    self.last_updated_id = update["update_id"]
                else:
                    print(
                        f"{RED}{now()} - skip update with update_id <= self.last_updated_id {RESET}"
                    )
            await asyncio.sleep(0.1)

    async def handle_update(self, update: MiniGramUpdate):
        pass

    async def send_text(
        self, chat_id: int, text: str, parse_mode: str = "HTML", **kwargs
    ) -> dict:
        return await self.req(
            "sendMessage", chat_id=chat_id, text=text, parse_mode=parse_mode, **kwargs
        )

    async def reply(self, update: MiniGramUpdate, text: str = "") -> dict:
        params = {
            "chat_id": update.chat_id,
            "reply_to_message_id": update.message_id,
            "text": text,
        }
        return await self.req("sendMessage", **params)

    async def send_chat_action(self, chat_id, action, **kwargs):
        if isinstance(chat_id, MiniGramUpdate):
            chat_id = chat_id.chat_id
        return await self.req(
            "sendChatAction", chat_id=chat_id, action=action, **kwargs
        )

    async def set_message_reaction(
        self, update: MiniGramUpdate, reaction: str = "", is_big=False
    ):
        params = {
            "chat_id": update.chat_id,
            "message_id": update.message_id,
            "reaction": [{"type": "emoji", "emoji": reaction}],
            "is_big": is_big,
        }
        return await self.req("setMessageReaction", **params)

    async def set_webhook(self, url: str) -> dict:
        return await self.req("setWebhook", url=url)

    async def delete_webhook(self) -> dict:
        return await self.req("deleteWebhook")

    async def get_webhook_info(self) -> dict:
        return await self.req("getWebhookInfo")

    async def async_handler(self, data: dict) -> None:
        await self.handle_update(MiniGramUpdate(data))


class MiniGram(BaseMiniGram):
    def __init__(self, key: str):
        global CURRENT_SYNC
        super().__init__(key)
        CURRENT_SYNC = self

    def shutdown(self):
        self.delete_webhook()

    @classmethod
    def current(cls) -> "MiniGram":
        global CURRENT_SYNC
        if CURRENT_SYNC is None:
            raise ValueError("No current MiniGram")
        return CURRENT_SYNC

    def req(self, method: str, **kwargs) -> dict:
        if method != "getUpdates" and DEBUG:
            tmp = deepcopy(kwargs)
            tmp["method"] = method
            debug(YELLOW, "send request:", tmp)

        url = f"https://api.telegram.org/bot{self.key}/{method}"
        code, response = sync_req(url, kwargs)

        if method != "getUpdates" and DEBUG:
            tmp = deepcopy(response)
            tmp["code"] = code
            debug(GREEN, "get response:", tmp)

        return response

    def get_updates(self) -> dict:
        params = {"timeout": 60, "allowed_updates": self.allowed_updates}
        if self.last_updated_id != 0:
            params["offset"] = self.last_updated_id + 1
        return self.req("getUpdates", **params)

    def start_polling(self):
        while True:
            updates = self.get_updates()
            for update in updates.get("result", []):
                if update["update_id"] > self.last_updated_id:
                    self.handle_update(MiniGramUpdate(update))
                    self.last_updated_id = update["update_id"]
                else:
                    print(
                        f"{RED}{now()} - skip update with update_id <= self.last_updated_id {RESET}"
                    )
            time.sleep(0.01)

    def handle_update(self, update: MiniGramUpdate):
        pass

    def send_text(
        self, chat_id: int, text: str, parse_mode: str = "HTML", **kwargs
    ) -> dict:
        return self.req(
            "sendMessage", chat_id=chat_id, text=text, parse_mode=parse_mode, **kwargs
        )

    def reply(self, update: MiniGramUpdate, text: str = "") -> dict:
        params = {
            "chat_id": update.chat_id,
            "reply_to_message_id": update.message_id,
            "text": text,
        }
        return self.req("sendMessage", **params)

    def send_chat_action(self, chat_id: Any, action, **kwargs):
        if isinstance(chat_id, MiniGramUpdate):
            chat_id = chat_id.chat_id
        return self.req("sendChatAction", chat_id=chat_id, action=action, **kwargs)

    def set_message_reaction(
        self, update: MiniGramUpdate, reaction: str = "", is_big=False
    ):
        params = {
            "chat_id": update.chat_id,
            "message_id": update.message_id,
            "reaction": [{"type": "emoji", "emoji": reaction}],
            "is_big": is_big,
        }
        return self.req("setMessageReaction", **params)

    def set_webhook(self, url: str) -> dict:
        return self.req("setWebhook", url=url)

    def delete_webhook(self) -> dict:
        return self.req("deleteWebhook")

    def get_webhook_info(self) -> dict:
        return self.req("getWebhookInfo")

    def sync_handler(self, data: dict) -> None:
        self.handle_update(MiniGramUpdate(data))


CURRENT_ASYNC: AsyncMiniGram | None = None
CURRENT_SYNC: MiniGram | None = None
