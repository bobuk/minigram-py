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

class MyAwesomeBot(MiniGram):
    def incoming(self, msg):
        if msg.text == "/start":
            return msg.reply("Welcome to my awesome bot! 🎉")
        return self.sent_text(msg.chat.id, "I don't understand that command. 😕")

bot = MyAwesomeBot("YOUR_BOT_TOKEN")
bot.start_polling()
```

In just a few lines of code, you've created a bot that responds to the "/start" command. How cool is that? 😎

### Starlette Integration

```python
from starlette.applications import Starlette
from starlette.routing import Route
from minigram import StarletteMiniGram

class MyStarletteBot(StarletteMiniGram):
    async def incoming(self, msg):
        if msg.text == "/hello":
            return msg.reply("Hello from Starlette! 👋")

bot = MyStarletteBot("YOUR_BOT_TOKEN")
bot.set_webhook("https://yourwebsite.com/webhook")

app = Starlette(debug=True, routes=[
    Route("/webhook", bot.starlette_handler, methods=["POST"]),
])
```

This example shows how seamlessly MiniGram integrates with Starlette, allowing you to create a webhook endpoint for your bot in no time! 🌐

### Asynchronous Mode

```python
from minigram import AsyncMiniGram

class MyAsyncBot(AsyncMiniGram):
    async def incoming(self, msg):
        if msg.text == "/sync":
            return msg.reply("I'm a asynchronous bot, for sure! ⚙️")

async def main():
    bot = MyAsyncBot("YOUR_BOT_TOKEN")
    await bot.sent_text(YOUR_CHAT_ID, "Hello from an asynchronous bot! 🚀")
    await bot.start_polling()
```

MiniGram works just as well in asynchronous mode, making it easy to integrate with your existing async application. 🎛️

## Contributing 🤝

We love contributions! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request on our [GitHub repository](https://github.com/bobuk/minigram-py). Let's make MiniGram even better together! 💪

## License 📄

MiniGram is released under the [MIT License](https://opensource.org/licenses/MIT), so feel free to use it in your projects, whether they're open-source or commercial. 😄

---

Now go forth and build some amazing bots with MiniGram! 🎈🤖
