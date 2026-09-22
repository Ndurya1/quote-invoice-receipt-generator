import unittest
from pathlib import Path


class DeploymentConfigurationTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def test_container_installs_locked_dependencies_and_migrates_before_start(self):
        dockerfile = (self.root / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("uv sync --frozen --no-dev", dockerfile)
        self.assertIn("python -m app.db migrate", dockerfile)
        self.assertIn("uvicorn app.main:app", dockerfile)
        self.assertIn("--proxy-headers", dockerfile)
        self.assertIn("--forwarded-allow-ips=", dockerfile)

    def test_container_context_excludes_local_secrets_and_development_files(self):
        dockerignore = (self.root / ".dockerignore").read_text(encoding="utf-8")
        for entry in (".env", ".venv", "tests/", "docs/"):
            with self.subTest(entry=entry):
                self.assertIn(entry, dockerignore)
