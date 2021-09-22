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


def process_section(acc, lines):
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
            check_patt(line, QRSRP_PATT, acc, [("PRX", int), ("DRX", int), ("RX2", int), ("RX3", int)])
            )

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