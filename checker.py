"""
checker.py  –  проверяет работоспособность VPN конфигов через xray-core.

Алгоритм для каждого конфига:
  1. Генерируем xray JSON config с SOCKS-inbound на случайном порту.
  2. Запускаем xray как subprocess.
  3. Пробуем HTTP-запрос через SOCKS5 к TEST_URL.
  4. Фиксируем задержку (ms). Убиваем xray.

Конфиги тестируются параллельно через ThreadPoolExecutor.
"""

import json
import logging
import os
import random
import socket
import subprocess
import tempfile
import threading
import time
import urllib.parse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

import requests
import socks  # PySocks

import config as cfg

logger = logging.getLogger(__name__)

_port_lock = threading.Lock()
_used_ports: set[int] = set()


def _get_free_port() -> int:
    with _port_lock:
        for _ in range(1000):
            port = random.randint(cfg.SOCKS_BASE_PORT, cfg.SOCKS_BASE_PORT + 10000)
            if port not in _used_ports:
                _used_ports.add(port)
                return port
    raise RuntimeError("No free ports")


def _release_port(port: int) -> None:
    with _port_lock:
        _used_ports.discard(port)


# ── Генерация xray конфига ────────────────────────────────────────────────────

def _parse_vmess(uri: str) -> Optional[dict]:
    try:
        b64 = uri[len("vmess://"):]
        padded = b64 + "=" * (-len(b64) % 4)
        v = json.loads(base64.b64decode(padded).decode())
        net   = v.get("net", "tcp")
        tls   = v.get("tls", "")
        host  = v.get("host", v.get("add", ""))
        path  = v.get("path", "/")
        sni   = v.get("sni", host)

        stream: dict = {"network": net}
        if net == "ws":
            stream["wsSettings"] = {"path": path, "headers": {"Host": host}}
        elif net == "grpc":
            stream["grpcSettings"] = {"serviceName": v.get("path", "")}
        elif net == "h2":
            stream["httpSettings"] = {"host": [host], "path": path}

        if tls in ("tls", "xtls"):
            stream["security"] = "tls"
            stream["tlsSettings"] = {"serverName": sni, "allowInsecure": True}
        elif tls == "reality":
            stream["security"] = "reality"
            stream["realitySettings"] = {
                "serverName": sni,
                "fingerprint": v.get("fp", "chrome"),
                "publicKey": v.get("pbk", ""),
                "shortId": v.get("sid", ""),
            }

        return {
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": v.get("add", ""),
                    "port": int(v.get("port", 443)),
                    "users": [{"id": v.get("id", ""), "security": v.get("scy", "auto")}],
                }]
            },
            "streamSettings": stream,
        }
    except Exception as e:
        logger.debug("vmess parse error: %s", e)
        return None


def _parse_vless(uri: str) -> Optional[dict]:
    try:
        p = urllib.parse.urlparse(uri)
        params = dict(urllib.parse.parse_qsl(p.query))
        net     = params.get("type", "tcp")
        sec     = params.get("security", "none")
        sni     = params.get("sni", p.hostname or "")
        path    = params.get("path", "/")
        host    = params.get("host", sni)
        flow    = params.get("flow", "")

        stream: dict = {"network": net}
        if net == "ws":
            stream["wsSettings"] = {"path": path, "headers": {"Host": host}}
        elif net == "grpc":
            stream["grpcSettings"] = {"serviceName": params.get("serviceName", "")}
        elif net == "h2":
            stream["httpSettings"] = {"host": [host], "path": path}

        if sec == "tls":
            stream["security"] = "tls"
            stream["tlsSettings"] = {"serverName": sni, "allowInsecure": True}
        elif sec == "reality":
            stream["security"] = "reality"
            stream["realitySettings"] = {
                "serverName": sni,
                "fingerprint": params.get("fp", "chrome"),
                "publicKey": params.get("pbk", ""),
                "shortId": params.get("sid", ""),
            }
        elif sec == "xtls":
            stream["security"] = "xtls"
            stream["xtlsSettings"] = {"serverName": sni, "allowInsecure": True}

        user: dict = {"id": p.username or "", "encryption": "none"}
        if flow:
            user["flow"] = flow

        return {
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": p.hostname or "",
                    "port": p.port or 443,
                    "users": [user],
                }]
            },
            "streamSettings": stream,
        }
    except Exception as e:
        logger.debug("vless parse error: %s", e)
        return None


def _parse_trojan(uri: str) -> Optional[dict]:
    try:
        p = urllib.parse.urlparse(uri)
        params = dict(urllib.parse.parse_qsl(p.query))
        net = params.get("type", "tcp")
        sni = params.get("sni", p.hostname or "")
        path = params.get("path", "/")
        host = params.get("host", sni)

        stream: dict = {"network": net, "security": "tls",
                        "tlsSettings": {"serverName": sni, "allowInsecure": True}}
        if net == "ws":
            stream["wsSettings"] = {"path": path, "headers": {"Host": host}}
        elif net == "grpc":
            stream["grpcSettings"] = {"serviceName": params.get("serviceName", "")}

        return {
            "protocol": "trojan",
            "settings": {
                "servers": [{
                    "address": p.hostname or "",
                    "port": p.port or 443,
                    "password": p.username or "",
                }]
            },
            "streamSettings": stream,
        }
    except Exception as e:
        logger.debug("trojan parse error: %s", e)
        return None


