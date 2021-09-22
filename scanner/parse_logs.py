#!/usr/bin/env python3

import argparse
import csv
import json
import re
import sys

from collections import OrderedDict


FIELDS = ["Deg", "Time",
    "Temp", # AT+QTEMP
    "RSSI", "BitErrorRate", # AT+CSQ
    # AT+QENG / serving cell
    "SC Mode", "SC State", "SC LTE Net Mode", "SC LTE MCC", "SC NSA MCC", "SC LTE MNC", "SC NSA MNC",
    "SC LTE CellId", "SC LTE PCID", "SC NSA PCID", "SC LTE EARFCN", "SC NSA ARFCN", "SC LTE Band",
    "SC NSA Band", "SC LTE UL Bandwidth", "SC LTE DL Bandwidth", "SC LTE TAC", "SC LTE RSRP", "SC NSA RSRP",
    "SC LTE RSRQ", "SC NSA RSRQ", "SC LTE RSSI", "SC LTE SINR", "SC NSA SINR", "SC LTE CQI", "SC LTE TxPwr",
    # AT+QRSRP
    "PRX", "DRX", "RX2", "RX3",
    # AT+QCAINFO / carrier aggregation
    "CA", "CA Cnt", "CA Tot Bandwidth",
    # AT+QNWPREFCFG="mode_pref"
    "Mode Pref",
    # AT+CREG?
    "Reg State",
    # AT+COPS?
    "Oper", "AcT",
    # AT+QENDC
    "5G Icon",
    # Ping stats
    "Ping Pkt Loss", "Ping Min", "Ping Max", "Ping Avg", "Ping Jitter"
    ]

SECTION_PATT = re.compile(r"^=+$")
TIME_PATT = re.compile(r"^Current time:\s+([^\s]+)\s*$")
HEADING_PATT = re.compile(r"^Current heading:\s*(\d+)\s*$")
TEMP_PATT = re.compile(r"^\d+:\s*\+QTEMP:\"mdm-q6-usr\",\"(\d+)\"\s*$")
CSQ_PATT = re.compile(r"^\d+:\s*\+CSQ:\s*(\d+),(\d+)\s*$")

QENG_NSA1_PATT =  re.compile(r"^\d+:\s*\+QENG:\s*\"servingcell\",\s*\"([^\"]+)\"\s*$")
QENG_NSA2_PATT =  re.compile(r"^\d+:\s*\+QENG:\s*\"LTE\",\"([^\"]+)\",\s*(\d+),\s*(\d+),\s*([0-9a-fA-F]+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*([0-9a-fA-F]+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+).*$")
QENG_NSA3_PATT =  re.compile(r"^\d+:\s*\+QENG:\s*\"(NR5G-NSA)\",(\d+),(\d+),\s*(\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(\d+),\s*(\d+).*$")
QENG_SA_PATT =    re.compile(r"^\d+:\s*\+QENG:\s*\"servingcell\",\s*\"([^\"]+)\",\"(NR5G-SA)\".*$")
QENG_LTE_PATT =   re.compile(r"^\d+:\s*\+QENG:\s*\"servingcell\",\s*\"([^\"]+)\",\"(LTE)\".*$")
QENG_WCDMA_PATT = re.compile(r"^\d+:\s*\+QENG:\s*\"servingcell\",\s*\"([^\"]+)\",\"(WCDMA)\".*$")

QRSRP_PATT = re.compile(r"^\d+:\s*\+QRSRP:\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)")

QCAINFO_PCC_PATT = re.compile(r"^\d+:\s*\+QCAINFO:\s*\"(PCC)\",\s*(\d+),\s*(\d+),\s*\"LTE BAND (\d+)\",\s*(\d+),\s*(\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\s*$")
QCAINFO_SCC_PATT = re.compile(r"^\d+:\s*\+QCAINFO:\s*\"(SCC)\",\s*(\d+),\s*(\d+),\s*\"LTE BAND (\d+)\",\s*(\d+),\s*(\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)\s*$")

