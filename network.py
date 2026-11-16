import os
import time
import socket
import ctypes
from ctypes import wintypes
import requests
import pycountry
from config import FLAGS_DIR

COUNTRY_OVERRIDES = {
    "RU": "RUS",
    "US": "USA",
    "GB": "GBR",
    "DE": "DEU",
    "NL": "NLD",
    "FI": "FIN",
    "KZ": "KAZ",
    "BY": "BLR",
    "TR": "TUR",
    "AE": "ARE",
}

WIN_CITY_FIXES = {
    "krasnogvardeiskii": "Saint Petersburg",
    "krasnogvardeyskiy": "Saint Petersburg",
}


class _IP_ADAPTER_UNICAST_ADDRESS_LH(ctypes.Structure):
    pass


class _SOCKET_ADDRESS(ctypes.Structure):
    _fields_ = [
        ("lpSockaddr", ctypes.c_void_p),
        ("iSockaddrLength", ctypes.c_int),
    ]


_IP_ADAPTER_UNICAST_ADDRESS_LH._fields_ = [
    ("Length", wintypes.ULONG),
    ("Flags", wintypes.DWORD),
    ("Next", ctypes.POINTER(_IP_ADAPTER_UNICAST_ADDRESS_LH)),
    ("Address", _SOCKET_ADDRESS),
]


class _IP_ADAPTER_ADDRESSES_LH(ctypes.Structure):
    pass


_IP_ADAPTER_ADDRESSES_LH._fields_ = [
    ("Length", wintypes.ULONG),
    ("IfIndex", wintypes.DWORD),
    ("Next", ctypes.POINTER(_IP_ADAPTER_ADDRESSES_LH)),
    ("AdapterName", ctypes.c_char_p),
    ("FirstUnicastAddress", ctypes.POINTER(_IP_ADAPTER_UNICAST_ADDRESS_LH)),
    ("FirstAnycastAddress", ctypes.c_void_p),
    ("FirstMulticastAddress", ctypes.c_void_p),
    ("FirstDnsServerAddress", ctypes.c_void_p),
    ("DnsSuffix", wintypes.LPWSTR),
    ("Description", wintypes.LPWSTR),
    ("FriendlyName", wintypes.LPWSTR),
]


def _resolve_adapter_friendly_name(local_ip: str) -> str:
    """Находит FriendlyName сетевого адаптера Windows по локальному IPv4."""
    try:
        iphlpapi = ctypes.windll.iphlpapi
        AF_INET = 2
        GAA_FLAG_SKIP_ANYCAST = 0x0002
        GAA_FLAG_SKIP_MULTICAST = 0x0004
        GAA_FLAG_SKIP_DNS_SERVER = 0x0008
        flags = GAA_FLAG_SKIP_ANYCAST | GAA_FLAG_SKIP_MULTICAST | GAA_FLAG_SKIP_DNS_SERVER

        buf_len = wintypes.ULONG(15000)
        buf = ctypes.create_string_buffer(buf_len.value)
        ret = iphlpapi.GetAdaptersAddresses(AF_INET, flags, None, buf, ctypes.byref(buf_len))
        if ret == 111:  # ERROR_BUFFER_OVERFLOW
            buf = ctypes.create_string_buffer(buf_len.value)
            ret = iphlpapi.GetAdaptersAddresses(AF_INET, flags, None, buf, ctypes.byref(buf_len))
        if ret != 0:
            return ""

        curr = ctypes.cast(buf, ctypes.POINTER(_IP_ADAPTER_ADDRESSES_LH))
        while curr:
            adapter = curr.contents
            u_curr = adapter.FirstUnicastAddress
            while u_curr:
                u_addr = u_curr.contents
                if u_addr.Address.lpSockaddr and u_addr.Address.iSockaddrLength >= 8:
                    raw = (ctypes.c_ubyte * 8).from_address(u_addr.Address.lpSockaddr)
                    ip_str = f"{raw[4]}.{raw[5]}.{raw[6]}.{raw[7]}"
                    if ip_str == local_ip:
                        return adapter.FriendlyName or adapter.Description or ""
                u_curr = u_addr.Next
            curr = adapter.Next
    except Exception:
        pass
    return ""


