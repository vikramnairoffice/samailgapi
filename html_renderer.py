import asyncio
import atexit
import inspect
from concurrent.futures import Future
from io import BytesIO
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
from typing import Any, Callable, Optional

from PIL import Image


class PlaywrightUnavailable(RuntimeError):
    pass



_SEED_INIT_SCRIPT = """
    (function(seed){
        if (typeof seed !== 'number') { return; }
        function mulberry32(a) {
            return function() {
                var t = a += 0x6D2B79F5;
                t = Math.imul(t ^ (t >>> 15), t | 1);
                t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
                return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
            };
        }
        var generator = mulberry32((seed >>> 0) | 0);
        if (generator) {
            Math.random = function() { return generator(); };
        }
        try {
            if (typeof window !== 'undefined') {
                window.__MAILER_SEED__ = seed;
            }
        } catch (err) { /* ignore */ }
    })({seed});
"""


class PlaywrightHTMLRenderer:
    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._jobs = Queue()
        self._thread: Optional[Thread] = None
        self._thread_lock = Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        atexit.register(self.close)

    def _ensure_thread(self) -> None:
        with self._thread_lock:
            if self._thread and self._thread.is_alive():
                return
            self._thread = Thread(target=self._worker, name="PlaywrightHTMLRenderer", daemon=True)
            self._thread.start()

    def _worker(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            while True:
                job = self._jobs.get()
                if job is None:
                    break
                func, args, kwargs, future = job
                try:
                    result = func(*args, **kwargs)
                    if inspect.isawaitable(result):
                        result = loop.run_until_complete(result)
                except Exception as exc:  # pragma: no cover - defensive
                    future.set_exception(exc)
                else:
                    future.set_result(result)
        finally:
            try:
                if self._browser is not None or self._playwright is not None:
                    loop.run_until_complete(self._async_shutdown())
            finally:
                self._loop = None
                loop.close()

    def _submit(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        self._ensure_thread()
        future: Future = Future()
        self._jobs.put((func, args, kwargs, future))
        return future.result()

    def close(self) -> None:
        thread: Optional[Thread]
        with self._thread_lock:
            thread = self._thread if self._thread and self._thread.is_alive() else None
        if thread:
            future: Future = Future()
            self._jobs.put((self._shutdown, (), {}, future))
            future.result()
            self._jobs.put(None)
            thread.join(timeout=5)
        else:
            if self._browser is not None or self._playwright is not None:
                def _run_shutdown() -> None:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._async_shutdown())
                    finally:
                        loop.close()

                temp_thread = Thread(target=_run_shutdown, name="PlaywrightHTMLRendererShutdown", daemon=True)
                temp_thread.start()
                temp_thread.join(timeout=5)
        with self._thread_lock:
            self._thread = None

    async def _async_shutdown(self) -> None:
        if self._browser is not None:
            try:
                await self._browser.close()
            finally:
                self._browser = None
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            finally:
                self._playwright = None

    def _shutdown(self) -> Any:
        return self._async_shutdown()

    async def _ensure_browser(self) -> None:
        if self._browser is not None:
            return
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise PlaywrightUnavailable(
                "Playwright is required. Install with `pip install playwright` and run `playwright install chromium`."
            ) from exc
        manager = async_playwright()
        playwright = await manager.start()
        launch_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
        browser = await playwright.chromium.launch(headless=True, args=launch_args)
        self._playwright = playwright
        self._browser = browser

    async def _new_page(self, seed: Optional[int] = None):
        await self._ensure_browser()
        context = await self._browser.new_context(ignore_https_errors=True)
        if seed is not None:
            try:
                await context.add_init_script(_SEED_INIT_SCRIPT.format(seed=int(seed) & 0xFFFFFFFF))
            except Exception:
                pass
        page = await context.new_page()
        return context, page

    def render_pdf(self, html: str, destination: Path, *, format: str = "Letter") -> None:
        self._submit(self._render_pdf, html, destination, format=format)

    async def _render_pdf(self, html: str, destination: Path, *, format: str = "Letter") -> None:
        context, page = await self._new_page()
        try:
            await page.set_content(html, wait_until="networkidle")
            destination.parent.mkdir(parents=True, exist_ok=True)
            await page.pdf(
                path=str(destination),
                format=format,
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            await page.close()
            await context.close()

    def render_image(self, html: str, *, viewport_width: int = 1200) -> Image.Image:
        return self._submit(self._render_image, html, viewport_width=viewport_width)

    async def _render_image(self, html: str, *, viewport_width: int = 1200) -> Image.Image:
        context, page = await self._new_page()
        try:
            await page.set_viewport_size({"width": viewport_width, "height": 720})
            await page.set_content(html, wait_until="networkidle")
            data = await page.screenshot(full_page=True, type="png")
        finally:
            await page.close()
            await context.close()
        return Image.open(BytesIO(data)).convert('RGBA')

    def render_html_snapshot(self, html: str, *, wait_ms: int = 120, seed: Optional[int] = None) -> str:
        return self._submit(self._render_html_snapshot, html, wait_ms=wait_ms, seed=seed)

    async def _render_html_snapshot(self, html: str, *, wait_ms: int = 120, seed: Optional[int] = None) -> str:
        context, page = await self._new_page(seed=seed)
        try:
            await page.set_content(html, wait_until="networkidle")
            if wait_ms and wait_ms > 0:
                await page.wait_for_timeout(wait_ms)
            await page.evaluate("document.querySelectorAll('script').forEach(function(node){node.remove();});")
            return await page.content()
        finally:
            await page.close()
            await context.close()


html_renderer = PlaywrightHTMLRenderer()
