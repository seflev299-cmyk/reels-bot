# keep_alive.py
# Веб-сервер-обманка, чтобы Render не засыпал (бесплатный план)

from aiohttp import web


async def handle(request):
    return web.Response(text="🤖 Бот Шеф Льва жив и работает!")


async def start_webserver():
    """Запускаем веб-сервер для Render."""
    import os
    port = int(os.getenv("PORT", 10000))
    
    app = web.Application()
    app.router.add_get("/", handle)
    app.router.add_get("/health", handle)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"✅ Веб-сервер запущен на порту {port}")
