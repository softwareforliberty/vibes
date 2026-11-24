"""bin/setup-needs, on branches that add settings a person must provide.

    python3 -I -m unittest discover -s tests/setup_needs -t tests/setup_needs
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "setup-needs")
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null",
       "GIT_CONFIG_NOSYSTEM": "1"}


class SetupNeedsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.repo)
        self.git("init", "-q", "-b", "main")
        self.write("app.py", 'import os\nURL = os.environ["SHOP_URL"]\n')
        self.write(".env.example", "SHOP_URL=https://shop.example\n")
        self.commit("base")
        self.git("checkout", "-q", "-b", "feature")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.repo, check=True,
                              capture_output=True, text=True, env=ENV).stdout

    def write(self, path: str, text: str) -> None:
        full = os.path.join(self.repo, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as stream:
            stream.write(text)

    def commit(self, message: str) -> None:
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.invalid",
                 "commit", "-q", "-m", message)

    def run_it(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([SCRIPT, *args], cwd=self.repo, text=True,
                              capture_output=True, check=False, env=ENV)

    def test_none_when_nothing_new_is_needed(self) -> None:
        self.write("app.py", 'import os\nURL = os.environ["SHOP_URL"]\n'
                             'print(URL)\n')
        self.commit("tweak")
        result = self.run_it("main")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "None.\n")

    def test_lists_a_new_setting_with_where_it_is(self) -> None:
        self.write("pay.py", 'import os\n\nKEY = os.getenv("STRIPE_KEY")\n')
        self.write(".env.example", "SHOP_URL=https://shop.example\n"
                                   "STRIPE_KEY=\n")
        self.write(".github/workflows/ci.yml",
                   "jobs:\n  t:\n    env:\n"
                   "      STRIPE_KEY: ${{ secrets.STRIPE_KEY }}\n"
                   "      TOKEN: ${{ secrets.GITHUB_TOKEN }}\n"
                   "      REGION: ${{ vars.DEPLOY_REGION }}\n")
        self.commit("pay")
        result = self.run_it("main")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "DEPLOY_REGION: a GitHub variable in .github/workflows/ci.yml:6",
            "STRIPE_KEY: read in pay.py:3; in .env.example:2; a GitHub "
            "secret in .github/workflows/ci.yml:4",
        ])

    def test_finds_reads_in_many_languages(self) -> None:
        reads = {
            "a.js": 'const k = process.env.JS_KEY;\n',
            "b.ts": 'const k = process.env["TS_KEY"];\n',
            "c.go": 'k := os.Getenv("GO_KEY")\n',
            "d.rs": 'let k = std::env::var("RS_KEY");\n',
            "e.rb": 'k = ENV.fetch("RB_KEY")\n',
            "f.java": 'String k = System.getenv("JAVA_KEY");\n',
            "g.cs": 'var k = Environment.GetEnvironmentVariable("CS_KEY");\n',
            "h.php": '$k = getenv(\'PHP_KEY\');\n',
            "i.ex": 'k = System.get_env("EX_KEY")\n',
            "j.py": 'k = os.environ.get("PY_KEY")\n',
        }
        for path, text in reads.items():
            self.write(path, text)
        self.commit("reads")
        names = [line.split(":")[0] for line in
                 self.run_it("main").stdout.splitlines()]
        self.assertEqual(names, sorted(
            ["JS_KEY", "TS_KEY", "GO_KEY", "RS_KEY", "RB_KEY", "JAVA_KEY",
             "CS_KEY", "PHP_KEY", "EX_KEY", "PY_KEY"]))

    def test_leaves_out_what_every_machine_has(self) -> None:
        self.write("x.py", 'import os\nh = os.environ["HOME"]\n'
                           'p = os.getenv("PATH")\nc = os.getenv("CI")\n')
        self.commit("x")
        self.assertEqual(self.run_it("main").stdout, "None.\n")

    def test_refuses_a_bad_base(self) -> None:
        self.assertEqual(self.run_it("no-such-branch").returncode, 2)
        self.assertEqual(self.run_it().returncode, 2)


if __name__ == "__main__":
    unittest.main()
