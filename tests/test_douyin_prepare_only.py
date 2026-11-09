import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from uploader.douyin_uploader import main as douyin_main
from uploader.douyin_uploader.main import DouYinVideo


class DouyinPrepareOnlyTests(unittest.TestCase):
    def run_upload(self, prepare_only):
        video = DouYinVideo(
            "标题", "/tmp/demo.mp4", [], 0, "/tmp/cookie.json",
            prepare_only=prepare_only,
        )
        for method in (
            "validate_upload_args", "fill_title_and_description",
            "apply_self_declaration", "apply_collection", "set_thumbnail",
            "_wait_for_manual_close",
        ):
            setattr(video, method, AsyncMock())

        locator = MagicMock()
        locator.first = locator
        locator.locator.return_value = locator
        locator.set_input_files = AsyncMock()
        locator.wait_for = AsyncMock()
        locator.is_visible = AsyncMock(return_value=False)
        locator.count = AsyncMock(return_value=1)
        locator.click = AsyncMock()
        page = MagicMock()
        for method in ("goto", "wait_for_url", "wait_for_timeout", "evaluate"):
            setattr(page, method, AsyncMock())
        page.eval_on_selector = AsyncMock(return_value="semi-switch-checked")
        page.locator.return_value = locator
        page.get_by_role.return_value = locator
        context = MagicMock()
        context.new_page = AsyncMock(return_value=page)
        context.storage_state = AsyncMock()
        context.close = AsyncMock()
        browser = MagicMock()
        browser.is_connected.return_value = True
        browser.new_context = AsyncMock(return_value=context)
        browser.close = AsyncMock()
        playwright = MagicMock()
        playwright.chromium.launch = AsyncMock(return_value=browser)
        with (
            patch.object(douyin_main, "set_init_script", AsyncMock(return_value=context)),
            patch.object(douyin_main.asyncio, "sleep", AsyncMock()),
        ):
            asyncio.run(video.upload(playwright))
        return video, page, browser, playwright

    def test_manual_close_never_falls_through_to_publish(self):
        video, page, browser, playwright = self.run_upload(prepare_only=True)
        video._wait_for_manual_close.assert_awaited_once()
        page.get_by_role.assert_not_called()
        page.evaluate.assert_not_awaited()
        self.assertFalse(playwright.chromium.launch.call_args.kwargs["headless"])
        browser.close.assert_awaited_once()

    def test_ordinary_upload_still_publishes(self):
        video, page, _, _ = self.run_upload(prepare_only=False)
        video._wait_for_manual_close.assert_not_awaited()
        page.get_by_role.assert_called_once_with("button", name="发布", exact=True)
        page.get_by_role.return_value.click.assert_awaited_once_with(force=True)


if __name__ == "__main__":
    unittest.main()
