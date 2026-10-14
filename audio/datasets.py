"""Dataset manifest, local registry, download attempts and status reporting.

Principles: never invent file URLs, never silently substitute synthetic audio for a failed download.
 * data/manifest.json   - public SOURCES (collections) with source URL, attribution and licence notes.
 * data/local_registry.json - individual audio FILES the user (or a successful download) registered,
                              each with label, source URL, sampling rate, format, attribution, licence.
 * data/download_status.json - result of every download attempt (success or the exact error).
"""
from __future__ import annotations
import hashlib, json, time, urllib.request, urllib.error
from pathlib import Path
from audio.io import load_wav_bytes, AudioError

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SAMPLES = DATA / "samples"
MANIFEST = DATA / "manifest.json"
REGISTRY = DATA / "local_registry.json"
STATUS = DATA / "download_status.json"

DEFAULT_MANIFEST = {"sources": [
    {"id": "noaa_fisheries_sounds", "name": "NOAA Fisheries - Sounds in the Ocean: Environmental and Anthropogenic",
     "page_url": "https://www.fisheries.noaa.gov/national/science-data/sounds-ocean-environmental-and-anthropogenic",
     "fetch": "manual", "categories": ["vessel", "ambient", "impulsive", "biological"],
     "licence": "Not verified automatically. Read the usage statement on the source page before redistributing.",
     "attribution": "NOAA Fisheries (cite the specific page and file you use).",
     "howto": "Open the page, download the example WAV/MP3-to-WAV files you want, then register each file in the app (Acoustic Data Explorer -> Register local file) or with scripts/register_local_file.py."},
    {"id": "noaa_ncei_pad", "name": "NOAA NCEI Passive Acoustic Data Archive",
     "page_url": "https://www.ncei.noaa.gov/products/passive-acoustic-data",
     "fetch": "manual", "categories": ["ambient", "vessel", "biological", "impulsive"],
     "licence": "Not verified automatically. Check dataset-level metadata/licence at NCEI.",
     "attribution": "NOAA National Centers for Environmental Information, Passive Acoustic Data Archive.",
     "howto": "Archive files are large. Browse https://www.ncei.noaa.gov/maps/passive-acoustic-data/ , download ONE short clip, and register it."},
    {"id": "noaa_pad_viewer", "name": "NOAA Passive Acoustic Data Viewer", "page_url": "https://www.ncei.noaa.gov/maps/passive-acoustic-data/",
     "fetch": "manual", "categories": [], "licence": "Viewer only; see archive entry.", "attribution": "NOAA NCEI.",
     "howto": "Use to locate datasets; not a direct file source."},
    {"id": "openwhistle", "name": "OpenWhistle (bottlenose dolphin whistles)", "page_url": "https://sumbre-lab.github.io/openwhistle/",
     "fetch": "hf_stream", "hf_repo": "dolphinteam/OpenWhistle-CNN", "categories": ["biological"],
     "licence": "Not verified automatically. Check the Hugging Face dataset card.",
     "attribution": "OpenWhistle project (Sumbre lab); Hugging Face dolphinteam/OpenWhistle-CNN.",
     "howto": "Needs internet and the optional 'datasets' package: python scripts/download_openwhistle_samples.py"}]}


def _read(p, default):
    try:
        return json.loads(Path(p).read_text())
    except FileNotFoundError:
        return default
    except Exception:
        return default


def load_manifest():
    return _read(MANIFEST, DEFAULT_MANIFEST)


def write_default_manifest():
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(DEFAULT_MANIFEST, indent=2))


def load_registry():
    return _read(REGISTRY, {"files": []})


def _save_registry(r):
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(r, indent=2))


def log_status(source_id, ok, message):
    s = _read(STATUS, {"attempts": []})
    s["attempts"].append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "source": source_id, "ok": bool(ok), "message": message})
    s["attempts"] = s["attempts"][-100:]
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(s, indent=2))


