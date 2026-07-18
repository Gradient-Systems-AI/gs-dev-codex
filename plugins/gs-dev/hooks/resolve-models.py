#!/usr/bin/env python3
"""gs-dev — resolve each agent's tier (L/M/S) to the best AVAILABLE model on this
machine, then install the agents into the user's Codex agents dir.

Robustness: reads ~/.codex/models_cache.json (the authoritative list of models the
installed Codex actually supports) and picks the first candidate per tier that
exists. Never writes an invalid model id; if nothing matches, it omits the model
line so the agent simply inherits the session model. Re-running is idempotent.

Usage: resolve-models.py <src_agents_dir> <dest_agents_dir> <models_cache.json>
"""
import json, os, re, sys

# Per-tier model preference, best -> fallback. First one present in the cache wins.
TIER_PREFS = {
    "L": ["gpt-5.6-sol",  "gpt-5.5",      "gpt-5.4",      "gpt-5-codex"],   # frontier / complex
    "M": ["gpt-5.6-terra", "gpt-5.4",      "gpt-5.5",      "gpt-5-codex"],   # balanced / everyday
    "S": ["gpt-5.6-luna",  "gpt-5.4-mini", "gpt-5.4",      "gpt-5-codex-mini"],  # fast / simple
}
AUTO = "# gs-dev:auto"  # marks a model line this installer manages

def load_cache(path):
    """Return {slug: (set_of_efforts, default_effort)} for every model Codex knows."""
    try:
        data = json.load(open(path))
    except Exception:
        return {}
    out = {}
    for m in data.get("models", []):
        slug = m.get("slug")
        if not slug:
            continue
        efforts = {e["effort"] for e in m.get("supported_reasoning_levels", []) if "effort" in e}
        out[slug] = (efforts, m.get("default_reasoning_level"))
    return out

def pick_model(tier, cache):
    for cand in TIER_PREFS.get(tier, []):
        if cand in cache:
            return cand
    return None

def pick_effort(model, want, cache):
    efforts, default = cache.get(model, (set(), None))
    if not efforts or want in efforts:
        return want
    # clamp toward a supported level: try lower, then the model's own default
    for e in ("high", "medium", "low"):
        if e in efforts:
            return e
    return default or want

def resolve_one(src_text, tier, cache):
    tier_model = pick_model(tier, cache)
    lines = src_text.split("\n")
    # current desired effort from the source
    want_effort = None
    for ln in lines:
        mo = re.match(r'\s*model_reasoning_effort\s*=\s*"([^"]+)"', ln)
        if mo:
            want_effort = mo.group(1)
    out = []
    for ln in lines:
        if re.match(r'\s*model\s*=', ln):
            continue  # drop any existing model line; we re-add below
        if re.match(r'\s*model_reasoning_effort\s*=', ln) and tier_model:
            eff = pick_effort(tier_model, want_effort or "medium", cache)
            out.append(f'model = "{tier_model}"  {AUTO}')
            out.append(f'model_reasoning_effort = "{eff}"')
            continue
        out.append(ln)
    return "\n".join(out), tier_model

def main():
    src, dest, cache_path = sys.argv[1], sys.argv[2], sys.argv[3]
    cache = load_cache(cache_path)
    os.makedirs(dest, exist_ok=True)
    changed = 0
    rows = []
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(".toml"):
            continue
        src_text = open(os.path.join(src, fn)).read()
        m = re.search(r'gs-dev-tier:\s*([LMS])', src_text)
        tier = m.group(1) if m else "M"
        new_text, model = resolve_one(src_text, tier, cache)
        dpath = os.path.join(dest, fn)
        # respect a user override: dest has a model line WITHOUT our AUTO marker
        if os.path.exists(dpath):
            dtext = open(dpath).read()
            if re.search(r'^\s*model\s*=.*(?<!%s)$' % re.escape(AUTO.strip()), dtext, re.M) \
               and AUTO not in dtext and re.search(r'^\s*model\s*=', dtext, re.M):
                rows.append((fn[:-5], tier, "(user override kept)"))
                continue
        if not os.path.exists(dpath) or open(dpath).read() != new_text:
            open(dpath, "w").write(new_text)
            changed += 1
        rows.append((fn[:-5], tier, model or "inherit(session)"))
    print(f"gs-dev: resolved {len(rows)} agents ({changed} written) from {len(cache)} available models")
    for name, tier, model in rows:
        print(f"  {name:26} tier {tier} -> {model}")

if __name__ == "__main__":
    main()
