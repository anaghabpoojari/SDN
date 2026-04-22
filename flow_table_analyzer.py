"""
Final Clean Flow Table Analyzer (Optimized + No Duplicate Prints)
"""
from pox.core import core
from pox.lib.util import dpid_to_str
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import EventMixin

log = core.getLogger()

# ─────────────────────────────────────────────
# Tunables
# ─────────────────────────────────────────────
IDLE_TIMEOUT    = 20
HARD_TIMEOUT    = 60
STATS_INTERVAL  = 8

mac_tables  = {}
last_output = {}   # used to avoid duplicate prints
DIVIDER = "=" * 60

# ─────────────────────────────────────────────
# Clean printer
# ─────────────────────────────────────────────
def print_clean_table(dpid, stats):
    flows = []
    for s in stats:
        # Skip useless entries
        if s.packet_count == 0:
            continue
        if s.match.dl_type == 0x806:   # ARP
            continue
        if s.match.dl_src is None or s.match.dl_dst is None:
            continue
        flows.append(s)

    print(f"\n{DIVIDER}")
    print(f"  SWITCH {dpid} | Active flows: {len(flows)}")
    print(DIVIDER)

    if not flows:
        print("  No meaningful active flows")
        print(DIVIDER)
        return

    flows = sorted(flows, key=lambda s: -s.packet_count)[:10]

    for i, s in enumerate(flows, 1):
        src     = s.match.dl_src
        dst     = s.match.dl_dst
        out_port = "?"
        for a in s.actions:
            if isinstance(a, of.ofp_action_output):
                out_port = a.port

        print(f"  [{i}]  {src} → {dst} | port {out_port}")
        print(f"       packets={s.packet_count}  age={s.duration_sec}s")

    print(DIVIDER)

# ─────────────────────────────────────────────
# Controller
# ─────────────────────────────────────────────
class FlowTableAnalyzer(EventMixin):

    def __init__(self):
        self.listenTo(core.openflow)
        core.call_delayed(STATS_INTERVAL, self.poll_stats)
        log.info("Final Clean Flow Analyzer running...")

    # ── Switch connect ────────────────────────
    def _handle_ConnectionUp(self, event):
        dpid = dpid_to_str(event.dpid)
        mac_tables[dpid] = {}
        log.info(f"[+] Switch connected: {dpid}")

        # Default rule → controller
        msg = of.ofp_flow_mod()
        msg.priority = 1
        msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
        event.connection.send(msg)

    # ── Learning switch logic ─────────────────
    def _handle_PacketIn(self, event):
        packet  = event.parsed
        if not packet.parsed:
            return

        dpid    = dpid_to_str(event.dpid)
        in_port = event.port

        mac_tables.setdefault(dpid, {})
        mac_tables[dpid][packet.src] = in_port

        out_port = mac_tables[dpid].get(packet.dst)

        # Flood if unknown
        if out_port is None:
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            msg.data    = event.ofp
            msg.in_port = in_port
            event.connection.send(msg)
            return

        # Install simplified flow (MAC-based)
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match()
        msg.match.dl_src    = packet.src
        msg.match.dl_dst    = packet.dst
        msg.idle_timeout    = IDLE_TIMEOUT
        msg.hard_timeout    = HARD_TIMEOUT
        msg.priority        = 10
        msg.actions.append(of.ofp_action_output(port=out_port))
        msg.data = event.ofp
        event.connection.send(msg)

        log.info(f"Flow installed: {packet.src} → {packet.dst}")

    # ── Flow removed logging ──────────────────
    def _handle_FlowRemoved(self, event):
        dpid = dpid_to_str(event.connection.dpid)
        if event.ofp.reason == of.OFPRR_IDLE_TIMEOUT:
            reason = "IDLE_TIMEOUT"
        elif event.ofp.reason == of.OFPRR_HARD_TIMEOUT:
            reason = "HARD_TIMEOUT"
        else:
            reason = "DELETE"
        log.info(f"[FLOW REMOVED] {dpid}  reason={reason}")

    # ── Stats received ────────────────────────
    def _handle_FlowStatsReceived(self, event):
        dpid = dpid_to_str(event.connection.dpid)

        # Create snapshot of meaningful flows
        current = [
            (s.match.dl_src, s.match.dl_dst, s.packet_count)
            for s in event.stats
            if s.packet_count > 0
            and s.match.dl_src is not None
            and s.match.dl_dst is not None
            and s.match.dl_type != 0x806
        ]

        # Skip if no change
        if last_output.get(dpid) == current:
            return
        last_output[dpid] = current

        print_clean_table(dpid, event.stats)

    # ── Poll stats ────────────────────────────
    def poll_stats(self):
        if core.openflow:
            for con in core.openflow.connections:
                con.send(of.ofp_stats_request(
                    body=of.ofp_flow_stats_request()
                ))
        core.call_delayed(STATS_INTERVAL, self.poll_stats)

# ─────────────────────────────────────────────
# Launch
# ─────────────────────────────────────────────
def launch():
    core.registerNew(FlowTableAnalyzer)

    def attach():
        analyzer = core.components.get("FlowTableAnalyzer")
        if analyzer:
            core.openflow.addListenerByName(
                "FlowStatsReceived",
                analyzer._handle_FlowStatsReceived
            )
            core.openflow.addListenerByName(
                "FlowRemoved",
                analyzer._handle_FlowRemoved
            )
    core.call_delayed(0.1, attach)
