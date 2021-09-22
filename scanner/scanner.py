#!/usr/bin/env python3

import argparse
from datetime import datetime
import os
import subprocess
import sys
import time


def log(msg):
    print(msg, flush=True)


def do_ssh_cmd(remote, cmd):
    log(f"ssh: {cmd}")
    p = subprocess.Popen(["ssh", remote, cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(p.stdout.readline, b''):
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()


def do_at(modem_host, cmds):
    cmds = " ".join([f"'{cmd}'" for cmd in cmds])
    do_ssh_cmd(modem_host, f"~/atcmd-locked 1 --device /dev/ttyUSB2 --cmds {cmds}")


def do_ping(modem_host):
    do_ssh_cmd(modem_host, "ping 8.8.8.8 -c 4")


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--modem-host", default="root@192.168.11.1", help="Host to run modem ssh commands")
    parser.add_argument("--start", type=int, default=0, help="Start heading")
    parser.add_argument("--end", type=int, default=360, help="Final heading")
    parser.add_argument("--step", type=int, default=2, help="Number of degrees for each increment")
    parser.add_argument("--poll-rate", type=int, default=6, help="Number of seconds between retrieving modem status")
    parser.add_argument("--step-rate", type=int, default=60, help="Number of seconds before incrementing heading")
    args = parser.parse_args(args)

    if args.start < 0 or args.start > 360 or args.end < 0 or args.end > 360 or args.start > args.end:
        print("--start must be less than --end and both must be between 0 and 360")
        sys.exit(1)

    if args.poll_rate < 2 or args.poll_rate > 30:
        print("--poll-rate must be between 2 and 30")
        sys.exit(1)

    if args.step_rate < 10 or args.step_rate > 300:
        print("--step-rate must be between 10 and 300")
        sys.exit(1)

    for deg in range(args.start, args.end + 1, args.step):
        os.system(f"./rotator.py set {deg}")
        t = time.time()
        e = t + args.step_rate

        while time.time() <= e:
            log(f"===================")
            log(f"Current time: {datetime.utcnow().isoformat()}")
            log(f"Current heading: {deg}")

            do_at(args.modem_host, [
                'AT+QTEMP',
                'AT+CSQ',
                'AT+QENG="servingcell"',
                'AT+QRSRP', # not documented, but returns strength of each antenna
                'AT+QCAINFO',
                'AT+QNWPREFCFG="mode_pref"',
                'AT+CREG?',
                'AT+COPS?',
                'AT+QNWINFO',
                'AT+QENDC'
                ])
            do_ping(args.modem_host)

            time.sleep(args.poll_rate)


if __name__ == "__main__":
    main(sys.argv[1:])