MODEPREF_PATT = re.compile(r"^\d+:\s*\+QNWPREFCFG:\s*\"mode_pref\",([A-Z0-9]+)")

CREG_PATT = re.compile(r"^\d+:\s*\+CREG:\s*\d+,\s*(\d+)")

COPS_PATT = re.compile(r"^\d+:\s*\+COPS:\s*\d+,\d+,\"([^\"]+)\",(\d+)")

QENDC_PATT = re.compile(r"^\d+:\s*\+QENDC:\s*\d+,\d+,\d+,(\d+)")

PING_1_PATT = re.compile(r".*bytes from.*time=([0-9.]+) ms")
PING_2_PATT = re.compile(r".* (\d+)% packet loss.*")


def check_patt(line, patt, acc, fields):
    m = patt.match(line)
    if m:
        for i, field in enumerate(fields, start=1):
            if type(field) == tuple:
                field, fn = field
                acc[field] = fn(m.group(i))
            else:
                acc[field] = m.group(i)
        return True
    else:
        return False

BER_VALS = [0.14, 0.28, 0.57, 1.13, 2.26, 4.53, 9.05, 18.10]
def map_ber(v):
    ber = int(v)
    if ber == 99:
        return None
    else:
        return BER_VALS[ber]


def map_rssi(v):
    rssi = int(v)
    if rssi == 99:
        return None
    else:
        return -113 + rssi*2


LTE_BANDWIDTH_VALS = [1.4, 3.0, 5.0, 10.0, 15.0, 20.0]
def map_lte_bandwidth(v):
    return LTE_BANDWIDTH_VALS[int(v)]


PCELL_STATE = ["No Serving", "Registered"]
def map_pcell_state(v):
    return PCELL_STATE[int(v)]


SCELL_STATE = ["Deconfigured", "Configured Deactivate", "Configured Activated"]
def map_scell_state(v):
    return SCELL_STATE[int(v)]


def map_scc_bandwidth(v):
    v = int(v)
    if v == 6:
        return 1.4
    else:
        return v / 5


CREG_STAT = ["Not Registered", "Registered Home Network", "Registration Denied", "Unknown", "Registered Roaming"]
def map_creg_state(v):
    return CREG_STAT[int(v)]

ACT_STATE = [None, None, "UTRAN", None, "UTRAN W/HSDPA", "UTRAN W/HSUPA", "UTRAN W/HSDPA&HSUPA", "E-UTRAN",
             None, None, "E-UTRAN 5GCN", "NR 5GCN", "NG-RAN", "E-UTRAN-NR dual connect"]
def map_act_state(v):
    return ACT_STATE[int(v)]


