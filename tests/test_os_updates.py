
import pytest

from d3s.nagios_plugins.check_os_updates import CheckOsUpdates

@pytest.fixture
def mp(mock_plugin):
    return mock_plugin

def patch_for_fedora(mock, fedora_version, kernel_version, update_info):
    mock.patch_file('/etc/os-release',
f"""
NAME="Fedora Linux"
VERSION="{fedora_version} (Server Edition)"
RELEASE_TYPE=stable
ID=fedora
VERSION_ID={fedora_version}
VERSION_CODENAME=""
""")
    mock.patch_process('uname -r', kernel_version)
    mock.patch_process('env LC_ALL=C dnf updateinfo list --quiet', update_info.strip('\n'))
    mock.patch_eol('fedora', fedora_version, fedora_version >= 42, 43)


def test_fedora_without_updates(mp):
    patch_for_fedora(mp, 43, '7.0.0-test.fc43.x86_64',  "")
    mp.run(CheckOsUpdates())
    assert mp.get_stdout() == "OS-UPDATES OK - Fedora 43, 0 out-dated packages|os_id=fedora,os_is_maintained=true,os_kernel=7.0.0-test.fc43.x86_64,os_latest_version=43,os_outdated_packages=0,os_security_updates=0,os_version=43"

def test_fedora_with_few_updates(mp):
    patch_for_fedora(mp, 43, '7.0.0-test.fc43.x86_64',
"""
Name                   Type        Severity                                                 Package              Issued
FEDORA-2026-0000000000 bugfix      None                                   alpha-1.2.3-2.fc43.x86_64 2026-01-01 00:00:00
FEDORA-2026-0000000001 bugfix      None                                   bravo-1.2.3-2.fc43.x86_64 2026-01-02 00:00:00
FEDORA-2026-0000000002 security    Low                                  charlie-1.2.3-2.fc43.x86_64 2026-01-03 00:00:00
""")
    mp.run(CheckOsUpdates())
    assert mp.get_stdout() == "OS-UPDATES OK - Fedora 43, 1 security updates, 3 out-dated packages|os_id=fedora,os_is_maintained=true,os_kernel=7.0.0-test.fc43.x86_64,os_latest_version=43,os_outdated_packages=3,os_security_updates=1,os_version=43"

def test_fedora_outdated(mp):
    patch_for_fedora(mp, 42, '7.0.0-test.fc42.x86_64',
"""
Name                   Type        Severity                                                 Package              Issued
FEDORA-2024-0000000000 bugfix      None                                   alpha-1.2.3-2.fc42.x86_64 2024-01-01 00:00:00
FEDORA-2024-0000000001 security    High                                   bravo-1.2.3-2.fc42.x86_64 2024-01-02 00:00:00
FEDORA-2024-0000000002 security    Low                                  charlie-1.2.3-2.fc42.x86_64 2024-01-03 00:00:00
""")
    mp.run(CheckOsUpdates())
    assert mp.get_stdout() == "OS-UPDATES WARNING - Fedora 42 (43 available), 2 security updates, 3 out-dated packages|os_id=fedora,os_is_maintained=true,os_kernel=7.0.0-test.fc42.x86_64,os_latest_version=43,os_outdated_packages=3,os_security_updates=2,os_version=42"

def test_fedora_unmaintained(mp):
    patch_for_fedora(mp, 38, '6.0.0-test.fc38.x86_64',
"""
FEDORA-2024-0000000000 Moderate/Sec. alpha-1.2.3-2.fc38.x86_64
FEDORA-2024-0000000001 Unknown/Sec.  bravo-1.2.3-2.fc38.x86_64
""")
    mp.run(CheckOsUpdates())
    assert mp.get_stdout() == "OS-UPDATES CRITICAL - Fedora 38 is past its EOL (43 available), 2 security updates, 2 out-dated packages|os_id=fedora,os_is_maintained=false,os_kernel=6.0.0-test.fc38.x86_64,os_latest_version=43,os_outdated_packages=2,os_security_updates=2,os_version=38"

