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
from backend.routers import settings as settings_router


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

    async def test_provider_reasoning_options_are_capability_aware(self) -> None:
        glm_settings = {
            "executor_base_url": "https://open.bigmodel.cn/api/paas/v4",
            "executor_model_id": "glm-5",
            "executor_provider": "auto",
            "executor_reasoning_effort": "high",
        }
        with patch.object(
            llm_client, "get_all_settings", AsyncMock(return_value=glm_settings)
        ):
            glm_config = await llm_client.get_agent_config("executor")
        glm_body: dict[str, object] = {}
        llm_client.apply_provider_options(glm_body, glm_config)
        self.assertEqual(glm_config.provider, "glm")
        self.assertEqual(glm_body, {"thinking": {"type": "enabled"}})

        openai_settings = {
            "executor_base_url": "https://api.openai.com/v1",
            "executor_model_id": "gpt-5",
            "executor_reasoning_effort": "max",
            "executor_request_options": '{"parallel_tool_calls":true}',
        }
        with patch.object(
            llm_client, "get_all_settings", AsyncMock(return_value=openai_settings)
        ):
            openai_config = await llm_client.get_agent_config("executor")
        openai_body: dict[str, object] = {}
        llm_client.apply_provider_options(openai_body, openai_config)
        self.assertEqual(
            openai_body,
            {"reasoning_effort": "high", "parallel_tool_calls": True},
        )

        deepseek_settings = {
            "reviewer_base_url": "https://api.deepseek.com/v1",
            "reviewer_model_id": "deepseek-chat",
            "reviewer_provider": "deepseek",
            "reviewer_reasoning_effort": "medium",
        }
        with patch.object(
            llm_client, "get_all_settings", AsyncMock(return_value=deepseek_settings)
        ):
            deepseek_config = await llm_client.get_agent_config("reviewer")
        deepseek_body: dict[str, object] = {}
        deepseek_resolution = llm_client.apply_provider_options(
            deepseek_body, deepseek_config
        )
        self.assertEqual(
            deepseek_body,
            {"thinking": {"type": "enabled"}, "reasoning_effort": "high"},
        )
        self.assertEqual(deepseek_resolution.requested, "medium")
        self.assertEqual(deepseek_resolution.effective, "high")
        self.assertTrue(deepseek_resolution.downgraded)

        generic_config = llm_client.AgentConfig(
            "editor_ai",
            "https://models.example/v1",
            "",
            "custom-model",
            {},
            "generic",
            "high",
            {},
        )
        generic_body: dict[str, object] = {}
        generic_resolution = llm_client.apply_provider_options(
            generic_body, generic_config
        )
        self.assertEqual(generic_body, {})
        self.assertEqual(generic_resolution.effective, "default")
        self.assertTrue(generic_resolution.downgraded)

        reasoner_config = llm_client.AgentConfig(
            "reviewer",
            "https://api.deepseek.com/v1",
            "",
            "deepseek-reasoner",
            {},
            "deepseek",
            "max",
            {},
        )
        reasoner_body: dict[str, object] = {}
        reasoner_resolution = llm_client.apply_provider_options(
            reasoner_body, reasoner_config
        )
        self.assertEqual(reasoner_body["reasoning_effort"], "high")
        self.assertTrue(reasoner_resolution.downgraded)

    async def test_each_role_reasoning_reaches_its_provider_request(self) -> None:
        cases = {
            "executor": (
                {
                    "executor_base_url": "https://api.openai.com/v1",
                    "executor_model_id": "gpt-5",
                    "executor_provider": "openai",
                    "executor_reasoning_effort": "low",
                },
                {"reasoning_effort": "low"},
            ),
            "reviewer": (
                {
                    "reviewer_base_url": "https://api.deepseek.com/v1",
                    "reviewer_model_id": "deepseek-chat",
                    "reviewer_provider": "deepseek",
                    "reviewer_reasoning_effort": "max",
                },
                {"thinking": {"type": "enabled"}, "reasoning_effort": "max"},
            ),
            "editor_ai": (
                {
                    "editor_ai_base_url": "https://open.bigmodel.cn/api/paas/v4",
                    "editor_ai_model_id": "glm-5",
                    "editor_ai_provider": "glm",
                    "editor_ai_reasoning_effort": "off",
                },
                {"thinking": {"type": "disabled"}},
            ),
        }
        for agent, (stored, expected) in cases.items():
            seen: dict[str, object] = {}

            def handler(request: httpx.Request) -> httpx.Response:
                seen.update(json.loads(request.content))
                return httpx.Response(
                    200,
                    json={"choices": [{"message": {"content": "OK"}}]},
                )

            client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
            try:
                with patch.object(
                    llm_client, "get_all_settings", AsyncMock(return_value=stored)
                ):
                    await llm_client.chat_completion(
                        agent, [{"role": "user", "content": "ping"}], client=client
                    )
            finally:
                await client.aclose()
            for key, value in expected.items():
                self.assertEqual(seen[key], value, agent)

    async def test_local_kernel_routes_text_role_with_role_options(self) -> None:
        settings = {
            "agent_runtime": "openai_compatible",
            "reviewer_agent_runtime": "local_claude",
            "reviewer_reasoning_effort": "xhigh",
            "reviewer_claude_model": "claude-sonnet-test",
        }
        with patch.object(
            llm_client, "get_all_settings", AsyncMock(return_value=settings)
        ), patch.object(
            ClaudeRunner, "run_text", AsyncMock(return_value="reviewed")
        ) as local_call, patch.object(
            llm_client, "chat_completion", AsyncMock()
        ) as remote_call:
            result = await llm_client.call_llm("reviewer", "Review this")

        self.assertEqual(result, "reviewed")
        remote_call.assert_not_awaited()
        self.assertEqual(local_call.await_args.args[:3], ("reviewer", "Review this", settings))

        with patch.object(
            llm_client, "get_all_settings", AsyncMock(return_value=settings)
        ), patch.object(
            llm_client, "get_agent_config", AsyncMock()
        ) as config_call:
            with self.assertRaisesRegex(RuntimeError, "CLI Agent kernel"):
                await llm_client.chat_completion(
                    "reviewer", [{"role": "user", "content": "Review this"}]
                )
        config_call.assert_not_awaited()

    def test_request_options_cannot_override_reasoning_resolution(self) -> None:
        with self.assertRaisesRegex(ValueError, "reasoning_effort"):
            llm_client._parse_request_options(
                '{"reasoning_effort":"max"}', "executor"
            )

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
            ), patch(
                "backend.services.claude_runner.get_all_settings",
                AsyncMock(return_value={"agent_runtime": "openai_compatible"}),
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

    async def test_local_claude_runtime_is_selected_from_settings(self) -> None:
        runner = ClaudeRunner()
        local_result = {
            "success": True,
            "output": "done",
            "runtime": "local_claude",
            "output_files": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "backend.services.claude_runner.get_all_settings",
                AsyncMock(
                    return_value={
                        "agent_runtime": "local_claude",
                        "claude_bin": "claude",
                        "claude_effort": "max",
                    }
                ),
            ), patch.object(
                runner, "_load_skill", return_value="Inspect the workspace."
            ), patch.object(
                runner, "_run_local_claude", AsyncMock(return_value=local_result)
            ) as local_run:
                result = await runner.run_skill(
                    "test-skill", "Run locally", directory, "wf-local"
                )

        self.assertEqual(result["runtime"], "local_claude")
        self.assertEqual(local_run.await_args.kwargs["settings"]["claude_effort"], "max")
        self.assertEqual(
            runner._local_claude_options(
                {
                    "executor_reasoning_effort": "default",
                    "claude_effort": "max",
                }
            )["effective_effort"],
            "max",
        )

    async def test_claude_detection_reports_version_and_cli_compatibility(self) -> None:
        fake_path = Path("C:/Tools/claude.exe")
        with patch.object(
            ClaudeRunner,
            "_resolve_claude_candidate",
            side_effect=lambda value: fake_path if value in {"claude", "custom"} else None,
        ), patch.object(
            ClaudeRunner,
            "_claude_probe",
            AsyncMock(
                side_effect=[
                    (0, "2.1.220 (Claude Code)"),
                    (
                        0,
                        "--print --output-format stream-json "
                        "--include-partial-messages --permission-mode "
                        "--allowedTools --model --resume --effort "
                        "low medium high xhigh max",
                    ),
                ]
            ),
        ):
            detected = await ClaudeRunner.detect_local_claude(
                {
                    "claude_bin": "custom",
                    "agent_runtime": "openai_compatible",
                    "executor_agent_runtime": "local_claude",
                }
            )

        self.assertTrue(detected["compatible"])
        self.assertTrue(detected["required"])
        self.assertEqual(detected["recommended"], str(fake_path))
        self.assertEqual(detected["candidates"][0]["version"], "2.1.220")
        self.assertTrue(detected["candidates"][0]["capabilities"]["effort"])
        self.assertEqual(
            detected["selected_by_agent"]["executor"], "local_claude"
        )

    async def test_execution_uses_compatible_fallback_candidate(self) -> None:
        old = Path("C:/Old/claude.exe")
        current = Path("C:/Tools/claude.exe")
        detection = {
            "recommended": str(current),
            "candidates": [
                {"path": str(old), "compatible": False, "issues": ["missing options"]},
                {
                    "path": str(current),
                    "compatible": True,
                    "issues": [],
                    "capabilities": {"effort": True},
                },
            ],
            "message": "Local Claude Code is compatible.",
        }
        with patch.object(
            ClaudeRunner,
            "detect_local_claude",
            AsyncMock(return_value=detection),
        ):
            executable, inspected = await ClaudeRunner._compatible_claude_executable(
                {"claude_bin": str(old)}
            )

        self.assertEqual(executable, current)
        self.assertTrue(inspected["compatible"])

    async def test_settings_capability_api_exposes_kernel_and_downgrade(self) -> None:
        stored = {
            "executor_agent_runtime": "local_claude",
            "executor_reasoning_effort": "off",
        }
        with patch.object(
            settings_router, "get_all_settings", AsyncMock(return_value=stored)
        ):
            status = await settings_router.provider_status()

        executor = status.agents["executor"]
        self.assertEqual(executor.kernel.value, "local_claude")
        self.assertTrue(executor.configured)
        self.assertEqual(executor.reasoning.effective, "default")
        self.assertTrue(executor.reasoning.downgraded)

    async def test_file_tools_reject_workspace_escape(self) -> None:
        runner = ClaudeRunner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.assertRaises(PermissionError):
                runner._safe_path(root, "../outside.txt")


if __name__ == "__main__":
    unittest.main()
