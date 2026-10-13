import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
