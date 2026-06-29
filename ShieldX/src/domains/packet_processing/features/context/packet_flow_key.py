#!/usr/bin/env python


from scapy.layers.inet import IP
from scapy.layers.inet6 import IPv6

from . import packet_direction


def _get_ip_layer(packet):
    if IPv6 in packet:
        return packet[IPv6]
    return packet[IP]


def get_packet_flow_key(packet, direction) -> tuple:
    """Creates a key signature for a packet.

    Summary:
        Creates a key signature for a packet so it can be
        assigned to a flow.

    Args:
        packet: A network packet
        direction: The direction of a packet

    Returns:
        A tuple of the String IP addresses of the destination,
        the source port as an int,
        the time to live value,
        the window size, and
        TCP flags.

    """
    if 'TCP' in packet:
        protocol = 'TCP'
    elif 'UDP' in packet:
        protocol = 'UDP'
    else:
        raise Exception('Only TCP protocols are supported.')

    ip_layer = _get_ip_layer(packet)

    if direction == packet_direction.PacketDirection.FORWARD:
        dest_ip = ip_layer.dst
        src_ip = ip_layer.src
        src_port = packet[protocol].sport
        dest_port = packet[protocol].dport
    else:
        dest_ip = ip_layer.src
        src_ip = ip_layer.dst
        src_port = packet[protocol].dport
        dest_port = packet[protocol].sport

    return dest_ip, src_ip, src_port, dest_port
