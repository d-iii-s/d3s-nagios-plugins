
import pytest

class MockPlugin:
    def __init__(self, capturer, patcher):
        self.capturer = capturer
        self.patcher = patcher
        self.patched_files = {}
        self.patched_processes = {}
        self.captured = None

    def mock_read_file(self, filename):
        assert filename in self.patched_files.keys()
        for line in self.patched_files[filename].split('\n'):
            yield line.rstrip()

    def mock_read_command_output(self, cmdline):
        cmdline = ' '.join(cmdline)
        assert cmdline in self.patched_processes.keys()
        for line in self.patched_processes[cmdline].split('\n'):
            yield line.rstrip()


    def patch_file(self, filename, contents):
        self.patched_files[filename] = contents

    def patch_process(self, cmdline, output):
        self.patched_processes[cmdline] = output

    def get_stdout(self):
        return self.captured.out.rstrip()

    def run(self, plugin):
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
        plugin.run()
        self.captured = self.capturer.readouterr()


@pytest.fixture
def mock_plugin(capsys, monkeypatch):
    return MockPlugin(capsys, monkeypatch)

