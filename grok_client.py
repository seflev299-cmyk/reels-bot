# grok_client.py
# Подключение к Grog API (xAI) через OpenAI-совместимый клиент

import os
from openai import AsyncOpenAI
from prompts import SYSTEM_PROMPT

# Инициализация клиента Grog
client = AsyncOpenAI(
    api_key=os.getenv("GROG_API_KEY"),
    base_url="https://api.x.ai/v1"
)

MODEL = os.getenv("GROG_MODEL", "grog-2-latest")


async def ask_grog(user_message: str, history: list = None) -> str:
    """
    Отправляет запрос в Grog и возвращает ответ.
    
    user_message — текущее сообщение пользователя
    history — список предыдущих сообщений [{"role": "user/assistant", "content": "..."}]
    """
    if history is None:
        history = []
    
    # Собираем сообщения: системный промпт + история + новое сообщение
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"❌ Ошибка Grog API: {e}")
        return "ой, что-то я завис) попробуй ещё раз через пару секунд"
