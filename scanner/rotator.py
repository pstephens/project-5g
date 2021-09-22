#!/usr/bin/env python3

### Control a Green Heron RT-21 Rotator Controller using the serial port

import argparse
import re
import serial
import sys
from time import sleep


def get_serial(device):
    return serial.Serial(device, 4800, timeout=1)


def print_bytes(bytes):
    prev_is_hex = False
    is_first = True
    for b in bytes:
        if b < 32:
            if not is_first:
                print(" ", end="")
            print(f"{hex(b)}", end="")
            prev_is_hex = True
        else:
            if prev_is_hex:
                print(" ", end="")
            print(chr(b), end="")
            prev_is_hex = False
        is_first = False
    print()

def do_cmd(ser, cmd):
    print(f"executing: {cmd}")
    ser.write(cmd.encode())
    print_bytes(ser.read(100))


def do_set(ser, deg):
    print(f"setting heading to: {deg}")
    ser.write(f";AP1{deg};AM1;".encode("ascii"))
    while True:
        ser.write("R21;".encode("ascii"))
        bytes = ser.read(100)
        if bytes[0] != 1:
            raise Exception("First byte of response is not an SOH")
        if bytes[1] != 48:
            raise Exception("Unexpected second character in response")
        if bytes[2] == 0:
            print(f"Rotated to {bytes[4:-1].decode('ascii')}")
            return
        elif bytes[2] == 1:
            pass
        elif bytes[2] == 2:
            raise Exception("Error, no motion")
        elif bytes[2] == 4:
            raise Exception("Pot out of range")
        elif bytes[2] == 5:
            raise Exception("Counter range")
        else:
            raise Exception("Invalid status code in response")


def do_get(ser):
    ser.write("BI1;".encode())
    print_bytes(ser.read(100))


DEGREE_PATTERN = re.compile(r"^([0-9]{1,3})(\.[0-9])?$")
def validate_degrees(v):
    m = DEGREE_PATTERN.match(v)
    if not m or float(v) < 0.0 or float(v) > 360.0:
        raise argparse.ArgumentTypeError("Degrees must be between 0.0 and 360.0")
    return m.group(1).zfill(3) + (m.group(2) or ".0")


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="/dev/ttyUSB0", help="Serial device")
    subparsers = parser.add_subparsers()
    cmd_parser = subparsers.add_parser("cmd", help="Execute a command and wait for a response")
    cmd_parser.add_argument("cmd", help="Command to execute")
    cmd_parser.set_defaults(which="cmd")
    set_parser = subparsers.add_parser("set", help="Rotate to the specified heading")
    set_parser.add_argument("deg", type=validate_degrees, help="Coordinates in degrees")
    set_parser.set_defaults(which="set")
    get_parser = subparsers.add_parser("get", help="Print the current heading")
    get_parser.set_defaults(which="get")

    args = parser.parse_args(args)

    if args.which == "cmd":
        do_cmd(get_serial(args.device), args.cmd)
    elif args.which == "set":
        do_set(get_serial(args.device), args.deg)
    elif args.which == "get":
        do_get(get_serial(args.device))
    else:
        parser.print_help()
        
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])

