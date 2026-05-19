# ai_client.py
# Подключение к Groq API с retry и fallback моделями

import os
import asyncio
import logging
from openai import AsyncOpenAI
from prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Клиент Groq (быстрый бесплатный сервис на Llama)
client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Основная модель + fallback'и (если первая упадёт — пробуем следующую)
MODELS = [
    os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "gemma2-9b-it",
]


async def ask_ai(user_message: str, history: list = None) -> str:
    """
    Отправляет запрос с retry и fallback моделями.
    Возвращает ответ или человеческое сообщение об ошибке.
    """
    if history is None:
        history = []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    last_error = None

    # Перебираем модели — если одна не работает, пробуем следующую
    for model in MODELS:
        for attempt in range(3):  # 3 попытки на каждую модель
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.8,
                    max_tokens=2000,
                    timeout=60,
                )
                logger.info(f"✅ Ответ получен от модели: {model}")
                return response.choices[0].message.content

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                logger.warning(f"⚠️ Попытка {attempt+1}/{3} с моделью {model}: {e}")

                # Если лимит — ждём и пробуем снова
                if "429" in error_str or "rate" in error_str:
                    wait_time = 5 * (attempt + 1)
                    logger.info(f"⏳ Лимит. Жду {wait_time} сек...")
                    await asyncio.sleep(wait_time)
                    continue

                # Если модель не найдена — сразу переходим к следующей
                if "404" in error_str or "not found" in error_str or "decommissioned" in error_str:
                    logger.warning(f"❌ Модель {model} недоступна, пробую следующую")
                    break

                # Другая ошибка — пробуем ещё раз
                await asyncio.sleep(2)

    # Если ВСЕ модели и попытки провалились
    logger.error(f"❌ Все модели недоступны. Последняя ошибка: {last_error}")
    return (
        "слушай, у меня сейчас затык с подключением к нейросети — "
        "видимо лимиты бесплатного плана кончились) "
        "попробуй написать через 5-10 минут, должно отпустить"
    )
