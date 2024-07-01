#!/usr/bin/env python3
import time
import argparse

from concurrent.futures import ThreadPoolExecutor

from connection import Connection
from msgparser import MsgParser
from procfs import find_abstract_sockets

VERSION_HEADER = bytearray('MangoHudControlVersion', 'utf-8')
DEVICE_NAME_HEADER = bytearray('DeviceName', 'utf-8')
MANGOHUD_VERSION_HEADER = bytearray('MangoHudVersion', 'utf-8')

DEFAULT_SERVER_ADDRESS = "\0mangohud"

def send_command(args, address):
    conn = Connection(address)
    msgparser = MsgParser(conn)

    version = 0
    name = None
    mangohud_version = None

    msgs = msgparser.readCmd(3)

    for m in msgs:
        cmd, param = m
        if cmd == VERSION_HEADER:
            version = int(param)
        elif cmd == DEVICE_NAME_HEADER:
            name = param.decode('utf-8')
        elif cmd == MANGOHUD_VERSION_HEADER:
            mangohud_version = param.decode('utf-8')

    if args.info:
        info = "{addr}: Protocol Version: {}\n"
        info += "{addr}: Device Name: {}\n"
        info += "{addr}: MangoHud Version: {}"
        print(info.format(version, name, mangohud_version, addr=address))

    if args.cmd == 'toggle-logging':
        conn.send(bytearray(':logging;', 'utf-8'))
    elif args.cmd == 'start-logging':
        conn.send(bytearray(':logging=1;', 'utf-8'))

    elif args.cmd == 'stop-logging':
        conn.send(bytearray(':logging=0;', 'utf-8'))
        now = time.monotonic()
        while True:
            msg = str(conn.recv(3))
            if "LoggingFinished" in msg:
                print(f"{address}: Logging has stopped")
                return True
            elapsed = time.monotonic() - now
            if elapsed > 3:
                print(f"{address}: Stop logging timed out")
                return False

    elif args.cmd == 'toggle-hud':
        conn.send(bytearray(':hud;', 'utf-8'))
    elif args.cmd == 'toggle-fcat':
        conn.send(bytearray(':fcat;', 'utf-8'))

    elif version >= 2:
        if args.cmd == 'reload-cfg':
            conn.send(bytearray(':reload_cfg;', 'utf-8'))

        elif args.cmd == 'upload-log':
            conn.send(bytearray(':upload_log;', 'utf-8'))
            now = time.monotonic()
            while True:
                msg = str(conn.recv(10))
                if "NoLogFiles" in msg:
                    print(f"{address}: No log files to upload")
                    return True
                elif "UploadFinished" in msg:
                    print(f"{address}: Upload has finished")
                    return False
                elapsed = time.monotonic() - now
                if elapsed > 10:
                    print(f"{address}:Upload timed out")
                    return False
        elif args.cmd == 'upload-logs':
            conn.send(bytearray(':upload_logs;', 'utf-8'))
            now = time.monotonic()
            while True:
                msg = str(conn.recv(10))
                if "NoLogFiles" in msg:
                    print(f"{address}: No log files to upload")
                    return True
                elif "UploadFinished" in msg:
                    print(f"{address}: Upload has finished")
                    return True
                elapsed = time.monotonic() - now
                if elapsed > 10:
                    print(f"{address}: Upload timed out")
                    return False

        elif args.cmd == 'reset-fps-metrics':
            conn.send(bytearray(':reset_fps_metrics;', 'utf-8'))

        elif args.cmd == 'toggle-fps-limit':
            if args.entry:
                conn.send(bytearray(f':fps_limit={args.entry};', 'utf-8'))
            else:
                conn.send(bytearray(':fps_limit;', 'utf-8'))
        elif args.cmd == 'set-fps-limit':
            conn.send(bytearray(f':set_fps_limit={args.limit};', 'utf-8'))

        elif args.cmd == 'toggle-preset':
            if args.entry:
                conn.send(bytearray(f':preset={args.entry};', 'utf-8'))
            else:
                conn.send(bytearray(':preset;', 'utf-8'))

        elif args.cmd == 'toggle-hud-position':
            if args.position:
                conn.send(bytearray(f':hud_position={args.position};', 'utf-8'))
            else:
                conn.send(bytearray(':hud_position;', 'utf-8'))

    else:
        print(f"{address}: Command {args.cmd} not supported by receiver (protocol {version})")
        return False

    return True

def control(args):
    futures = []

    with ThreadPoolExecutor() as executor:
        if args.socket:
            try:
                candidates = find_abstract_sockets(args.socket) or [args.socket]
            except IOError:
                candidates = [args.socket]

            for socket in candidates:
                futures.append(executor.submit(send_command, args, '\0' + socket))
        else:
            futures.append(executor.submit(send_command, args, DEFAULT_SERVER_ADDRESS))

    if any([not f.result() for f in futures]):
        return 1

    return 0

def main():
    parser = argparse.ArgumentParser(description='MangoHud control client')
    parser.add_argument('--info', action='store_true', help='Print info from socket')
    parser.add_argument('--socket', '-s', type=str, help='Path to socket')

    commands = parser.add_subparsers(help='commands to run', dest='cmd')

    commands.add_parser('toggle-hud')
    commands.add_parser('toggle-logging')
    commands.add_parser('start-logging')
    commands.add_parser('stop-logging')
    commands.add_parser('toggle-fcat')
    commands.add_parser('reload-cfg')
    commands.add_parser('upload-log')
    commands.add_parser('upload-logs')
    commands.add_parser('reset-fps-metrics')

    toggle_fps_limit = commands.add_parser('toggle-fps-limit')
    toggle_fps_limit.add_argument('--entry', type=int, required=False)

    set_fps_limit = commands.add_parser('set-fps-limit')
    set_fps_limit.add_argument('limit', type=float)

    toggle_preset = commands.add_parser('toggle-preset')
    toggle_preset.add_argument('--entry', type=int, required=False)

    toggle_hud_position = commands.add_parser('toggle-hud-position')
    toggle_hud_position.add_argument('--position', type=str, required=False)

    args = parser.parse_args()

    return control(args)

if __name__ == '__main__':
    main()
