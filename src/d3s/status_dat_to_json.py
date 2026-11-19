#!/usr/bin/env python3

"""
Converts Nagios status.dat to JSON (stdout).

Stdlib only.
"""

import argparse
import json
import os
import re
import sys
import time

DEFAULT_STATUS_FILE = "/var/spool/nagios/status.dat"

HOST_STATE_NAMES = {
    0: "UP",
    1: "DOWN",
    2: "UNREACHABLE",
}

SERVICE_STATE_NAMES = {
    0: "OK",
    1: "WARNING",
    2: "CRITICAL",
    3: "UNKNOWN",
}

# Lower number means more severe; used for sorting problems to the top.
HOST_SEVERITY = {
    "DOWN": 0,
    "UNREACHABLE": 1,
    "PENDING": 2,
    "UNKNOWN": 3,
    "UP": 4,
}

SERVICE_SEVERITY = {
    "CRITICAL": 0,
    "UNKNOWN": 1,
    "WARNING": 2,
    "PENDING": 3,
    "OK": 4,
}


def parse_status_lines(lines):
    """Return a list of (block_type, attributes) tuples from status.dat lines."""
    blocks = []
    block_type = None
    attributes = None
    for raw_line in lines:
        line = raw_line.strip()
        if attributes is None:
            if line.endswith("{"):
                block_type = line[:-1].strip()
                attributes = {}
        elif line == "}":
            blocks.append((block_type, attributes))
            attributes = None
        elif "=" in line:
            key, value = line.split("=", 1)
            attributes[key] = value
    return blocks


def parse_status_text(text):
    """Return a list of (block_type, attributes) tuples from status.dat text."""
    return parse_status_lines(text.splitlines())


def parse_status_file(path):
    """Return a list of (block_type, attributes) tuples from a status.dat file."""
    with open(path, encoding="utf-8", errors="replace") as status_file:
        return parse_status_lines(status_file)


