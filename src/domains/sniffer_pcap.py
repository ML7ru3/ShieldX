import logging
import threading
import time
from collections import defaultdict
from scapy.all import AsyncSniffer, IP, TCP, UDP
import pandas as pd

class PacketFlow:
    """
    Represents a bidirectional flow and extracts basic features like DoHLyzer, ready for ML/AI analysis.
    """
    def __init__(self, five_tuple):
        self.five_tuple = five_tuple  # (src_ip, src_port, dst_ip, dst_port, proto)
        self.packets = []
        self.timestamps = []
        self.sizes = []
        self.start_time = None
        self.end_time = None

    def add_packet(self, pkt):
        ts = pkt.time
        size = len(pkt)
        self.packets.append(pkt)
        self.timestamps.append(ts)
        self.sizes.append(size)
        if self.start_time is None or ts < self.start_time:
            self.start_time = ts
        if self.end_time is None or ts > self.end_time:
            self.end_time = ts

    def to_features(self):
        features = {
            'src_ip': self.five_tuple[0],
            'src_port': self.five_tuple[1],
            'dst_ip': self.five_tuple[2],
            'dst_port': self.five_tuple[3],
            'proto': self.five_tuple[4],
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': (self.end_time - self.start_time) if self.end_time and self.start_time else 0,
            'num_packets': len(self.packets),
            'total_bytes': sum(self.sizes),
            'mean_pkt_len': pd.Series(self.sizes).mean() if self.sizes else 0,
            'std_pkt_len': pd.Series(self.sizes).std() if self.sizes else 0,
            'min_pkt_len': min(self.sizes) if self.sizes else 0,
            'max_pkt_len': max(self.sizes) if self.sizes else 0,
            'median_pkt_len': pd.Series(self.sizes).median() if self.sizes else 0,
            # Add more as needed for ML
        }
        return features


def extract_five_tuple(pkt):
    if IP in pkt:
        ip = pkt[IP]
        proto = None
        src_port = 0
        dst_port = 0
        if TCP in pkt:
            proto = 'TCP'
            src_port = pkt[TCP].sport
            dst_port = pkt[TCP].dport
        elif UDP in pkt:
            proto = 'UDP'
            src_port = pkt[UDP].sport
            dst_port = pkt[UDP].dport
        else:
            proto = ip.proto
        return (ip.src, src_port, ip.dst, dst_port, proto)
    return None


class PcapSniffer:
    """
    Sniffs packets on a local interface and processes flows for AI/ML.
    """
    def __init__(self, iface=None, filter_expr=None):
        self.iface = iface
        self.filter_expr = filter_expr
        self.flows = defaultdict(lambda: PacketFlow(None))
        self.sniffer = None
        self.running = False
        self.lock = threading.Lock()

    def _packet_callback(self, pkt):
        key = extract_five_tuple(pkt)
        if key:
            with self.lock:
                if self.flows[key].five_tuple is None:
                    self.flows[key] = PacketFlow(key)
                self.flows[key].add_packet(pkt)

    def start(self, timeout=30):
        self.sniffer = AsyncSniffer(prn=self._packet_callback, iface=self.iface, filter=self.filter_expr, store=False)
        self.sniffer.start()
        self.running = True
        logging.info("Started packet sniffer on interface %s", self.iface)
        try:
            time.sleep(timeout)
        except KeyboardInterrupt:
            pass
        self.stop()

    def stop(self):
        if self.running and self.sniffer:
            self.sniffer.stop()
            logging.info("Stopped packet sniffer.")
            self.running = False

    def get_flow_features(self):
        """Returns all flows as a DataFrame, ready for ML."""
        with self.lock:
            data = [f.to_features() for f in self.flows.values() if f.five_tuple]
            return pd.DataFrame(data)

def sniff(timeout=30, iface=None, filter_expr=None, output_csv=None):
    """
    Main sniffer entry-point. Collect packets, extract ML-usable features, and return as DataFrame. 
    Optionally saves to CSV for AI pipelines.
    """
    logging.info("Active packets sniffer")
    sniffer = PcapSniffer(iface=iface, filter_expr=filter_expr)
    sniffer.start(timeout=timeout)
    df = sniffer.get_flow_features()
    if output_csv:
        df.to_csv(output_csv, index=False)
        logging.info(f"Saved flow features to {output_csv}")
    return df

# Example usage:
# df = sniff(timeout=10, iface="eth0", filter_expr="tcp port 443", output_csv="flows.csv")

