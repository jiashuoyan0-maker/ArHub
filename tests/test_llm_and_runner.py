from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services import llm_client
from backend.services.claude_runner import ClaudeRunner


class LlmClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_chat_completion_builds_provider_neutral_request(self) -> None:
        seen: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["authorization"] = request.headers.get("authorization")
            seen["custom"] = request.headers.get("x-arhub-test")
            seen["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"role": "assistant", "content": "OK"}}
                    ]
                },
            )

        settings = {
            "executor_base_url": "https://open.bigmodel.cn/api/paas/v4",
            "executor_api_key": "unit-test-key",
            "executor_model_id": "glm-test",
            "executor_extra_headers": '{"X-ArHub-Test":"yes"}',
        }
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            with patch.object(
                llm_client, "get_all_settings", AsyncMock(return_value=settings)
            ):
                payload = await llm_client.chat_completion(
                    "executor",
                    [{"role": "user", "content": "ping"}],
                    tools=[
                        {
                            "type": "function",
                            "function": {"name": "read_file", "parameters": {}},
                        }
                    ],
                    client=client,
                )
        finally:
            await client.aclose()

        self.assertEqual(
            seen["url"],
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        )
        self.assertEqual(seen["authorization"], "Bearer unit-test-key")
        self.assertEqual(seen["custom"], "yes")
        self.assertEqual(seen["body"]["model"], "glm-test")
        self.assertEqual(seen["body"]["tool_choice"], "auto")
        self.assertEqual(
            llm_client.message_text(payload["choices"][0]["message"]), "OK"
        )

    async def test_missing_endpoint_has_clear_error(self) -> None:
        with patch.object(
            llm_client, "get_all_settings", AsyncMock(return_value={})
        ):
            with self.assertRaisesRegex(RuntimeError, "Base URL is not configured"):
                await llm_client.get_agent_config("executor")

    async def test_chat_completion_streams_text_and_reassembles_tool_calls(self) -> None:
        seen: dict[str, object] = {}
        events = [
            {"choices": [{"index": 0, "delta": {"role": "assistant"}}]},
            {"choices": [{"index": 0, "delta": {"content": "Hel"}}]},
            {
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": [{"type": "text", "text": "lo"}]},
                    }
                ]
            },
            {
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "write_",
                                        "arguments": '{"path":"RESULT',
                                    },
                                }
                            ]
                        },
                    }
                ]
            },
            {
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "function": {
                                        "name": "file",
                                        "arguments": '.md"}',
                                    },
                                }
                            ]
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {"total_tokens": 12},
            },
        ]
        stream = "".join(
            f"data: {json.dumps(event, ensure_ascii=False)}\n\n" for event in events
        ) + "data: [DONE]\n\n"

        def handler(request: httpx.Request) -> httpx.Response:
            seen["body"] = json.loads(request.content)
            seen["accept"] = request.headers.get("accept")
            return httpx.Response(
                200,
                headers={"Content-Type": "text/event-stream"},
                content=stream.encode("utf-8"),
            )

        settings = {
            "executor_base_url": "https://api.deepseek.com/v1",
            "executor_api_key": "unit-test-key",
            "executor_model_id": "deepseek-chat",
        }
        deltas: list[str] = []
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            with patch.object(
                llm_client, "get_all_settings", AsyncMock(return_value=settings)
            ):
                payload = await llm_client.chat_completion(
                    "executor",
                    [{"role": "user", "content": "create RESULT.md"}],
                    tools=[
                        {
                            "type": "function",
                            "function": {"name": "write_file", "parameters": {}},
                        }
                    ],
                    client=client,
                    on_delta=deltas.append,
                )
        finally:
            await client.aclose()

        self.assertTrue(seen["body"]["stream"])
        self.assertEqual(seen["accept"], "text/event-stream")
        self.assertEqual(deltas, ["Hel", "lo"])
        choice = payload["choices"][0]
        self.assertEqual(choice["finish_reason"], "tool_calls")
        self.assertEqual(choice["message"]["content"], "Hello")
        tool_call = choice["message"]["tool_calls"][0]
        self.assertEqual(tool_call["id"], "call-1")
        self.assertEqual(tool_call["function"]["name"], "write_file")
        self.assertEqual(tool_call["function"]["arguments"], '{"path":"RESULT.md"}')
        self.assertEqual(payload["usage"], {"total_tokens": 12})


class RunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_loop_writes_file_and_returns_changed_files(self) -> None:
        runner = ClaudeRunner()
        replies = [
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "write_file",
                                        "arguments": json.dumps(
                                            {
                                                "path": "RESULT.md",
                                                "content": "# Result\ncomplete\n",
                                            }
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Completed RESULT.md",
                        }
                    }
                ]
            },
        ]
        fake_chat = AsyncMock(side_effect=replies)
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "backend.services.claude_runner.chat_completion", fake_chat
            ), patch.object(
                runner, "_load_skill", return_value="Write RESULT.md and verify it."
            ):
                result = await runner.run_skill(
                    "test-skill", "Create the result", directory, "wf-test"
                )

            output = Path(directory, "RESULT.md").read_text(encoding="utf-8")
            self.assertEqual(output, "# Result\ncomplete\n")
            self.assertTrue(result["success"])
            self.assertEqual(result["output_files"], ["RESULT.md"])
            self.assertEqual(result["rounds"], 2)
            second_messages = fake_chat.await_args_list[1].args[1]
            self.assertEqual(second_messages[-1]["role"], "tool")
            self.assertEqual(second_messages[-1]["tool_call_id"], "call-1")

    async def test_file_tools_reject_workspace_escape(self) -> None:
        runner = ClaudeRunner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.assertRaises(PermissionError):
                runner._safe_path(root, "../outside.txt")


if __name__ == "__main__":
    unittest.main()
