import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

import agent


class AgentSafetyTests(unittest.TestCase):
    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            with self.assertRaises(ValueError):
                agent.safe_workspace_path(root, "../outside.txt", allow_missing=True)

    def test_rejects_sensitive_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / ".env").write_text("SECRET=x", encoding="utf-8")
            with self.assertRaises(ValueError):
                agent.safe_workspace_path(root, ".env")

    def test_rejects_env_variants(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / ".env.development").write_text("SECRET=x", encoding="utf-8")
            with self.assertRaises(ValueError):
                agent.safe_workspace_path(root, ".env.development")

    def test_rejects_symlink_outside_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            outside = Path(temp) / "outside.txt"
            outside.write_text("data", encoding="utf-8")
            (root / "link.txt").symlink_to(outside)
            with self.assertRaises(ValueError):
                agent.safe_workspace_path(root.resolve(), "link.txt")

    def test_allows_directory_for_run_cwd(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "src").mkdir()
            self.assertEqual(agent.safe_workspace_path(root, "src", allow_directory=True), root / "src")

    def test_parses_json_fenced_in_markdown(self):
        self.assertEqual(agent.parse_model_json('```json\n{"files": []}\n```'), {"files": []})

    def test_rejects_invalid_json_shape(self):
        with self.assertRaises(ValueError):
            agent.parse_model_json('{"answer": "no files"}')

    def test_blocks_destructive_run_command(self):
        args = type("Args", (), {"command": ["--", "rm", "-rf", "."], "cwd": None})()
        with patch.object(agent.sys.stdin, "isatty", return_value=True):
            with self.assertRaises(ValueError):
                agent.command_run(args)

    def test_rejects_changes_to_unselected_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "main.py").write_text("print('old')\n", encoding="utf-8")
            response = '{"files": [{"path": "main.py", "content": "print(\\\"new\\\")\\n"}]}'
            with patch.object(agent, "get_ai_response", return_value=response):
                with self.assertRaises(ValueError):
                    agent.generate_file_changes(root, "change file", {})

    def test_accepts_run_options_before_command_separator(self):
        args = agent.build_parser().parse_args(["run", "--cwd", "tests", "--notify", "--", "python", "-m", "unittest"])
        self.assertEqual(args.cwd, "tests")
        self.assertTrue(args.notify)
        self.assertEqual(args.command, ["--", "python", "-m", "unittest"])

    def test_notification_uses_argument_list_without_shell(self):
        with patch.object(agent.shutil, "which", return_value="/usr/bin/termux-notification"):
            with patch.object(agent.subprocess, "run") as run:
                agent.send_notification(True, "title", "answer")
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["/usr/bin/termux-notification", "--title", "title", "--content", "answer"])
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_code_discards_changes_without_confirmation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "main.py").write_text("print(1)\n", encoding="utf-8")
            args = agent.build_parser().parse_args(["code", "change it", "--file", "main.py"])
            response = '{"files": [{"path": "main.py", "content": "print(2)\\n"}]}'
            with patch.object(agent, "workspace_root", return_value=root):
                with patch.object(agent, "get_ai_response", return_value=response):
                    with patch.object(agent.sys.stdin, "isatty", return_value=True):
                        with patch("builtins.input", return_value="n"):
                            self.assertEqual(agent.command_code(args), 0)
            self.assertEqual((root / "main.py").read_text(encoding="utf-8"), "print(1)\n")

    def test_code_applies_changes_after_confirmation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / "main.py").write_text("print(1)\n", encoding="utf-8")
            args = agent.build_parser().parse_args(["code", "change it", "--file", "main.py"])
            response = '{"files": [{"path": "main.py", "content": "print(2)\\n"}]}'
            with patch.object(agent, "workspace_root", return_value=root):
                with patch.object(agent, "get_ai_response", return_value=response):
                    with patch.object(agent.sys.stdin, "isatty", return_value=True):
                        with patch("builtins.input", return_value="y"):
                            self.assertEqual(agent.command_code(args), 0)
            self.assertEqual((root / "main.py").read_text(encoding="utf-8"), "print(2)\n")

    def test_wizard_exits_from_menu(self):
        args = agent.build_parser().parse_args(["wizard"])
        with patch.object(agent.sys.stdin, "isatty", return_value=True):
            with patch("builtins.input", return_value="0"):
                self.assertEqual(agent.command_wizard(args), 0)

    def test_wizard_guides_code_task_into_review_flow(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            args = agent.build_parser().parse_args(["wizard"])
            answers = ["2", "Crear una API REST", "Python y Flask", "Incluye una prueba", "0"]
            with patch.object(agent.sys.stdin, "isatty", return_value=True):
                with patch.object(agent, "workspace_root", return_value=root):
                    with patch.object(agent, "command_code", return_value=0) as code:
                        with patch("builtins.input", side_effect=answers):
                            self.assertEqual(agent.command_wizard(args), 0)
            task = code.call_args.args[0].task
            self.assertIn("Objetivo: Crear una API REST", task)
            self.assertIn("Tecnologías preferidas: Python y Flask", task)
            self.assertIn("Criterios de aceptación: Incluye una prueba", task)

    def test_paint_respects_no_color(self):
        with patch.object(agent.sys.stdout, "isatty", return_value=True):
            with patch.dict(agent.os.environ, {"NO_COLOR": "1"}):
                self.assertEqual(agent.paint("text", "green"), "text")

    def test_empty_cli_defaults_to_wizard(self):
        with patch.object(agent, "command_wizard", return_value=0) as wizard:
            self.assertEqual(agent.main([]), 0)
        wizard.assert_called_once()

    def test_configure_openai_prompts_masked_and_saves_private_file(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            answers = iter(["1", "", "gpt-test", ""])
            with patch("builtins.print") as printed:
                with patch.object(agent, "list_available_models", return_value=[]):
                    result = agent.configure_provider(
                        config_path,
                        input_fn=lambda _prompt: next(answers),
                        secret_fn=lambda _prompt: "sk-test-private",
                    )
            self.assertEqual(result["provider"], "openai")
            saved = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["api_key"], "sk-test-private")
            self.assertEqual(saved["model"], "gpt-test")
            self.assertEqual(config_path.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("sk-test-private", " ".join(str(call) for call in printed.call_args_list))

    def test_configure_ollama_requests_server_and_model(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            answers = iter(["2", "http://192.168.1.5:11434/v1", "qwen2.5-coder:7b", ""])
            with patch.object(agent, "list_available_models", return_value=[]):
                result = agent.configure_provider(config_path, input_fn=lambda _prompt: next(answers))
            self.assertEqual(result["provider"], "ollama")
            self.assertEqual(result["base_url"], "http://192.168.1.5:11434/v1")
            self.assertEqual(result["model"], "qwen2.5-coder:7b")
            self.assertEqual(result["api_key"], "ollama")

    def test_ollama_configuration_rejects_invalid_url_scheme(self):
        with tempfile.TemporaryDirectory() as temp:
            answers = iter(["2", "192.168.1.5:11434", "qwen"])
            with self.assertRaises(ValueError):
                agent.configure_provider(Path(temp) / "config.json", input_fn=lambda _prompt: next(answers))

    def test_legacy_placeholder_key_is_not_accepted_as_real_credential(self):
        with patch.object(agent, "load_saved_config", return_value={}):
            with patch.dict(agent.os.environ, {"OPENAI_API_KEY": "TU_CLAVE_API_DE_OPENAI"}, clear=True):
                settings = agent.provider_settings()
        self.assertNotIn("api_key", settings)

    def test_missing_credentials_prompt_for_provider_on_first_interactive_request(self):
        with patch.object(agent, "load_saved_config", return_value={}):
            with patch.object(agent, "saved_config_path", return_value=Path("/tmp/config.json")):
                with patch.dict(agent.os.environ, {}, clear=True):
                    with patch.object(agent.sys.stdin, "isatty", return_value=True):
                        with patch.object(agent, "configure_provider", return_value={"provider": "ollama", "api_key": "ollama"}) as configure:
                            settings = agent.provider_settings(prompt_if_missing=True)
        configure.assert_called_once_with()
        self.assertEqual(settings["provider"], "ollama")

    def test_missing_credentials_prompt_ignores_existing_environment_keys(self):
        with patch.object(agent, "load_saved_config", return_value={}):
            with patch.dict(agent.os.environ, {}, clear=True):
                with patch.object(agent.sys.stdin, "isatty", return_value=True):
                    with patch.object(agent, "configure_provider", return_value={"provider": "ollama", "api_key": "ollama"}) as configure:
                        settings = agent.provider_settings(prompt_if_missing=True)
        configure.assert_called_once_with()
        self.assertEqual(settings["provider"], "ollama")

    def test_chat_and_code_use_different_configured_models(self):
        response = {"choices": [{"message": {"content": "ok"}}]}
        with patch.object(agent, "get_api_config", return_value={"api_key": "secret", "base_url": "https://api.test/v1", "model": "chat-model", "code_model": "code-model"}):
            with patch.object(agent, "request_api_json", return_value=response) as request:
                agent.get_ai_response([{"role": "user", "content": "hello"}], purpose="chat")
                agent.get_ai_response([{"role": "user", "content": "code"}], purpose="code")
        self.assertEqual([call.args[3]["model"] for call in request.call_args_list], ["chat-model", "code-model"])

    def test_model_discovery_reads_openai_compatible_catalog(self):
        with patch.object(agent, "request_api_json", return_value={"data": [{"id": "model-b"}, {"id": "model-a"}, {"object": "permission"}]}) as request:
            models = agent.list_available_models("token", "http://localhost:11434/v1")
        self.assertEqual(models, ["model-a", "model-b"])
        self.assertEqual(request.call_args.args[2], "/models")

    def test_http_request_uses_openai_compatible_chat_endpoint(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"ok": true}'

        payload = {"model": "test-model", "messages": [{"role": "user", "content": "hello"}]}
        with patch.object(agent.urllib.request, "urlopen", return_value=FakeResponse()) as urlopen:
            result = agent.request_api_json("secret-value", "https://api.test/v1", "/chat/completions", payload)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.test/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-value")
        self.assertEqual(json.loads(request.data.decode("utf-8")), payload)
        self.assertEqual(result, {"ok": True})

    def test_configure_selects_models_discovered_from_endpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            answers = iter(["2", "http://ollama:11434/v1", "1", "2"])
            with patch.object(agent, "list_available_models", return_value=["qwen-chat", "qwen-coder"]):
                result = agent.configure_provider(Path(temp) / "config.json", input_fn=lambda _prompt: next(answers))
        self.assertEqual(result["model"], "qwen-chat")
        self.assertEqual(result["code_model"], "qwen-coder")

    def test_model_route_uses_code_model_for_code_requests_or_files(self):
        self.assertEqual(agent.infer_model_route("¿Qué es una variable?"), "chat")
        self.assertEqual(agent.infer_model_route("Ayúdame a depurar este bug"), "code")
        self.assertEqual(agent.infer_model_route("Revisa esto", ["src/main.py"]), "code")


if __name__ == "__main__":
    unittest.main()
