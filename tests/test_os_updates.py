
import pytest

from d3s.nagios_plugins.check_os_updates import CheckOsUpdates

@pytest.fixture
def mp(mock_plugin):
    return mock_plugin

def patch_for_fedora(mock, fedora_version, kernel_version, upgradable_packages):
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
    if upgradable_packages:
        updates = "\n".join(
            ["Available upgrades"] +
            [
                '{:45} {:30} updates'.format(
                    f'{pkg}.x86_64',
                    f'1.2.3-1.fc{fedora_version}'
                )
                for pkg in upgradable_packages
            ]
        )
    else:
        updates = ""
    mock.patch_process('dnf list --quiet --upgrades', updates)
    mock.patch_eol('fedora', fedora_version, fedora_version >= 42, 43)


def test_fedora_without_updates(mp):
    patch_for_fedora(mp, 43, '7.0.0-test.fc43.x86_64',  [])
    mp.run(CheckOsUpdates())
    assert mp.get_stdout() == "OS-UPDATES OK - Fedora 43, 0 out-dated packages|os_id=fedora,os_is_maintained=true,os_kernel=7.0.0-test.fc43.x86_64,os_latest_version=43,os_outdated_packages=0,os_version=43"

def test_fedora_with_few_updates(mp):
    patch_for_fedora(mp, 43, '7.0.0-test.fc43.x86_64',
        ['alpha', 'bravo', 'charlie'])
    mp.run(CheckOsUpdates())
    assert mp.get_stdout() == "OS-UPDATES OK - Fedora 43, 3 out-dated packages|os_id=fedora,os_is_maintained=true,os_kernel=7.0.0-test.fc43.x86_64,os_latest_version=43,os_outdated_packages=3,os_version=43"

def test_fedora_outdated(mp):
    patch_for_fedora(mp, 42, '7.0.0-test.fc42.x86_64',
        ['alpha', 'bravo', 'charlie'])
    mp.run(CheckOsUpdates())
    assert mp.get_stdout() == "OS-UPDATES WARNING - Fedora 42 (43 available), 3 out-dated packages|os_id=fedora,os_is_maintained=true,os_kernel=7.0.0-test.fc42.x86_64,os_latest_version=43,os_outdated_packages=3,os_version=42"

def test_fedora_unmaintained(mp):
    patch_for_fedora(mp, 40, '7.0.0-test.fc40.x86_64',
        ['alpha', 'bravo'])
    mp.run(CheckOsUpdates())
    assert mp.get_stdout() == "OS-UPDATES CRITICAL - Fedora 40 is past its EOL (43 available), 2 out-dated packages|os_id=fedora,os_is_maintained=false,os_kernel=7.0.0-test.fc40.x86_64,os_latest_version=43,os_outdated_packages=2,os_version=40"

