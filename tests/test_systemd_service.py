
import pytest

from d3s.nagios_plugins.check_systemd_service import CheckSystemdService

@pytest.fixture
def mp(mock_plugin):
    return mock_plugin

def test_smoke(mp):
    mp.patch_process('systemctl is-enabled sshd', 'enabled')
    mp.patch_process('systemctl is-active sshd', 'active')
    mp.patch_process('systemctl status sshd',
"""* sshd.service - OpenSSH Daemon
     Loaded: loaded (/usr/lib/systemd/system/sshd.service; enabled; preset: disabled)
     Active: active (running) since Mon 2025-01-01 00:30:00 CEST; 1 week 2 days ago
 Invocation: 12340000000000000000000000000000
       Docs: man:sshd(8)
             man:sshd_config(5)
   Main PID: 987 (sshd)
      Tasks: 1 (limit: 38237)
     Memory: 888K (peak: 15.8M, swap: 912K, swap peak: 912K, zswap: 9.4K)
        CPU: 345ms
     CGroup: /system.slice/sshd.service
             `-987 "sshd: /usr/bin/sshd -D [listener] 0 of 10-100 startups"

Jan 01 01:00:00 machine.example.com sshd-session[12100]: Accepted publickey for guest from 127.0.0.1 port 58341 ssh2: RSA SHA256:blahblahblah
Jan 01 01:01:01 machine.example.com sshd-session[12100]: pam_unix(sshd:session): session opened for user guest(uid=1000) by guest(uid=0)
 """)
    mp.run(CheckSystemdService(), '--service=sshd')
    assert mp.get_stdout() == "SRV OK - sshd running, 888K, 1 tasks|service_memory=888K,service_name=sshd,service_tasks=1"

