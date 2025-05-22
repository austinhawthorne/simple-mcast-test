#!/usr/bin/env python3
import socket
import struct
import threading
import argparse
import time
import os

import asciichartpy

lock = threading.Lock()

# Packet-loss stats
total_received = 0
total_lost     = 0
last_seq       = None
loss_history   = []

# Jitter stats
arrival_times        = []
inter_interval_hist  = []
jitter_history       = []

def receiver_thread(group, port, iface):
    global total_received, total_lost, last_seq
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((iface, port))
    mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, _ = sock.recvfrom(1024)
        recv_time = time.time()
        seq, = struct.unpack('!I', data)

        with lock:
            # ——— loss tracking ———
            if last_seq is not None:
                gap = seq - last_seq - 1
                if gap > 0:
                    total_lost += gap
            total_received += 1
            last_seq = seq
            loss = (100 * total_lost / (total_received + total_lost)
                    if (total_received + total_lost) > 0 else 0)
            loss_history.append(loss)

            # ——— jitter tracking ———
            if arrival_times:
                interval = recv_time - arrival_times[-1]
                inter_interval_hist.append(interval)
                # compute absolute difference between last two intervals
                if len(inter_interval_hist) > 1:
                    j = abs(inter_interval_hist[-1] - inter_interval_hist[-2])
                    jitter_history.append(j)
            arrival_times.append(recv_time)

def dashboard(update_interval=1.0, chart_width=60):
    """Clears screen and redraws loss + jitter charts."""
    while True:
        with lock:
            recv = total_received
            lost = total_lost
            losses = loss_history[-chart_width:]
            jits = jitter_history[-chart_width:]

        loss_rate = (100 * lost / (recv + lost)) if (recv + lost) > 0 else 0

        # jitter metrics (in ms)
        if jits:
            jits_ms = [j * 1000 for j in jits]
            avg_jit = sum(jits_ms) / len(jits_ms)
            min_jit = min(jits_ms)
            max_jit = max(jits_ms)
        else:
            jits_ms = []
            avg_jit = min_jit = max_jit = 0

        os.system('clear')
        print("🎯  Multicast Receiver Dashboard  🎯")
        print(f" Group            : {ARGS.group}")
        print(f" Port             : {ARGS.port}")
        print(f" Interface        : {ARGS.iface or 'all'}")
        print("───────────────────────────────────────────")
        print(f" Packets Received : {recv}")
        print(f" Packets Lost     : {lost}")
        print(f" Loss Rate        : {loss_rate:.2f}%")
        print("───────────────────────────────────────────")
        if losses:
            print(f" Loss % (last {len(losses)}):")
            print(asciichartpy.plot(losses, {'height': 6}))
        else:
            print(" Waiting for packets…")

        print("\n───────────────────────────────────────────")
        print(f" Jitter (ms) avg={avg_jit:.2f}  min={min_jit:.2f}  max={max_jit:.2f}")
        if jits_ms:
            print(f" Last {len(jits_ms)} samples:")
            print(asciichartpy.plot(jits_ms, {'height': 6}))
        else:
            print(" Gathering jitter data…")

        print(f"\n⏎ Refresh every {ARGS.interval:.1f}s   Ctrl-C to quit")
        time.sleep(update_interval)

if __name__ == '__main__':
    p = argparse.ArgumentParser(
        description="Headless multicast receiver w/ ASCII loss & jitter charts"
    )
    p.add_argument('--group',   default='224.1.1.1', help='Multicast group IP')
    p.add_argument('--port',    type=int,   default=5007,  help='UDP port')
    p.add_argument('--iface',   default='',           help='Local interface (empty=all)')
    p.add_argument('--interval',type=float, default=1.0,   help='Dashboard refresh (s)')
    p.add_argument('--width',   type=int,   default=60,    help='Chart width (# samples)')
    ARGS = p.parse_args()

    # start the receive thread
    t = threading.Thread(
        target=receiver_thread,
        args=(ARGS.group, ARGS.port, ARGS.iface),
        daemon=True
    )
    t.start()

    # launch ASCII dashboard
    try:
        dashboard(update_interval=ARGS.interval, chart_width=ARGS.width)
    except KeyboardInterrupt:
        print("\nExiting…")