def _parse_ss(uri: str) -> Optional[dict]:
    try:
        rest = uri[len("ss://"):]
        rest = rest.split("#")[0].strip()
        if "@" in rest:
            userinfo, hostport = rest.rsplit("@", 1)
            try:
                dec = base64.b64decode(userinfo + "==").decode()
                method, password = dec.split(":", 1)
            except Exception:
                method, password = userinfo.split(":", 1)
        else:
            dec = base64.b64decode(rest + "==").decode()
            method_pw, hostport = dec.split("@")
            method, password = method_pw.split(":", 1)

        if ":" in hostport:
            host, port_s = hostport.rsplit(":", 1)
            port = int(port_s.split("/")[0].split("?")[0])
        else:
            return None

        return {
            "protocol": "shadowsocks",
            "settings": {
                "servers": [{
                    "address": host,
                    "port": port,
                    "method": method,
                    "password": password,
                }]
            },
        }
    except Exception as e:
        logger.debug("ss parse error: %s", e)
        return None


def _parse_hysteria2(uri: str) -> Optional[dict]:
    try:
        p = urllib.parse.urlparse(uri)
        params = dict(urllib.parse.parse_qsl(p.query))
        sni = params.get("sni", p.hostname or "")
        return {
            "protocol": "hysteria2",
            "settings": {
                "servers": [{
                    "address": p.hostname or "",
                    "port": p.port or 443,
                    "password": p.username or p.password or "",
                    "sni": sni,
                    "insecure": True,
                }]
            },
        }
    except Exception as e:
        logger.debug("hy2 parse error: %s", e)
        return None


def _build_xray_config(outbound: dict, socks_port: int) -> dict:
    return {
        "log": {"loglevel": "none"},
        "inbounds": [{
            "tag": "socks-in",
            "protocol": "socks",
            "listen": "127.0.0.1",
            "port": socks_port,
            "settings": {"auth": "noauth", "udp": False},
        }],
        "outbounds": [
            {**outbound, "tag": "proxy"},
            {"protocol": "freedom", "tag": "direct"},
        ],
        "routing": {
            "rules": [{"type": "field", "outboundTag": "proxy", "inboundTag": ["socks-in"]}]
        },
    }


def _uri_to_outbound(uri: str) -> Optional[dict]:
    scheme = uri.split("://")[0].lower()
    if scheme == "vmess":
        return _parse_vmess(uri)
    elif scheme == "vless":
        return _parse_vless(uri)
    elif scheme == "trojan":
        return _parse_trojan(uri)
    elif scheme == "ss":
        return _parse_ss(uri)
    elif scheme in ("hysteria2", "hy2"):
        return _parse_hysteria2(uri)
    return None


# ── Тест одного конфига ────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    uri:     str
    ok:      bool
    latency: int = 0   # ms


def check_one(uri: str) -> CheckResult:
    outbound = _uri_to_outbound(uri)
    if outbound is None:
        return CheckResult(uri, False)

    port = _get_free_port()
    xray_cfg = _build_xray_config(outbound, port)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(xray_cfg, f)
        tmpfile = f.name

    proc = None
    try:
        proc = subprocess.Popen(
            [cfg.XRAY_PATH, "run", "-c", tmpfile],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1.2)  # даём xray стартовать

        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, "127.0.0.1", port)
        s.settimeout(cfg.CHECK_TIMEOUT)

        t0 = time.monotonic()
        try:
            s.connect(("www.gstatic.com", 80))
            s.sendall(b"GET /generate_204 HTTP/1.0\r\nHost: www.gstatic.com\r\n\r\n")
            data = s.recv(64)
            latency = int((time.monotonic() - t0) * 1000)
            ok = b"204" in data or b"200" in data
        except Exception:
            ok = False
            latency = 0
        finally:
            s.close()

        return CheckResult(uri, ok, latency)
    except Exception as e:
        logger.debug("check error for %s: %s", uri[:60], e)
        return CheckResult(uri, False)
    finally:
        if proc:
            proc.kill()
            proc.wait()
        try:
            os.unlink(tmpfile)
        except OSError:
            pass
        _release_port(port)


# ── Проверка списка конфигов ───────────────────────────────────────────────────

def check_all(
    uris: list[str],
    max_workers: int = cfg.MAX_WORKERS,
    progress_cb=None,        # callable(done: int, total: int)
) -> list[CheckResult]:
    """Проверяет все конфиги параллельно. Возвращает список результатов."""
    results: list[CheckResult] = []
    total = len(uris)
    done  = 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(check_one, uri): uri for uri in uris}
        for fut in as_completed(futures):
            result = fut.result()
            results.append(result)
            done += 1
            if progress_cb:
                try:
                    progress_cb(done, total)
                except Exception:
                    pass

    # Сортируем: сначала рабочие по задержке
    results.sort(key=lambda r: (not r.ok, r.latency))
    return results
