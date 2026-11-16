import os
import time
import requests
import pycountry
from config import FLAGS_DIR, APP_NAME, APP_VERSION


def get_alpha3_code(alpha2: str) -> str:
    if not alpha2:
        return "UNK"
    code = alpha2.strip().upper()
    if len(code) == 3:
        return code
    try:
        country = pycountry.countries.get(alpha_2=code)
        if country and hasattr(country, "alpha_3"):
            return country.alpha_3
    except Exception:
        pass
    return code


def download_flag(alpha2: str) -> str:
    if not alpha2:
        return ""
    code = alpha2.strip().lower()
    if len(code) != 2:
        return ""
    os.makedirs(FLAGS_DIR, exist_ok=True)
    flag_path = os.path.join(FLAGS_DIR, f"{code}.png")
    if os.path.exists(flag_path) and os.path.getsize(flag_path) > 0:
        return flag_path
    try:
        url = f"https://flagcdn.com/w40/{code}.png"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and resp.content:
            with open(flag_path, "wb") as f:
                f.write(resp.content)
            return flag_path
    except Exception:
        pass
    return ""


def _parse_api_response(data: dict) -> dict | None:
    if not isinstance(data, dict):
        return None

    # 1. ipwho.is
    if "success" in data:
        if not data.get("success"):
            return None
        ip = data.get("ip", "")
        alpha2 = data.get("country_code", "")
        city = data.get("city", "")
        conn = data.get("connection") or {}
        isp = conn.get("isp") or conn.get("org") or ""
        tz_raw = data.get("timezone")
        timezone = tz_raw.get("id", "") if isinstance(tz_raw, dict) else str(tz_raw or "")
        if ip and alpha2:
            return {"ip": ip, "alpha2": alpha2, "city": city, "isp": isp, "timezone": timezone}

    # 2. ip-api.com
    if data.get("status") == "success":
        ip = data.get("query", "")
        alpha2 = data.get("countryCode", "")
        city = data.get("city", "")
        isp = data.get("isp") or data.get("org") or ""
        timezone = data.get("timezone", "")
        if ip and alpha2:
            return {"ip": ip, "alpha2": alpha2, "city": city, "isp": isp, "timezone": timezone}

    # 3. get.geojs.io
    if "organization_name" in data or ("country_code" in data and "ip" in data and "success" not in data):
        ip = data.get("ip", "")
        alpha2 = data.get("country_code", "")
        city = data.get("city", "")
        isp = data.get("organization_name") or data.get("organization") or ""
        timezone = data.get("timezone", "")
        if ip and alpha2:
            return {"ip": ip, "alpha2": alpha2, "city": city, "isp": isp, "timezone": timezone}

    # 4. ipinfo.io
    if "ip" in data and "country" in data and "success" not in data:
        ip = data.get("ip", "")
        alpha2 = data.get("country", "")
        city = data.get("city", "")
        org = data.get("org", "")
        if org.startswith("AS") and " " in org:
            org = org.split(" ", 1)[1]
        timezone = data.get("timezone", "")
        if ip and alpha2:
            return {"ip": ip, "alpha2": alpha2, "city": city, "isp": org, "timezone": timezone}

    # 5. api.country.is (резервный)
    if "ip" in data and "country" in data:
        ip = data.get("ip", "")
        alpha2 = data.get("country", "")
        if ip and alpha2:
            return {"ip": ip, "alpha2": alpha2, "city": "", "isp": "", "timezone": ""}

    return None


def fetch_ip_info(apis: list) -> dict | None:
    headers = {"User-Agent": f"{APP_NAME}/{APP_VERSION}"}
    for url in apis:
        try:
            start_time = time.perf_counter()
            resp = requests.get(url, headers=headers, timeout=5)
            ping_ms = int(round((time.perf_counter() - start_time) * 1000))

            if resp.status_code == 200:
                parsed = _parse_api_response(resp.json())
                if parsed:
                    alpha2 = parsed["alpha2"].upper()
                    alpha3 = get_alpha3_code(alpha2)
                    flag_path = download_flag(alpha2)
                    return {
                        "ip": parsed["ip"],
                        "alpha2": alpha2,
                        "alpha3": alpha3,
                        "city": (parsed.get("city") or "").strip(),
                        "isp": (parsed.get("isp") or "").strip(),
                        "timezone": (parsed.get("timezone") or "").strip(),
                        "ping_ms": ping_ms,
                        "flag_path": flag_path,
                    }
        except Exception:
            continue
    return None