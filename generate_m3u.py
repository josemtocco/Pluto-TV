#!/usr/bin/env python3
"""
Pluto TV Brasil - Gerador M3U com Redirecionador Cloudflare (SS IPTV)
Gera URLs CURTAS que passam pelo Worker do Cloudflare.
"""
import json
import os
import sys
import uuid
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests

# ── Configuração ──────────────────────────────────────────────────────────────
REGION = "br"
BR_IP = "177.192.255.38"
MAX_FAILS = 3
CHECK_STREAMS = os.environ.get("CHECK_STREAMS", "0") == "1"

# ⚠️ IMPORTANTE: Substitua pela URL do SEU Cloudflare Worker
REDIRECTOR_BASE_URL = os.environ.get(
    "REDIRECTOR_BASE_URL",
    "https://restless-resonance-dba9.bepigaucho.workers.dev"
)

STATE_FILE = Path("state.json")
OUTPUT_M3U = Path("pluto_br.m3u")
BOOT_URL = "https://boot.pluto.tv/v4/start"
CHANNELS_URL = "https://service-channels.clusters.pluto.tv/v2/guide/channels"
CATEGORIES_URL = "https://service-channels.clusters.pluto.tv/v2/guide/categories"
TIMEOUT = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/133.0.0.0 Safari/537.36"
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"channels": {}, "last_update": None}

