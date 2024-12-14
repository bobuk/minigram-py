# MiniGram 🤖📬

MiniGram is an ultraminimalistic Python library for building Telegram bots that's perfect for use in restricted environments like AWS Lambdas. Say goodbye to bloated libraries and hello to MiniGram's sleek and efficient design! 🚀✨

## Features 🌟

-   Lightweight and minimalistic 🍃
-   Works in both synchronous and asynchronous modes ⚡️
-   Seamless integration with popular web libraries like Starlette/FastAPI and aiohttp 🌐
-   Easy to use and understand API 😊
-   Perfect for deploying bots in restricted environments like AWS Lambdas 🔒

## Installation 📦

To start building your super cool Telegram bot with MiniGram, simply install it using pip:

```
pip install minigram-py
```

## Usage 🚀

Using MiniGram is as easy as 1-2-3! Here are a few examples to get you started:

### Basic Example

```python
from minigram import MiniGram

YOUR_BOT_TOKEN = "0:0"
CHAT_ID = 0


class MyAwesomeBot(MiniGram):
    def handle_update(self, update):
        match update.update_type:
            case "message":
                match update.text:
                    case "/sync" | "/async":
                        self.reply(update, "I'm a bot, for sure! ⚙️")
                    case _:
                        self.send_text(
                            update.from_id,
                            f"I don't understand that command. 😕\n"
                            f"But your id = {update.from_id}",
                        )

            case "message_reaction":
                self.reply(update, "I see you like this message!")

            case "edited_message":
                self.set_message_reaction(update, "👀")


bot = MyAwesomeBot(YOUR_BOT_TOKEN)
bot.send_text(CHAT_ID, "Hello from an bot! 🚀")
bot.start_polling()

```

In just a few lines of code, you've created a bot that responds to the "/start" command. How cool is that? 😎

### Starlette Integration

```python
from starlette.applications import Starlette
from starlette.routing import Route
from minigram import StarletteMiniGram

YOUR_BOT_TOKEN = "0:0"

class MyStarletteBot(StarletteMiniGram):
    async def incoming(self, msg):
        if msg.text == "/hello":
            return msg.reply("Hello from Starlette! 👋")

bot = MyStarletteBot(YOUR_BOT_TOKEN)
bot.set_webhook("https://yourwebsite.com/webhook")

app = Starlette(debug=True, routes=[
    Route("/webhook", bot.starlette_handler, methods=["POST"]),
])
```

This example shows how seamlessly MiniGram integrates with Starlette, allowing you to create a webhook endpoint for your bot in no time! 🌐

### FastAPI Integration

```python
from fastapi import FastAPI, Request
from minigram import FastAPIMiniGram
from fastapi.responses import JSONResponse

class MyFastAPIBot(FastAPIMiniGram):
    async def incoming(self, msg):
        if msg.text == "/hello":
            return await msg.reply("Hello from FastAPI! 👋")

bot = MyFastAPIBot("YOUR_BOT_TOKEN")
bot.set_webhook("https://yourwebsite.com/webhook")

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    return await bot.fastapi_handler(request)
```

MiniGram supports both asynchronous and synchronous methods for FastAPI, giving you the flexibility to choose the best approach for your application. Whether you prefer async or sync, MiniGram has got you covered! 🌐



### Asynchronous Mode

```python
import asyncio
from minigram import AsyncMiniGram

YOUR_BOT_TOKEN = "0:0"
CHAT_ID = 0

class MyAsyncBot(AsyncMiniGram):
    async def handle_update(self, update):
        match update.update_type:
            case "message":
                match update.text:
                    case "/sync" | "/async":
                        await self.reply(update, "I'm a asynchronous bot, for sure! ⚙️")
                    case _:
                        await self.send_text(
                            update.from_id,
                            f"I don't understand that command. 😕\n"
                            f"But your id = {update.from_id}",
                        )

            case "message_reaction":
                await self.reply(update, "I see you like this message!")

            case "edited_message":
                await self.set_message_reaction(update, "👀")


async def main():
    bot = MyAsyncBot(YOUR_BOT_TOKEN)
    await bot.send_text(CHAT_ID, "Hello from an asynchronous bot! 🚀")
    await bot.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
```

MiniGram works just as well in asynchronous mode, making it easy to integrate with your existing async application. 🎛️

## Contributing 🤝

We love contributions! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request on our [GitHub repository](https://github.com/bobuk/minigram-py). Let's make MiniGram even better together! 💪

## License 📄

MiniGram is released under the [MIT License](https://opensource.org/licenses/MIT), so feel free to use it in your projects, whether they're open-source or commercial. 😄

---

Now go forth and build some amazing bots with MiniGram! 🎈🤖