def register_file(path, label, source_url="", attribution="", licence="unknown - verify at source", recording_id=None, source_id=""):
    """Validate a WAV on disk and add it to the registry. Raises AudioError if unreadable."""
    p = Path(path)
    raw = p.read_bytes() if p.exists() else b""
    clip = load_wav_bytes(raw, p.name, "downloaded")
    rel = str(p.resolve().relative_to(ROOT)) if ROOT in p.resolve().parents else str(p.resolve())
    entry = {"path": rel, "label": label, "source_url": source_url, "source_id": source_id, "attribution": attribution,
             "licence": licence, "recording_id": recording_id or p.stem, "format": "WAV", "sampling_rate": clip.fs,
             "duration_s": round(clip.duration_s, 3), "sha256": hashlib.sha256(raw).hexdigest()}
    r = load_registry()
    r["files"] = [f for f in r["files"] if f["path"] != entry["path"]] + [entry]
    _save_registry(r)
    return entry


def registry_status():
    """Rows for the status screen: one per registered file, flagged missing if the file vanished."""
    rows = []
    for f in load_registry()["files"]:
        p = Path(f["path"]); p = p if p.is_absolute() else ROOT / p
        rows.append({**f, "present": p.exists()})
    return rows


def source_status():
    """One row per public SOURCE: how many registered files came from it, and last download attempt."""
    reg = registry_status(); att = _read(STATUS, {"attempts": []})["attempts"]
    out = []
    for s in load_manifest()["sources"]:
        mine = [r for r in reg if r.get("source_id") == s["id"] and r["present"]]
        last = next((a for a in reversed(att) if a["source"] == s["id"]), None)
        out.append({"Source": s["name"], "Fetch method": s["fetch"], "Files available": len(mine),
                    "Last attempt": (("OK: " if last["ok"] else "FAILED: ") + last["message"]) if last else "not attempted",
                    "Page": s["page_url"], "Licence note": s["licence"]})
    return out


def download_url(url, dest, timeout=20, max_bytes=50_000_000):
    """Download one WAV from a DIRECT url (only use URLs you have verified). Returns Path or raises AudioError."""
    dest = Path(dest); dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            raw = r.read(max_bytes + 1)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise AudioError(f"Download failed (no internet or URL unreachable): {e}")
    if len(raw) > max_bytes:
        raise AudioError("File larger than the safety limit; download manually.")
    load_wav_bytes(raw, dest.name)                     # validates before keeping
    dest.write_bytes(raw)
    return dest


def fetch_openwhistle(n_whistle=5, n_noise=2):
    """Use the existing streaming loader; record outcome; register files. Never substitutes synthetic data."""
    from signal_processing.dataset import fetch_openwhistle_samples
    src = next(s for s in load_manifest()["sources"] if s["id"] == "openwhistle")
    try:
        w, n = fetch_openwhistle_samples(n_whistle, n_noise, SAMPLES / "openwhistle")
    except Exception as e:
        log_status("openwhistle", False, str(e)[:300])
        raise AudioError(f"OpenWhistle download failed: {e}")
    for p in sorted((SAMPLES / "openwhistle").glob("*.wav")):
        lab = "biological_dolphin_whistle" if p.name.startswith("whistle") else "openwhistle_non_whistle"
        try:
            register_file(p, lab, src["page_url"], src["attribution"], src["licence"], recording_id=f"openwhistle_{p.stem}", source_id="openwhistle")
        except AudioError as e:
            log_status("openwhistle", False, f"{p.name}: {e}")
    log_status("openwhistle", True, f"{w} whistle + {n} non-whistle clips")
    return w, n


def labelled_items():
    """(samples, fs, label, recording_id) for every present registered file, for supervised training."""
    from audio.io import load_wav_path
    items = []
    for r in registry_status():
        if not r["present"]:
            continue
        p = Path(r["path"]); p = p if p.is_absolute() else ROOT / p
        try:
            c = load_wav_path(p)
            items.append((c.samples, c.fs, r["label"], r["recording_id"]))
        except AudioError:
            continue
    return items
