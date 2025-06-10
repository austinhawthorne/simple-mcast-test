To test an ability of a network to support multicast you can use these simple scripts.  One acts as a multicast source that you can set the group and port and it will start streaming packets.  The other acts as a multicast receiver that joins that source and accepts the streamed packets.  Both will display the packet stream with jitter and loss stats.

To run the source, run 'sudo python mcast-source.py', it will default to group 224.1.1.1 on port 5007 (you can change this with options):

```
🚀  Multicast Sender Dashboard  🚀
 Group           : 224.1.1.1
 Port            : 5007
 TTL             : 1
────────────────────────────────────────
 Packets Sent    : 151
 Target Interval : 0.100 s
 Avg Actual Int. : 0.100 s
 Jitter          : avg=-0.00 ms  min=-0.00 ms  max=-0.00 ms
────────────────────────────────────────
 Jitter (ms) over last 60 sends:
   -0.00  ┼───────────────────────────────────────────────────────────
   -0.00  ┼

⏎ Refresh every 1.0s   Ctrl-C to quit
```

To set the receiver, run 'sudo python mcast-receiver.py', will default to the 224.1.1.1 group on port 5007 (you can change this with options):

```
🎯  Multicast Receiver Dashboard  🎯
 Group            : 224.1.1.1
 Port             : 5007
 Interface        : all
───────────────────────────────────────────
 Packets Received : 41
 Packets Lost     : 0
 Loss Rate        : 0.00%
───────────────────────────────────────────
 Loss % (last 41):
    0.00  ┼────────────────────────────────────────

───────────────────────────────────────────
 Jitter (ms) avg=0.04  min=0.00  max=0.23
 Last 39 samples:
    0.23  ┼
    0.20  ┤                             ╭╮
    0.16  ┤                             ││
    0.13  ┤                             ││
    0.10  ┤                            ╭╯╰╮
    0.07  ┤                    ╭─╮╭───╮│  │
    0.03  ┼╮╭╮   ╭──╮     ╭─╮ ╭╯ ││   ││  │  ╭──╮
    0.00  ┤╰╯╰───╯  ╰─────╯ ╰─╯  ╰╯   ╰╯  ╰──╯  ╰

⏎ Refresh every 1.0s   Ctrl-C to quit
