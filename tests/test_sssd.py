
import pytest

from d3s.nagios_plugins.check_sssd import CheckSSSD

@pytest.fixture
def mp(mock_plugin):
    return mock_plugin

def test_unknown_domain(mp):
    mp.patch_process('sssctl domain-status --online alpha', 'Unable to get online status')
    mp.run(CheckSSSD(), '--domain=alpha')
    assert mp.get_stdout() == "SSSD CRITICAL - unable to query domain status (probably wrong domain name)"

def test_online_domain(mp):
    mp.patch_process('sssctl domain-status --online bravo', 'Online status: Online\n')
    mp.run(CheckSSSD(), '--domain=bravo')
    assert mp.get_stdout() == "SSSD OK - domain bravo is online|domain=bravo,status=online"

def test_offline_domain(mp):
    mp.patch_process('sssctl domain-status --online charlie', 'Online status: Offline\n')
    mp.run(CheckSSSD(), '--domain=charlie')
    assert mp.get_stdout() == "SSSD CRITICAL - domain charlie is offline|domain=charlie,status=offline"


