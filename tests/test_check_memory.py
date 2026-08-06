
import pytest

from d3s.nagios_plugins.check_memory import CheckMemory

@pytest.fixture
def mp(mock_plugin):
    mock_plugin.patch_file(
        '/proc/meminfo', """"
MemTotal:       32775876 kB
MemFree:        12481024 kB
MemAvailable:   19941800 kB
Buffers:              12 kB
Cached:          5997860 kB
SwapCached:       327724 kB
Active:          9639528 kB
    """)
    mock_plugin.patch_process(
        'ps -e --no-header --sort=-%mem -o rss,%mem,comm,time,command',
        """
699324  4.2 alpha 00:02:16 /usr/bin/alpha --zulu
217136  1.3 bravo       00:07:41 /usr/sbin/bravo --xray --yankee
199548  1.2 charlie 00:00:20 /bin/charlie
160780  0.9 delta        00:02:05 /usr/libexec/delta/delta --whiskey
159988  0.9 echo 00:00:18 /usr/bin/echo -u -V
126084  0.7 foxtrot 00:01:20 /bin/foxtrot -sierra -tango
98768  0.6 golf        00:00:25 /usr/bin/golf -Q -R
        """)
    return mock_plugin

def test_smoke(mp):
    mp.run(CheckMemory())
    assert mp.get_stdout() == "MEM OK - 31GB, 19GB available (61%)|mem_total_kb=32775876kB,mem_avail_kb=19941800kB,mem_avail_percent=60.84291995734912,top_1_app=alpha:699324:4.2:00_02_16:--zulu,top_2_app=bravo:217136:1.3:00_07_41:--yankee,top_3_app=charlie:199548:1.2:00_00_20:/bin/charlie,top_4_app=delta:160780:0.9:00_02_05:--whiskey,top_5_app=echo:159988:0.9:00_00_18:-V"

