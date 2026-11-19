import json
import os
import time

import pytest

from d3s import status_dat_to_json as conv

NOW = 1_700_000_000

STATUS_DAT = """\
########################################
#          NAGIOS STATUS FILE
########################################

info {
\tcreated=1699999990
\tversion=4.4.6
\t}

hoststatus {
\thost_name=alpha
\tcurrent_state=0
\thas_been_checked=1
\tplugin_output=PING OK
\tlast_state_change=1699996400
\t}

hoststatus {
\thost_name=beta
\tcurrent_state=1
\thas_been_checked=1
\tplugin_output=PING CRITICAL
\tlast_state_change=1699999940
\tproblem_has_been_acknowledged=1
\t}

servicestatus {
\thost_name=alpha
\tservice_description=Load
\tcurrent_state=0
\thas_been_checked=1
\tplugin_output=LOAD OK
\tlong_plugin_output=line one\\nline two
\tperformance_data=load1=0.5;4;8;0 'load 5'=0.25;3;6
\tlast_state_change=1699900000
\t}

servicestatus {
\thost_name=alpha
\tservice_description=Disk
\tcurrent_state=1
\thas_been_checked=1
\tstate_type=0
\tcurrent_attempt=2
\tmax_attempts=3
\tplugin_output=DISK WARNING
\tperformance_data=/=95%;80;90;0;100
\tlast_state_change=1699999000
\t}

servicestatus {
\thost_name=alpha
\tservice_description=Backup
\tcurrent_state=0
\thas_been_checked=0
\tplugin_output=
\t}

servicestatus {
\thost_name=ghost
\tservice_description=Orphan
\tcurrent_state=1
\thas_been_checked=1
\tplugin_output=WARN
\tscheduled_downtime_depth=1
\tis_flapping=1
\t}
"""


def make_blocks():
    return conv.parse_status_text(STATUS_DAT)


def test_parse_blocks():
    blocks = make_blocks()
    assert [b[0] for b in blocks] == [
        "info", "hoststatus", "hoststatus",
        "servicestatus", "servicestatus", "servicestatus", "servicestatus",
    ]
    assert blocks[1][1]["host_name"] == "alpha"
    assert blocks[3][1]["performance_data"] == "load1=0.5;4;8;0 'load 5'=0.25;3;6"


def host_names(output):
    return [h["name"] for h in output["hosts"]]


def service_names(output, host):
    (h,) = [h for h in output["hosts"] if h["name"] == host]
    return [s["name"] for s in h["services"]]


def test_full_conversion_worst_first():
    output = conv.convert(make_blocks(), NOW, 125, sort=conv.sort_worst_first)
    # The "generated" value depends on the local time zone.
    generated = output.pop("generated")
    assert generated == time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(NOW))

    expected = {
        "status_age": "2m",
        "summary": {
            "hosts": {"UP": 1, "DOWN": 1, "UNKNOWN": 1},
            "services": {"OK": 1, "WARNING": 2, "PENDING": 1},
        },
        "hosts": [
            {
                "name": "beta",
                "state": "DOWN",
                "since": 1699999940,
                "for": "1m",
                "flags": ["acknowledged"],
                "output": "PING CRITICAL",
                "long_output": [],
                "perfdata": [],
                "perfdata_raw": "",
                "services": [],
                "worst_severity": 0,
            },
            {
                "name": "alpha",
                "state": "UP",
                "since": 1699996400,
                "for": "1h 0m",
                "flags": [],
                "output": "PING OK",
                "long_output": [],
                "perfdata": [],
                "perfdata_raw": "",
                "worst_severity": 2,
                "services": [
                    {
                        "name": "Disk",
                        "state": "WARNING",
                        "since": 1699999000,
                        "for": "16m",
                        "flags": ["soft 2/3"],
                        "output": "DISK WARNING",
                        "long_output": [],
                        "perfdata": [
                            {"label": "/", "value": 95, "unit": "%",
                             "warn": "80", "crit": "90", "min": 0, "max": 100},
                        ],
                        "perfdata_raw": "/=95%;80;90;0;100",
                    },
                    {
                        "name": "Backup",
                        "state": "PENDING",
                        "since": 0,
                        "for": "",
                        "flags": [],
                        "output": "",
                        "long_output": [],
                        "perfdata": [],
                        "perfdata_raw": "",
                    },
                    {
                        "name": "Load",
                        "state": "OK",
                        "since": 1699900000,
                        "for": "1d 3h",
                        "flags": [],
                        "output": "LOAD OK",
                        "long_output": ["line one", "line two"],
                        "perfdata": [
                            {"label": "load1", "value": 0.5, "unit": "",
                             "warn": "4", "crit": "8", "min": 0, "max": None},
                            {"label": "load 5", "value": 0.25, "unit": "",
                             "warn": "3", "crit": "6", "min": None, "max": None},
                        ],
                        "perfdata_raw": "load1=0.5;4;8;0 'load 5'=0.25;3;6",
                    },
                ],
            },
            {
                "name": "ghost",
                "state": "UNKNOWN",
                "since": 0,
                "for": "",
                "flags": [],
                "output": "",
                "long_output": [],
                "perfdata": [],
                "perfdata_raw": "",
                "worst_severity": 2,
                "services": [
                    {
                        "name": "Orphan",
                        "state": "WARNING",
                        "since": 0,
                        "for": "",
                        "flags": ["downtime", "flapping"],
                        "output": "WARN",
                        "long_output": [],
                        "perfdata": [],
                        "perfdata_raw": "",
                    },
                ],
            },
        ],
    }
    assert output == expected
    # The result must be JSON serializable.
    assert json.loads(json.dumps(output)) == expected


