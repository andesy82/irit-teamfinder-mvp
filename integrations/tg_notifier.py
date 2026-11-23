import os
import asyncio
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")


async def send_new_user_notification(name: str, role: str, skills: list[str], tg_username: str) -> bool:
    """
    Отправляет уведомление в Telegram о новой анкете на платформе IRIT TeamFinder.
    """
    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        print(f"[MOCK TG] Новая анкета: {name} ({role}) | Стек: {', '.join(skills)}")
        return True

    url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
    skills_str = ", ".join(skills)
    text = (
        f"🚀 <b>Новый участник в IRIT TeamFinder!</b>\n\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"🛠 <b>Роль:</b> {role}\n"
        f"💻 <b>Стек:</b> {skills_str}\n"
        f"📱 <b>Telegram:</b> @{tg_username.lstrip('@')}"
    )

    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.status_code == 200


dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Это бот уведомлений <b>IRIT TeamFinder</b>.\n"
        f"Твой Chat ID: <code>{message.chat.id}</code>",
        parse_mode="HTML"
    )


async def run_bot():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(send_new_user_notification("Морковка", "Bot Developer", ["Python", "aiogram"], "@morkovka_dev"))
