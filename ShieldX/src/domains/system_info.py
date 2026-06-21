# src/system_info.py
from __future__ import annotations

import getpass
import ipaddress
import platform
from dataclasses import dataclass

import psutil


@dataclass
class SystemInfo:
    hostname: str
    mac_addresses: list[str]
    ip_addresses: list[str]
    username: str
    os_version: str
    kernel: str

    def to_dict(self) -> dict:
        return {
            "hostname": self.hostname,
            "mac_addresses": self.mac_addresses,
            "ip_addresses": self.ip_addresses,
            "username": self.username,
            "os_version": self.os_version,
            "kernel": self.kernel,
        }


def _is_useful_ip(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    return not (
        ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
        or ip.is_reserved
    )


def _is_useful_mac(addr: str) -> bool:
    if not addr:
        return False
    normalized = addr.replace(":", "").replace("-", "").lower()
    return normalized != "0" * 12


def collect_system_info() -> SystemInfo:
    hostname = platform.node()
    os_version = platform.platform()
    kernel = platform.release()
    username = getpass.getuser()

    mac_addresses: list[str] = []
    ip_addresses: list[str] = []

    for _iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK and _is_useful_mac(addr.address):
                mac_addresses.append(addr.address)
            elif addr.family == 2 and _is_useful_ip(addr.address):  # socket.AF_INET
                ip_addresses.append(addr.address)

    return SystemInfo(
        hostname=hostname,
        mac_addresses=mac_addresses,
        ip_addresses=ip_addresses,
        username=username,
        os_version=os_version,
        kernel=kernel,
    )
