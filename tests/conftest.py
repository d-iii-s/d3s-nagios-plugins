
import sys

import pytest

class MockPlugin:
    def __init__(self, capturer, patcher):
        self.capturer = capturer
        self.patcher = patcher
        self.patched_files = {}
        self.patched_processes = {}
        self.patched_eols = {}
        self.captured = None

    def patch_file(self, filename, contents):
        self.patched_files[filename] = contents

    def mock_read_file(self, filename):
        assert filename in self.patched_files.keys()
        for line in self.patched_files[filename].split('\n'):
            yield line.rstrip()

    def patch_process(self, cmdline, output):
        self.patched_processes[cmdline] = output

    def mock_read_command_output(self, cmdline):
        cmdline = ' '.join(cmdline)
        assert cmdline in self.patched_processes.keys()
        for line in self.patched_processes[cmdline].split('\n'):
            yield line.rstrip()

    def get_stdout(self):
        return self.captured.out.rstrip()

    def patch_eol(self, product, release, is_maintained, latest):
        self.patched_eols[f'{product}--{release}'] = {
            'product': product,
            'release': str(release),
            'latest': str(latest),
            'is_maintained': is_maintained,
        }

    def mock_get_endoflife_info(self, product, release):
        key = f'{product}--{release}'
        assert key in self.patched_eols.keys()
        return self.patched_eols[key]


    def run(self, plugin, *args):
        self.patcher.setattr(
            plugin,
            'read_file',
            lambda x: self.mock_read_file(x)
        )
        self.patcher.setattr(
            plugin,
            'read_command_output',
            lambda x: self.mock_read_command_output(x)
        )
        self.patcher.setattr(
            plugin,
            'get_endoflife_info',
            lambda p, v: self.mock_get_endoflife_info(p, v)
        )
        self.patcher.setattr(
            sys,
            'argv',
            [str(plugin.__class__)] + list(args),
        )
        plugin.run()
        self.captured = self.capturer.readouterr()


@pytest.fixture
def mock_plugin(capsys, monkeypatch):
    return MockPlugin(capsys, monkeypatch)

