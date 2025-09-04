import os
import unittest
from click.testing import CliRunner
from droidbuilder.main import cli

class TestInitCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_init_command(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['init'], input='''
MyTestApp
1.0
main.py
android
org.test
debug
arm64-v8a

9123335
py2jib
34
21
24
25.2.9519653
11
interactive
openssl,sdl2
''')
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(os.path.exists('droidbuilder.toml'))

            # Verify system_packages are in droidbuilder.toml
            with open('droidbuilder.toml', 'r') as f:
                content = f.read()
                self.assertIn('system_packages = [ "openssl", "sdl2",]', content)

if __name__ == '__main__':
    unittest.main()