def get_active_interface_info() -> str:
    """Возвращает строку вида 'Tailscale (100.84.12.5)' или локальный IP."""
    local_ip = ""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("1.1.1.1", 80))
            local_ip = s.getsockname()[0]
    except Exception:
        return ""

    if not local_ip:
        return ""

    friendly = _resolve_adapter_friendly_name(local_ip)
    if friendly:
        if len(friendly) > 22:
            friendly = friendly[:21] + "…"
        return f"{friendly} ({local_ip})"
    return local_ip


def iso2_to_iso3(iso2: str) -> str:
    if not iso2:
        return "UNK"
    code = iso2.strip().upper()
    if code in COUNTRY_OVERRIDES:
        return COUNTRY_OVERRIDES[code]
    try:
        country = pycountry.countries.get(alpha_2=code)
        if country and hasattr(country, "alpha_3"):
            return country.alpha_3
    except Exception:
        pass
    return code


def normalize_city(city: str) -> str:
    if not city:
        return ""
    clean = city.strip()
    return WIN_CITY_FIXES.get(clean.lower(), clean)


def ensure_flag_png(iso2: str) -> str:
    if not iso2 or len(iso2) != 2:
        return ""
    code = iso2.lower()
    os.makedirs(FLAGS_DIR, exist_ok=True)

    for ext in ("png", "svg"):
        cached = os.path.join(FLAGS_DIR, f"{code}.{ext}")
        if os.path.exists(cached) and os.path.getsize(cached) > 100:
            return cached

    sources = [
        ("png", f"https://flagcdn.com/w40/{code}.png"),
        ("svg", f"https://cdn.jsdelivr.net/gh/lipis/flag-icons@main/flags/4x3/{code}.svg"),
        ("svg", f"https://raw.githubusercontent.com/lipis/flag-icons/main/flags/4x3/{code}.svg"),
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) IPWidget/0.4.4"}

    for ext, url in sources:
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            content = resp.content
            if resp.status_code != 200 or len(content) <= 100:
                continue
            # Отсекаем HTML-страницы блокировок/ошибок
            head = content[:64].lstrip().lower()
            if head.startswith(b"<!doctype") or head.startswith(b"<html"):
                continue

            flag_path = os.path.join(FLAGS_DIR, f"{code}.{ext}")
            with open(flag_path, "wb") as f:
                f.write(content)
            return flag_path
        except Exception:
            continue
    return ""

def _parse_response(data: dict) -> tuple[str, str, str, str, str]:
    if data.get("status") == "fail":
        return "", "", "", "", ""
    if "success" in data and data.get("success") is False:
        return "", "", "", "", ""

    ip = data.get("ip") or data.get("query") or ""
    iso2 = data.get("country_code") or data.get("countryCode") or data.get("country") or ""
    city = data.get("city") or ""

    isp = ""
    conn = data.get("connection")
    if isinstance(conn, dict):
        isp = conn.get("isp") or conn.get("org") or ""
    if not isp:
        isp = data.get("isp") or data.get("organization_name") or data.get("org") or ""

    tz = ""
    tz_obj = data.get("timezone")
    if isinstance(tz_obj, dict):
        tz = tz_obj.get("id") or ""
    elif isinstance(tz_obj, str):
        tz = tz_obj

    return str(ip).strip(), str(iso2).strip(), normalize_city(str(city)), str(isp).strip(), str(tz).strip()


def fetch_ip_info(api_urls: list) -> dict | None:
    headers = {"User-Agent": "IPWidget/0.4.4"}
    for url in api_urls:
        try:
            t0 = time.perf_counter()
            resp = requests.get(url, headers=headers, timeout=5)
            ping_ms = int(round((time.perf_counter() - t0) * 1000))
            if resp.status_code != 200:
                continue
            data = resp.json()
            ip, iso2, city, isp, tz = _parse_response(data)
            if ip and iso2:
                return {
                    "ip": ip,
                    "iso2": iso2.upper(),
                    "alpha3": iso2_to_iso3(iso2),
                    "city": city,
                    "isp": isp,
                    "timezone": tz,
                    "ping_ms": ping_ms,
                    "iface": get_active_interface_info(),
                    "flag_path": ensure_flag_png(iso2),
                }
        except Exception:
            continue
    return None