def process_section(acc, lines):
    ca = []
    ping = []
    for line in lines:
        (check_patt(line, TIME_PATT, acc, ["Time"]) or
            check_patt(line, HEADING_PATT, acc, [("Deg", int)]) or
            check_patt(line, TEMP_PATT, acc, [("Temp", int)]) or
            check_patt(line, CSQ_PATT, acc, [("RSSI", map_rssi), ("BitErrorRate", map_ber)]) or
            check_patt(line, QENG_NSA1_PATT, acc, ["SC State"]) or
            check_patt(line, QENG_NSA2_PATT, acc, ["SC LTE Net Mode", ("SC LTE MCC", int), ("SC LTE MNC", int),
                                                   "SC LTE CellId", ("SC LTE PCID", int), ("SC LTE EARFCN", int),
                                                   ("SC LTE Band", int),
                                                   ("SC LTE UL Bandwidth", map_lte_bandwidth),
                                                   ("SC LTE DL Bandwidth", map_lte_bandwidth),
                                                   "SC LTE TAC", ("SC LTE RSRP", int), ("SC LTE RSRQ", int), ("SC LTE RSSI", int),
                                                   ("SC LTE SINR", int), ("SC LTE CQI", int), ("SC LTE TxPwr", int)]) or
            check_patt(line, QENG_NSA3_PATT, acc, ["SC Mode", ("SC NSA MCC", int), ("SC NSA MNC", int), ("SC NSA PCID", int),
                                                   ("SC NSA RSRP", int), ("SC NSA SINR", int), ("SC NSA RSRQ", int),
                                                   ("SC NSA ARFCN", int), ("SC NSA Band", int)]) or
            check_patt(line, QENG_SA_PATT, acc, ["SC State", "SC Mode"]) or
            check_patt(line, QENG_LTE_PATT, acc, ["SC State", "SC Mode"]) or
            check_patt(line, QENG_WCDMA_PATT, acc, ["SC State", "SC Mode"]) or
            check_patt(line, QRSRP_PATT, acc, [("PRX", int), ("DRX", int), ("RX2", int), ("RX3", int)]) or
            check_patt(line, MODEPREF_PATT, acc, ["Mode Pref"]) or
            check_patt(line, CREG_PATT, acc, [("Reg State", map_creg_state)]) or
            check_patt(line, COPS_PATT, acc, ["Oper", ("AcT", map_act_state)]) or
            check_patt(line, QENDC_PATT, acc, [("5G Icon", lambda v: int(v) == 1)]) or
            check_patt(line, PING_2_PATT, acc, [("Ping Pkt Loss", int)])
            )

        ca_obj = {}
        if (check_patt(line, QCAINFO_PCC_PATT, ca_obj, ["Type", ("EARFCN", int), ("Bandwidth", map_lte_bandwidth),
                                                        ("Band", int), ("PCell State", map_pcell_state), "PCID",
                                                        ("RSRP", int), ("RSRQ", int), ("RSSI", int), ("SINR", int)]) or
                check_patt(line, QCAINFO_SCC_PATT, ca_obj, ["Type", ("EARFCN", int), ("Bandwidth", map_scc_bandwidth),
                                                        ("Band", int), ("SCell State", map_scell_state), "PCID",
                                                        ("RSRP", int), ("RSRQ", int), ("RSSI", int), ("SINR", int)])):
            ca.append(ca_obj)

        ping_obj = {}
        if check_patt(line, PING_1_PATT, ping_obj, [("P", float)]):
            ping.append(ping_obj["P"])

    acc["CA"] = ca
    acc["CA Cnt"] = len(ca)
    acc["CA Tot Bandwidth"] = sum([x["Bandwidth"] for x in ca])

    ping_min = None
    ping_max = None
    ping_jitter = 0
    ping_sum = 0
    for i, sample in enumerate(ping):
        if not ping_min or sample < ping_min:
            ping_min = sample
        if not ping_max or sample > ping_max:
            ping_max = sample
        ping_sum = ping_sum + sample
        if i > 0:
            ping_jitter = ping_jitter + abs(ping[i] - ping[i - 1])
    acc["Ping Min"] = ping_min
    acc["Ping Max"] = ping_max
    if len(ping) > 0:
        acc["Ping Avg"] = ping_sum / len(ping)
    else:
        acc["Ping Avg"] = None
    if len(ping) > 1:
        acc["Ping Jitter"] = ping_jitter / len(ping) - 1
    else:
        acc["Ping Jitter"] = None

    if acc.get("Time"):
        json.dump(acc, sys.stdout)
        sys.stdout.write("\n")
        for k in acc.keys():
            acc[k] = None


def main(args):
    parser = argparse.ArgumentParser("parse_logs.py", description="Extract LTE signal data points from logs and produce CSV")
    args = parser.parse_args(args)

    writer= OrderedDict((field, None) for field in FIELDS)
    
    section = []
    for line in sys.stdin:
        if SECTION_PATT.match(line):
            process_section(writer, section)
            section = []
        else:
            section.append(line)

    process_section(writer, section)


if __name__ == '__main__':
    main(sys.argv[1:])