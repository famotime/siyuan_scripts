import asyncio
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import urls_to_siyuan
from utilities.api_client import SiyuanAPI
from utilities.markdown_importer import MarkdownImporter
from utilities.url_to_markdown import URLToMarkdownConverter


class _DummyResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            response = requests.Response()
            response.status_code = self.status_code
            raise requests.exceptions.HTTPError(response=response)

    def json(self):
        return self._payload


def test_siyuan_api_retries_without_auth_header_after_auth_failure(monkeypatch):
    calls = []
    responses = [
        _DummyResponse(401),
        _DummyResponse(200, {"code": 0, "data": {"notebooks": []}}),
    ]

    def fake_post(url, headers, json, timeout):
        calls.append({"url": url, "headers": dict(headers), "json": json, "timeout": timeout})
        return responses[len(calls) - 1]

    monkeypatch.setattr("utilities.api_client.requests.post", fake_post)

    client = SiyuanAPI(api_url="http://127.0.0.1:6806", api_token="expired-token")

    assert client.call_api("/api/notebook/lsNotebooks") == {"notebooks": []}
    assert len(calls) == 2
    assert "Authorization" in calls[0]["headers"]
    assert "Authorization" not in calls[1]["headers"]


def test_step2_import_to_siyuan_returns_false_when_import_reports_errors(monkeypatch):
    monkeypatch.setattr(
        urls_to_siyuan.create_notes_from_md,
        "main",
        lambda *args, **kwargs: {"success": 0, "error": 1, "total": 1},
    )

    assert urls_to_siyuan.step2_import_to_siyuan("ignored") is False


def test_resolve_siyuan_api_url_prefers_non_test_workspace(monkeypatch):
    monkeypatch.setattr(
        urls_to_siyuan,
        "get_kernel_process_command_lines",
        lambda: [
            'SiYuan-Kernel.exe --workspace "D:\\notes\\siyuan-plugin-test" --port 6806',
            'SiYuan-Kernel.exe --workspace "D:\\notes\\siyuan-main" --port 13901',
        ],
    )
    monkeypatch.setattr(
        urls_to_siyuan,
        "fetch_siyuan_instance_info",
        lambda api_url, api_token="", timeout=2.0: {
            "http://127.0.0.1:6806": {
                "ok": True,
                "workspace": "D:\\notes\\siyuan-plugin-test",
            },
            "http://127.0.0.1:13901": {
                "ok": True,
                "workspace": "D:\\notes\\siyuan-main",
            },
        }[api_url],
    )

    resolved_api_url = urls_to_siyuan.resolve_siyuan_api_url(
        configured_api_url="http://127.0.0.1:6806",
        api_token="token",
    )

    assert resolved_api_url == "http://127.0.0.1:13901"


def test_resolve_siyuan_api_url_rejects_test_only_workspaces(monkeypatch):
    monkeypatch.setattr(
        urls_to_siyuan,
        "get_kernel_process_command_lines",
        lambda: ['SiYuan-Kernel.exe --workspace "D:\\notes\\siyuan-plugin-test" --port 6806'],
    )
    monkeypatch.setattr(
        urls_to_siyuan,
        "fetch_siyuan_instance_info",
        lambda api_url, api_token="", timeout=2.0: {
            "ok": True,
            "workspace": "D:\\notes\\siyuan-plugin-test",
        },
    )

    with pytest.raises(RuntimeError, match="test"):
        urls_to_siyuan.resolve_siyuan_api_url(
            configured_api_url="http://127.0.0.1:6806",
            api_token="token",
        )


def test_resolve_siyuan_api_url_skips_connection_reset_candidate(monkeypatch):
    monkeypatch.setattr(
        urls_to_siyuan,
        "get_kernel_process_command_lines",
        lambda: [
            'SiYuan-Kernel.exe --workspace "D:\\notes\\broken" --port 6806',
            'SiYuan-Kernel.exe --workspace "D:\\notes\\siyuan-main" --port 13901',
        ],
    )

    def fake_fetch(api_url, api_token="", timeout=2.0):
        if api_url == "http://127.0.0.1:6806":
            raise ConnectionResetError(10054, "远程主机强迫关闭了一个现有的连接")
        return {
            "ok": True,
            "workspace": "D:\\notes\\siyuan-main",
        }

    monkeypatch.setattr(urls_to_siyuan, "fetch_siyuan_instance_info", fake_fetch)

    resolved_api_url = urls_to_siyuan.resolve_siyuan_api_url(
        configured_api_url="http://127.0.0.1:6806",
        api_token="token",
    )

    assert resolved_api_url == "http://127.0.0.1:13901"


def test_step2_import_to_siyuan_uses_resolved_api_url(monkeypatch):
    calls = []

    monkeypatch.setattr(
        urls_to_siyuan,
        "resolve_siyuan_api_url",
        lambda configured_api_url="", api_token="", **kwargs: "http://127.0.0.1:13901",
    )
    monkeypatch.setattr(
        urls_to_siyuan.create_notes_from_md,
        "main",
        lambda *args, **kwargs: calls.append({"args": args, "kwargs": kwargs}) or {
            "success": 1,
            "error": 0,
            "total": 1,
        },
    )
    monkeypatch.delenv("SIYUAN_API_URL", raising=False)
    monkeypatch.setenv("SIYUAN_API_TOKEN", "token")

    assert urls_to_siyuan.step2_import_to_siyuan("D:\\tmp\\md") is True
    assert calls == [
        {
            "args": ("D:\\tmp\\md",),
            "kwargs": {
                "api_url": "http://127.0.0.1:13901",
                "api_token": "token",
            },
        }
    ]


def test_url_to_markdown_script_runs_without_relative_import_error():
    script_path = PROJECT_ROOT / "utilities" / "url_to_markdown.py"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_convert_url_items_uses_title_as_filename_fallback(tmp_path, monkeypatch):
    converter = URLToMarkdownConverter(output_dir=str(tmp_path))
    seen = []

    async def fake_convert(url, output_filename=None, download_media=True):
        seen.append((url, output_filename, download_media))
        output_path = tmp_path / output_filename
        output_path.write_text("# ok", encoding="utf-8")
        return output_path

    monkeypatch.setattr(converter, "convert_url_to_markdown", fake_convert)

    results = asyncio.run(
        converter.convert_url_items(
            [{"url": "https://example.com/post", "title": 'Title / With : Invalid'}],
            download_media=False,
        )
    )

    assert len(results) == 1
    assert seen == [
        (
            "https://example.com/post",
            "Title ／ With ： Invalid.md",
            False,
        )
    ]


def test_process_markdown_media_handles_adjacent_images_without_greedy_match(tmp_path):
    md_file = tmp_path / "article.md"
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    (media_dir / "a.png").write_bytes(b"a")
    (media_dir / "b.png").write_bytes(b"b")

    importer = MarkdownImporter(api_client=object())
    importer.media_manager = SimpleNamespace(
        is_media_file=lambda path: True,
        upload_asset=lambda path: f"assets/{Path(path).name}",
        get_media_type=lambda path: "image",
    )

    content = "![](media/a.png)![](media/b.png)"

    processed = importer.process_markdown_media(content, md_file)

    assert processed == "![](assets/a.png)![](assets/b.png)"