def format_duration(total_seconds):
    """Format a number of seconds as a short string like '3d 4h' or '12m'."""
    seconds = max(0, int(total_seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m"
    return f"{seconds}s"


PERFDATA_ITEM_RE = re.compile(r"""\s*('(?:[^']|'')*'|[^=\s]+)=(\S*)""")
PERFDATA_VALUE_RE = re.compile(r"^(-?[0-9.]+(?:[eE][-+]?[0-9]+)?|U)(.*)$")


def parse_number(text):
    """Return a number for a perf data field, or None if empty/unparsable."""
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def parse_perfdata(text):
    """Parse a Nagios perf data string into a list of dicts.

    Each item is label=value[UOM];warn;crit;min;max.
    """
    items = []
    for match in PERFDATA_ITEM_RE.finditer(text or ""):
        label = match.group(1)
        if label.startswith("'") and label.endswith("'") and len(label) >= 2:
            label = label[1:-1].replace("''", "'")
        fields = match.group(2).split(";")
        value_match = PERFDATA_VALUE_RE.match(fields[0])
        if value_match:
            value = parse_number(value_match.group(1))
            unit = value_match.group(2)
        else:
            value = None
            unit = ""
        fields += [""] * (5 - len(fields))
        items.append({
            "label": label,
            "value": value,
            "unit": unit,
            "warn": fields[1],
            "crit": fields[2],
            "min": parse_number(fields[3]),
            "max": parse_number(fields[4]),
        })
    return items


def parse_long_output(text):
    """Split long plugin output (newlines escaped as \\n) into a list of lines."""
    if not text:
        return []
    return text.replace("\\n", "\n").split("\n")


def build_flags(attributes, state):
    """Return a list of short notes: acknowledged, soft state, downtime..."""
    flags = []
    if state not in ("UP", "OK", "PENDING"):
        if attributes.get("problem_has_been_acknowledged") == "1":
            flags.append("acknowledged")
        if attributes.get("state_type") == "0":
            current_attempt = attributes.get("current_attempt")
            max_attempts = attributes.get("max_attempts")
            flags.append(f"soft {current_attempt}/{max_attempts}")
    if attributes.get("scheduled_downtime_depth", "0") != "0":
        flags.append("downtime")
    if attributes.get("is_flapping") == "1":
        flags.append("flapping")
    return flags


def build_entry(attributes, state_names, now):
    """Build the common part of a host or service entry."""
    try:
        state = state_names[int(attributes.get("current_state", 3))]
    except (ValueError, KeyError):
        state = "UNKNOWN"
    if attributes.get("has_been_checked") == "0":
        state = "PENDING"

    last_state_change = int(attributes.get("last_state_change") or 0)
    if last_state_change:
        time_in_state = format_duration(now - last_state_change)
    else:
        time_in_state = ""

    return {
        "state": state,
        "since": last_state_change,
        "for": time_in_state,
        "flags": build_flags(attributes, state),
        "output": attributes.get("plugin_output", ""),
        "long_output": parse_long_output(attributes.get("long_plugin_output", "")),
        "perfdata": parse_perfdata(attributes.get("performance_data", "")),
        "perfdata_raw": attributes.get("performance_data", ""),
    }


def collect_hosts(blocks, now):
    """Return a dict of host name -> host entry with its services attached."""
    hosts_by_name = {}

    for block_type, attributes in blocks:
        if block_type in ("hoststatus", "host") and "host_name" in attributes:
            host = build_entry(attributes, HOST_STATE_NAMES, now)
            host["name"] = attributes["host_name"]
            host["services"] = []
            hosts_by_name[host["name"]] = host

    for block_type, attributes in blocks:
        if block_type in ("servicestatus", "service") and "host_name" in attributes:
            host_name = attributes["host_name"]
            host = hosts_by_name.get(host_name)
            if host is None:
                # Service without a matching host block: create a stub host.
                host = {
                    "name": host_name,
                    "state": "UNKNOWN",
                    "since": 0,
                    "for": "",
                    "flags": [],
                    "output": "",
                    "long_output": [],
                    "perfdata": [],
                    "perfdata_raw": "",
                    "services": [],
                }
                hosts_by_name[host_name] = host
            service = build_entry(attributes, SERVICE_STATE_NAMES, now)
            service["name"] = attributes.get("service_description", "?")
            host["services"].append(service)

    return hosts_by_name


def keep_order(hosts):
    """Keep hosts and services in the order of status.dat."""
    return hosts


def sort_by_name(hosts):
    """Sort hosts and their services alphabetically."""
    for host in hosts:
        host["services"].sort(key=lambda service: service["name"])
    return sorted(hosts, key=lambda host: host["name"])


def sort_worst_first(hosts):
    """Sort hosts and their services, worst problems first (ties by name)."""
    for host in hosts:
        host["services"].sort(
            key=lambda service: (SERVICE_SEVERITY[service["state"]], service["name"])
        )
    return sorted(hosts, key=lambda host: (host["worst_severity"], host["name"]))


def compute_worst_severity(host):
    """Return the lowest (worst) severity of a host and its services."""
    severities = [HOST_SEVERITY[host["state"]]]
    severities.extend(SERVICE_SEVERITY[s["state"]] for s in host["services"])
    return min(severities)


def count_states(hosts):
    """Count hosts and services per state name."""
    host_counts = {}
    service_counts = {}
    for host in hosts:
        host_counts[host["state"]] = host_counts.get(host["state"], 0) + 1
        for service in host["services"]:
            state = service["state"]
            service_counts[state] = service_counts.get(state, 0) + 1
    return {
        "hosts": host_counts,
        "services": service_counts,
    }


def convert(blocks, now, status_age_seconds, sort=keep_order):
    """Convert parsed status.dat blocks to the output structure (a dict).

    The sort argument is a function that takes the list of hosts and returns
    it in the desired order: keep_order (default), sort_by_name or
    sort_worst_first.
    """
    hosts = list(collect_hosts(blocks, now).values())
    for host in hosts:
        host["worst_severity"] = compute_worst_severity(host)
    hosts = sort(hosts)

    return {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(now)),
        "status_age": format_duration(status_age_seconds),
        "summary": count_states(hosts),
        "hosts": hosts,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert Nagios status.dat to JSON (written to stdout).",
    )
    parser.add_argument(
        "status_file",
        nargs="?",
        default=DEFAULT_STATUS_FILE,
        help="path to status.dat (default: %(default)s)",
    )
    order = parser.add_mutually_exclusive_group()
    order.add_argument(
        "--sort",
        dest="sort",
        action="store_const",
        const=sort_by_name,
        help="sort hosts and services alphabetically "
             "(default: keep the order of status.dat)",
    )
    order.add_argument(
        "--worst-first",
        dest="sort",
        action="store_const",
        const=sort_worst_first,
        help="list the worst problems first (hosts and services)",
    )
    parser.set_defaults(sort=keep_order)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    now = int(time.time())

    output = convert(
        parse_status_file(args.status_file),
        now,
        now - os.path.getmtime(args.status_file),
        sort=args.sort,
    )
    json.dump(output, sys.stdout, indent=4, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
