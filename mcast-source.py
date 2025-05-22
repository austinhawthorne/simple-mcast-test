#!/usr/bin/env python3
import socket
import struct
import threading
import argparse
import time
import os

import asciichartpy

lock = threading.Lock()
seq = 0
timestamps = []
interval_history = []
jitter_history = []

def sender_thread(group, port, ttl, interval, history_width):
    global seq, timestamps, interval_history, jitter_history
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', ttl))

    next_time = time.time()
    while True:
        now = time.time()
        if now < next_time:
            time.sleep(next_time - now)
            now = next_time

        # send seq #
        data = struct.pack('!I', seq)
        sock.sendto(data, (group, port))

        with lock:
            # record timestamp
            timestamps.append(now)
            if len(timestamps) > 1:
                # actual interval & jitter
                actual = timestamps[-1] - timestamps[-2]
                interval_history.append(actual)
                jitter = actual - interval
                jitter_history.append(jitter)

                # trim history
                if len(interval_history) > history_width:
                    del interval_history[:-history_width]
                    del jitter_history[:-history_width]

            seq += 1

        next_time += interval

def dashboard(group, port, ttl, interval, refresh, history_width):
    """Clears screen & redraws send stats + jitter chart."""
    while True:
        with lock:
            sent = seq
            ints = list(interval_history)
            jits = list(jitter_history)

        avg_int = (sum(ints) / len(ints)) if ints else 0
        if jits:
            avg_jit = sum(jits) / len(jits)
            min_jit = min(jits)
            max_jit = max(jits)
        else:
            avg_jit = min_jit = max_jit = 0

        # clear
        os.system('clear')

        print("🚀  Multicast Sender Dashboard  🚀")
        print(f" Group           : {group}")
        print(f" Port            : {port}")
        print(f" TTL             : {ttl}")
        print("────────────────────────────────────────")
        print(f" Packets Sent    : {sent}")
        print(f" Target Interval : {interval:.3f} s")
        print(f" Avg Actual Int. : {avg_int:.3f} s")
        print(f" Jitter          : avg={avg_jit*1000:.2f} ms  min={min_jit*1000:.2f} ms  max={max_jit*1000:.2f} ms")
        print("────────────────────────────────────────")
        if jits:
            # plot last N jitters in ms
            jits_ms = [j*1000 for j in jits]
            print(" Jitter (ms) over last {} sends:".format(len(jits_ms)))
            print(asciichartpy.plot(jits_ms, {'height': 10}))
        else:
            print(" Gathering data...")

        print("\n⏎ Refresh every {:.1f}s   Ctrl-C to quit".format(refresh))
        time.sleep(refresh)

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description="Headless multicast sender w/ ASCII-chart jitter dashboard"
    )
    p.add_argument('--group',   default='224.1.1.1', help='Multicast group IP')
    p.add_argument('--port',    type=int,   default=5007,  help='UDP port')
    p.add_argument('--ttl',     type=int,   default=1,     help='Multicast TTL')
    p.add_argument('--interval',type=float, default=0.1,   help='Seconds between packets')
    p.add_argument('--refresh', type=float, default=1.0,   help='Dashboard refresh interval (s)')
    p.add_argument('--width',   type=int,   default=60,    help='History length for chart (# samples)')
    args = p.parse_args()

    # start the sender
    t = threading.Thread(
        target=sender_thread,
        args=(args.group, args.port, args.ttl, args.interval, args.width),
        daemon=True
    )
    t.start()

    # launch the ASCII dashboard
    try:
        dashboard(
            args.group, args.port, args.ttl,
            args.interval, args.refresh, args.width
        )
    except KeyboardInterrupt:
        print("\nExiting…")
