#!/usr/bin/env python3
"""TikZ 图视觉自检 — 调 vision LLM 检查 TikZ 编译结果是否有重叠/截断等问题。

用法:
  python _utils/tikz_vision_check.py <image.png>

环境变量（按优先级）:
  EDITOR_AI_API_KEY + EDITOR_AI_BASE_URL  (editor_ai 配置)
  OPENAI_API_KEY + OPENAI_BASE_URL        (reviewer 配置)

退出码:
  0 = 通过（PASS）
  1 = 有问题（输出具体问题描述）
  2 = API 不可用（未配置 key 或调用失败）
"""
from __future__ import annotations

import base64
import http.client
import json
import os
import ssl
import sys
from pathlib import Path
from urllib.parse import urlparse

PROMPT = (
    "这是一张学术论文中的 TikZ 流程图/架构图/技术路线图。请严格检查以下问题：\n"
    "1. 文字是否被截断、重叠或超出节点边框？\n"
    "2. 连线上的标注文字是否跟节点重叠或被遮挡？\n"
    "3. 节点间距是否均匀，有没有挤在一起的？\n"
    "4. 有没有大片空白区域（布局不紧凑）？\n"
    "5. 箭头方向是否合理，有没有连线穿过节点？\n"
    "6. 整体是否美观、专业、适合放在学术论文中？\n\n"
    "如果全部没问题，只回答一个词：PASS\n"
    "如果有问题，逐条列出每个问题的具体位置和描述，格式：\n"
    "ISSUE 1: [位置] [问题描述]\n"
    "ISSUE 2: [位置] [问题描述]\n"
)


def _call_vision(api_base: str, api_key: str, model: str,
                 image_b64: str, mime: str, timeout: int = 60) -> str:
    parsed = urlparse(api_base)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        raise ValueError(f"Bad API base URL: {api_base}")

    path = (parsed.path or "").rstrip("/")
    if "/v1/chat/completions" not in path:
        path = path + "/v1/chat/completions"

    payload = json.dumps({
        "model": model or "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {
                    "url": f"data:{mime};base64,{image_b64}"
                }},
            ],
        }],
        "max_tokens": 2000,
        "stream": False,
    })

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Content-Length": str(len(payload)),
    }

    conn = None
    try:
        if parsed.scheme == "https":
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(host, port, timeout=timeout, context=ctx)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)

        conn.request("POST", path, payload, headers)
        res = conn.getresponse()
        data = res.read()

        if res.status != 200:
            raise Exception(f"HTTP {res.status}: {data.decode('utf-8', errors='replace')[:300]}")

        result = json.loads(data.decode("utf-8"))
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        raise Exception("No choices in response")
    finally:
        if conn:
            conn.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python tikz_vision_check.py <image.png>")
        sys.exit(2)

    img_path = Path(sys.argv[1])
    if not img_path.exists():
        print(f"File not found: {img_path}")
        sys.exit(2)

    # 读取图片
    img_data = img_path.read_bytes()
    img_b64 = base64.b64encode(img_data).decode("ascii")
    ext = img_path.suffix.lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext.lstrip("."), "image/png")

    # 按优先级尝试 API 配置
    configs = [
        (os.environ.get("EDITOR_AI_API_KEY", ""),
         os.environ.get("EDITOR_AI_BASE_URL", ""),
         os.environ.get("EDITOR_AI_MODEL_ID", "gpt-4o")),
        (os.environ.get("OPENAI_API_KEY", ""),
         os.environ.get("OPENAI_BASE_URL", ""),
         os.environ.get("REVIEWER_MODEL_ID", "gpt-4o")),
    ]

    for api_key, api_base, model in configs:
        if not api_key or not api_base:
            continue
        try:
            result = _call_vision(api_base, api_key, model, img_b64, mime)
            print(result)
            if "PASS" in result.upper().split("\n")[0]:
                sys.exit(0)
            else:
                sys.exit(1)
        except Exception as e:
            print(f"Vision API error: {e}", file=sys.stderr)
            continue

    print("NO_VISION_API: No vision-capable LLM configured (need EDITOR_AI_API_KEY or OPENAI_API_KEY)")
    sys.exit(2)


if __name__ == "__main__":
    main()
