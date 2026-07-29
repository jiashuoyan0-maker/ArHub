import unittest

from backend.provider_urls import chat_completions_url, models_url


class ProviderUrlTests(unittest.TestCase):
    def test_chat_endpoint_variants(self):
        cases = {
            "https://api.deepseek.com": "https://api.deepseek.com/v1/chat/completions",
            "https://api.deepseek.com/v1/": "https://api.deepseek.com/v1/chat/completions",
            "https://open.bigmodel.cn/api/paas/v4": (
                "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            ),
            "https://example.test/api/v1": "https://example.test/api/v1/chat/completions",
            "https://example.test/custom/chat/completions": (
                "https://example.test/custom/chat/completions"
            ),
            "http://127.0.0.1:8080/openai": (
                "http://127.0.0.1:8080/openai/v1/chat/completions"
            ),
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(chat_completions_url(source), expected)

    def test_models_endpoint_follows_chat_endpoint(self):
        self.assertEqual(
            models_url("https://open.bigmodel.cn/api/paas/v4"),
            "https://open.bigmodel.cn/api/paas/v4/models",
        )

    def test_invalid_urls_are_rejected(self):
        cases = (
            "",
            "api.example.test",
            "ftp://api.example.test",
            "https://api.example.test?v=1",
        )
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    chat_completions_url(source)


if __name__ == "__main__":
    unittest.main()