def save_state(state: Dict[str, Any]) -> None:
    state["last_update"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def boot_session() -> Optional[Dict[str, Any]]:
    """Obtém sessionToken via boot.pluto.tv"""
    device_id = str(uuid.uuid4())
    params = {
        "appName": "web",
        "appVersion": "8.1.0",
        "deviceVersion": "133.0.0",
        "deviceModel": "web",
        "deviceMake": "chrome",
        "deviceType": "web",
        "clientID": device_id,
        "clientModelNumber": "1.0.0",
        "serverSideAds": "false",
        "architecture": "x86_64",
        "buildVersion": "1.0.0",
        "drmCapabilities": "widevine:L3",
    }
    headers = {
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://pluto.tv",
        "Referer": "https://pluto.tv/",
        "User-Agent": USER_AGENT,
        "X-Forwarded-For": BR_IP,
    }
    try:
        r = requests.get(BOOT_URL, params=params, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if not data.get("sessionToken"):
            print("ERRO: boot não retornou sessionToken", file=sys.stderr)
            return None
        return {
            "token": data["sessionToken"],
            "stitcher": data.get("servers", {}).get(
                "stitcher", "https://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv"
            ),
            "device_id": device_id,
        }
    except Exception as e:
        print(f"ERRO no boot: {e}", file=sys.stderr)
        return None

def fetch_channels(session: Dict[str, Any]) -> List[Dict[str, Any]]:
    headers = {
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Authorization": f"Bearer {session['token']}",
        "Origin": "https://pluto.tv",
        "Referer": "https://pluto.tv/",
        "User-Agent": USER_AGENT,
        "X-Forwarded-For": BR_IP,
    }
    params = {"channelIds": "", "offset": "0", "limit": "1000", "sort": "number:asc"}
    try:
        r = requests.get(CHANNELS_URL, params=params, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print(f"ERRO ao buscar canais: {e}", file=sys.stderr)
        return []

def fetch_categories(session: Dict[str, Any]) -> Dict[str, str]:
    headers = {
        "Accept": "*/*",
        "Authorization": f"Bearer {session['token']}",
        "Origin": "https://pluto.tv",
        "Referer": "https://pluto.tv/",
        "User-Agent": USER_AGENT,
        "X-Forwarded-For": BR_IP,
    }
    try:
        r = requests.get(CATEGORIES_URL, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        cats = r.json().get("data", [])
        mapping = {}
        for cat in cats:
            name = cat.get("name") or cat.get("slug") or "Geral"
            for ch in cat.get("channelIDs", []) or cat.get("channels", []):
                cid = ch if isinstance(ch, str) else ch.get("id") or ch.get("_id")
                if cid:
                    mapping[str(cid)] = name
        return mapping
    except Exception as e:
        print(f"Aviso: categorias não carregadas ({e})", file=sys.stderr)
        return {}

def build_short_url(channel_id: str, jwt_token: str) -> str:
    """
    Gera URL CURTA para o Cloudflare Worker.
    Formato: https://worker.workers.dev/?id=CHANNEL_ID&jwt=TOKEN
    """
    encoded_jwt = urllib.parse.quote(jwt_token, safe='')
    return f"{REDIRECTOR_BASE_URL}/?id={channel_id}&jwt={encoded_jwt}"

def build_long_url(session: Dict[str, Any], channel: Dict[str, Any]) -> Optional[str]:
    """Gera URL longa completa (apenas para verificação de stream)"""
    cid = channel.get("id") or channel.get("_id")
    if not cid:
        return None
    base = session["stitcher"].rstrip("/")
    device_id = session["device_id"]
    query = (
        f"appName=web&appVersion=8.1.0"
        f"&clientID={device_id}&deviceId={device_id}"
        f"&deviceMake=chrome&deviceModel=web&deviceType=web&deviceVersion=133.0.0"
        f"&country=BR&marketingRegion=BR&serverSideAds=false"
        f"&jwt={session['token']}&masterJWTPassthrough=true"
    )
    return f"{base}/v2/stitch/hls/channel/{cid}/master.m3u8?{query}"

def check_stream(url: str, timeout: int = 5) -> bool:
    headers = {"User-Agent": USER_AGENT, "Range": "bytes=0-1023"}
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        if r.status_code < 400:
            return True
    except Exception:
        pass
    try:
        r = requests.get(url, timeout=timeout, stream=True, headers=headers)
        ok = r.status_code < 400
        r.close()
        return ok
    except Exception:
        return False

def get_logo(channel: Dict[str, Any]) -> str:
    images = channel.get("images") or []
    preferred = ("colorLogoPNG", "logo", "solidLogoPNG", "featuredImage", "hero")
    for ptype in preferred:
        for img in images:
            if isinstance(img, dict) and img.get("type") == ptype and img.get("url"):
                return img["url"]
    for key in ("colorLogoPNG", "logo", "featuredImage"):
        logo = channel.get(key)
        if isinstance(logo, dict):
            url = logo.get("path") or logo.get("url")
            if url:
                return url
        elif logo:
            return str(logo)
    return ""

def normalize_group(name: str) -> str:
    if not name:
        return "Pluto TV"
    n = name.strip()
    mapping = {
        "Movies": "Filmes", "Movie": "Filmes", "Series": "Séries",
        "Entertainment": "Entretenimento", "Kids": "Infantil", "News": "Notícias",
        "Sports": "Esportes", "Music": "Música", "Documentary": "Documentários",
        "Comedy": "Comédia", "Lifestyle": "Estilo de Vida", "Reality": "Reality",
    }
    for en, pt in mapping.items():
        if en.lower() in n.lower():
            return f"Pluto TV | {pt}"
    return f"Pluto TV | {n}"

def generate_m3u(channels: List[Dict[str, Any]], categories: Dict[str, str]) -> str:
    lines = [
        "#EXTM3U",
        '#EXT-X-SESSION-DATA:DATA-ID="com.xui.note",VALUE="Pluto TV Brasil - Redirecionador Cloudflare"',
        f"# Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"# Redirector: {REDIRECTOR_BASE_URL}",
        "",
    ]
    for ch in channels:
        cid = str(ch.get("id") or ch.get("_id") or "")
        name = (ch.get("name") or ch.get("slug") or "Canal").strip()
        logo = get_logo(ch)
        group = normalize_group(categories.get(cid, ch.get("category") or "Geral"))
        number = ch.get("number") or ""
        
        # Pega a URL CURTA gerada
        stream = ch.get("_short_url")
        if not stream:
            continue

        attrs = [f'tvg-id="{cid}"', f'tvg-name="{name}"']
        if logo:
            attrs.append(f'tvg-logo="{logo}"')
        if number:
            attrs.append(f'tvg-chno="{number}"')
        attrs.append(f'group-title="{group}"')
        
        lines.append(f'#EXTINF:-1 {" ".join(attrs)},{name}')
        lines.append(stream)
        lines.append("")
    return "\n".join(lines)

def main() -> int:
    print("=== Pluto TV BR → M3U (Redirecionador Cloudflare) ===")
    print(f"Região: {REGION.upper()} | IP spoof: {BR_IP}")
    print(f"Redirecionador: {REDIRECTOR_BASE_URL}")
    
    session = boot_session()
    if not session:
        print("Falha no boot da sessão. Abortando.")
        return 1
    print("✓ Sessão obtida com sucesso.")
    
    raw_channels = fetch_channels(session)
    if not raw_channels:
        print("Nenhum canal retornado pela API.")
        return 1
    print(f"✓ Canais recebidos: {len(raw_channels)}")
    
    categories = fetch_categories(session)
    print(f"✓ Categorias mapeadas: {len(categories)}")
    
    state = load_state()
    prev = state.get("channels", {})
    current_ids = set()
    healthy: List[Dict[str, Any]] = []
    
    for ch in raw_channels:
        cid = str(ch.get("id") or ch.get("_id") or "")
        if not cid:
            continue
        current_ids.add(cid)
        
        # Gera URL CURTA (para o M3U final)
        short_url = build_short_url(cid, session["token"])
        
        if CHECK_STREAMS:
            # Gera URL LONGA apenas para teste
            long_url = build_long_url(session, ch)
            if long_url:
                is_ok = check_stream(long_url)
                if not is_ok:
                    entry = prev.get(cid, {"fails": 0})
                    fails = entry.get("fails", 0) + 1
                    if fails >= MAX_FAILS:
                        print(f"  ✗ Removendo (falhou {fails}x): {ch.get('name')}")
                        continue
                    print(f"  ! Mantendo com {fails} falha(s): {ch.get('name')}")
                    ch["_short_url"] = short_url
                    ch["_fails"] = fails
                    healthy.append(ch)
                    prev[cid] = {
                        "name": ch.get("name"),
                        "fails": fails,
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                    }
                    continue
        
        ch["_short_url"] = short_url
        ch["_fails"] = 0
        healthy.append(ch)
        prev[cid] = {
            "name": ch.get("name"),
            "fails": 0,
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }

    # Manter canais antigos que sumiram
    for cid, entry in list(prev.items()):
        if cid in current_ids:
            continue
        fails = entry.get("fails", 0) + 1
        if fails >= MAX_FAILS:
            print(f"  ✗ Removendo antigo (sumiu {fails}x): {entry.get('name')}")
            del prev[cid]
            continue
        print(f"  ! Mantendo antigo com {fails} falha(s): {entry.get('name')}")
        # Gera URL curta para canal antigo (usando token atual)
        short_url = build_short_url(cid, session["token"])
        ghost = {
            "id": cid,
            "name": entry.get("name", cid),
            "_short_url": short_url,
            "_fails": fails,
        }
        healthy.append(ghost)
        prev[cid] = {**entry, "fails": fails, "last_seen": entry.get("last_seen")}

    def sort_key(c):
        num = c.get("number")
        try:
            return (0, int(num))
        except (TypeError, ValueError):
            return (1, (c.get("name") or "").lower())
    
    healthy.sort(key=sort_key)
    
    state["channels"] = prev
    save_state(state)
    
    m3u_content = generate_m3u(healthy, categories)
    OUTPUT_M3U.write_text(m3u_content, encoding="utf-8")
    print(f"\n✓ M3U gerado: {OUTPUT_M3U} ({len(healthy)} canais)")
    print(f"✓ Estado salvo: {STATE_FILE}")
    
    if healthy:
        sample = healthy[0].get("_short_url", "")
        print(f"\n📋 Exemplo de URL CURTA gerada:")
        print(f"   {sample}")
        print(f"\n   Tamanho: {len(sample)} caracteres")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())