def test_default_keeps_file_order():
    output = conv.convert(make_blocks(), NOW, 0)
    assert output == conv.convert(make_blocks(), NOW, 0, sort=conv.keep_order)
    # Hosts: all hoststatus blocks first (file order), then stub hosts.
    assert host_names(output) == ["alpha", "beta", "ghost"]
    assert service_names(output, "alpha") == ["Load", "Disk", "Backup"]
    assert output["hosts"][0]["worst_severity"] == 2


def test_sort_by_name():
    output = conv.convert(make_blocks(), NOW, 0, sort=conv.sort_by_name)
    assert host_names(output) == ["alpha", "beta", "ghost"]
    assert service_names(output, "alpha") == ["Backup", "Disk", "Load"]


def test_sort_by_name_is_independent_of_file_order():
    reversed_blocks = list(reversed(make_blocks()))
    unsorted = conv.convert(reversed_blocks, NOW, 0)
    assert host_names(unsorted) != sorted(host_names(unsorted))
    output = conv.convert(reversed_blocks, NOW, 0, sort=conv.sort_by_name)
    assert host_names(output) == ["alpha", "beta", "ghost"]


def test_worst_first_orders_problems_first():
    output = conv.convert(make_blocks(), NOW, 0, sort=conv.sort_worst_first)
    assert host_names(output) == ["beta", "alpha", "ghost"]
    assert service_names(output, "alpha") == ["Disk", "Backup", "Load"]


def test_custom_sort_function_is_used():
    output = conv.convert(make_blocks(), NOW, 0, sort=lambda hosts: hosts[::-1])
    assert host_names(output) == ["ghost", "beta", "alpha"]


def test_all_orders_have_same_content():
    by_name = lambda items: sorted(items, key=lambda i: i["name"])
    results = [
        conv.convert(make_blocks(), NOW, 0, sort=mode)
        for mode in (conv.keep_order, conv.sort_by_name, conv.sort_worst_first)
    ]
    for other in results[1:]:
        assert other["summary"] == results[0]["summary"]
        assert len(other["hosts"]) == len(results[0]["hosts"])
        for host, expected in zip(by_name(other["hosts"]), by_name(results[0]["hosts"])):
            assert by_name(host["services"]) == by_name(expected["services"])
            assert {k: v for k, v in host.items() if k != "services"} == \
                {k: v for k, v in expected.items() if k != "services"}


@pytest.mark.parametrize("text, expected", [
    ("", []),
    ("time=0.05s;1;2;0", [
        {"label": "time", "value": 0.05, "unit": "s", "warn": "1", "crit": "2",
         "min": 0, "max": None}]),
    ("'it''s'=3", [
        {"label": "it's", "value": 3, "unit": "", "warn": "", "crit": "",
         "min": None, "max": None}]),
    ("x=U", [
        {"label": "x", "value": None, "unit": "", "warn": "", "crit": "",
         "min": None, "max": None}]),
    ("t=1;10:20;~:5", [
        {"label": "t", "value": 1, "unit": "", "warn": "10:20", "crit": "~:5",
         "min": None, "max": None}]),
])
def test_parse_perfdata(text, expected):
    assert conv.parse_perfdata(text) == expected


@pytest.mark.parametrize("seconds, expected", [
    (-5, "0s"), (59, "59s"), (120, "2m"), (3700, "1h 1m"), (90000, "1d 1h"),
])
def test_format_duration(seconds, expected):
    assert conv.format_duration(seconds) == expected


@pytest.mark.parametrize("switches, expected", [
    ([], ["alpha", "beta", "ghost"]),
    (["--sort"], ["alpha", "beta", "ghost"]),
    (["--worst-first"], ["beta", "alpha", "ghost"]),
])
def test_main_reads_file_and_honours_switches(tmp_path, capsys, switches, expected):
    path = tmp_path / "status.dat"
    path.write_text(STATUS_DAT)
    assert conv.main(switches + [str(path)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert [h["name"] for h in output["hosts"]] == expected


def test_parse_args_defaults():
    args = conv.parse_args([])
    assert args.status_file == conv.DEFAULT_STATUS_FILE
    assert args.sort is conv.keep_order


@pytest.mark.parametrize("switch, mode", [
    ("--sort", conv.sort_by_name),
    ("--worst-first", conv.sort_worst_first),
])
def test_parse_args_sort_switches(switch, mode):
    args = conv.parse_args([switch, "/some/status.dat"])
    assert args.status_file == "/some/status.dat"
    assert args.sort == mode


@pytest.mark.parametrize("argv", [
    ["--bogus"],
    ["--no-sort"],
    ["--sort", "--worst-first"],
])
def test_parse_args_rejects_invalid_usage(argv, capsys):
    with pytest.raises(SystemExit) as excinfo:
        conv.parse_args(argv)
    assert excinfo.value.code == 2


def test_main_output_has_sorted_keys_and_four_space_indent(tmp_path, capsys):
    path = tmp_path / "status.dat"
    path.write_text(STATUS_DAT)
    assert conv.main([str(path)]) == 0
    text = capsys.readouterr().out
    assert text.endswith("}\n")
    assert text.startswith('{\n    "generated": ')
    parsed = json.loads(text)
    assert list(parsed) == sorted(parsed)
    assert text == json.dumps(parsed, indent=4, sort_keys=True) + "\n"
    host = parsed["hosts"][0]
    assert list(host) == sorted(host)
