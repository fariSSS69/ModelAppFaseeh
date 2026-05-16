import os
import sys
import json
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware


ROOT = Path(__file__).resolve().parents[1]

PYTHON_EXE = os.environ.get("FASSEH_PYTHON", sys.executable)

MODEL_PATH = os.environ.get(
    "FASSEH_MODEL",
    str(ROOT / "models" / "fasseh_v2_native_iqraeval_10000_001" / "best")
)

REFS_PATH = os.environ.get(
    "FASSEH_REFS",
    str(ROOT / "outputs" / "v2_native" / "quran_refs_v2_native_full.csv")
)

VOCAB_PATH = os.environ.get(
    "FASSEH_VOCAB",
    str(ROOT / "outputs" / "v2_native" / "vocab_quran_phonemizer_v2_native.json")
)

CONFIG_PATH = os.environ.get(
    "FASSEH_CONFIG",
    str(ROOT / "configs" / "scoring_v2_native_baseline_002_prudent.json")
)

SCORE_SCRIPT = str(ROOT / "scripts" / "score_ayah_v2_native_product.py")
ALIGN_SCRIPT = str(ROOT / "scripts" / "forced_align_v2_reference.py")

RUNTIME_DIR = ROOT / "runtime_demo"
UPLOAD_DIR = RUNTIME_DIR / "uploads"
OUT_DIR = RUNTIME_DIR / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


SOFT_TOKENS = {":", "ŋ"}
VOWELS = {"a", "aa", "i", "ii", "u", "uu"}
SOFT_ONLY = SOFT_TOKENS | VOWELS


app = FastAPI(title="FASSEH V2 Demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_cmd(cmd: List[str]) -> None:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    p = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    if p.returncode != 0:
        raise RuntimeError(
            f"Command failed:\n{' '.join(cmd)}\n\nSTDOUT:\n{p.stdout}\n\nSTDERR:\n{p.stderr}"
        )

def read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_soft_only(tokens: str) -> bool:
    toks = [t for t in tokens.split() if t]
    if not toks:
        return True
    return all(t in SOFT_ONLY for t in toks)


def has_important_consonant(tokens: str) -> bool:
    toks = [t for t in tokens.split() if t]
    return any(t not in SOFT_ONLY for t in toks)


def classify_product_zone(zone: Dict[str, Any]) -> Dict[str, Any]:
    tokens = zone["tokens"]
    severity = zone["severity"]
    count = int(zone["count"])
    min_prob = float(zone["min_prob"]) if zone["min_prob"] is not None else 1.0

    soft_only = is_soft_only(tokens)
    important = has_important_consonant(tokens)

    if tokens.replace(" ", "") == ":":
        product_class = "hide_or_soft"
        msg = "Fin ou durée non prioritaire."
        show = False

    elif soft_only:
        if severity == "strong_check" and count >= 3:
            product_class = "soft_warning"
            msg = "Durée, nasalisation ou fin de récitation à vérifier doucement."
            show = True
        else:
            product_class = "hide_or_soft"
            msg = "Variation douce détectée."
            show = False

    elif important and severity == "strong_check":
        product_class = "important_check"
        msg = "Vérifie cette zone : un son important semble faible ou différent."
        show = True

    elif important and count >= 2 and min_prob < 0.25:
        product_class = "important_check"
        msg = "Vérifie cette courte zone de récitation."
        show = True

    elif important and severity == "check":
        product_class = "light_check"
        msg = "Petite zone à vérifier."
        show = True

    else:
        product_class = "hide_or_soft"
        msg = "Zone peu fiable mais non prioritaire."
        show = False

    zone["product_class"] = product_class
    zone["message"] = msg
    zone["show_to_user"] = show
    return zone


def extract_weak_phonemes(alignment_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    weak = []
    wanted = {"check", "weak", "very_weak", "missing_alignment"}

    for seg in alignment_json.get("reference_phoneme_timings", []):
        if seg.get("quality") not in wanted:
            continue

        start = seg.get("start")
        end = seg.get("end")

        if start is None or end is None:
            continue

        weak.append({
            "ref_index": seg.get("ref_index"),
            "token": seg.get("token"),
            "start": float(start),
            "end": float(end),
            "duration": seg.get("duration"),
            "mean_target_prob": seg.get("mean_target_prob"),
            "quality": seg.get("quality"),
        })

    return weak


def group_weak_zones(weak: List[Dict[str, Any]], gap: float = 0.35) -> List[Dict[str, Any]]:
    weak = sorted(weak, key=lambda x: x["start"])
    zones = []
    cur = None

    for r in weak:
        if cur is None:
            cur = {
                "start": r["start"],
                "end": r["end"],
                "tokens": [r["token"]],
                "ref_indices": [str(r["ref_index"])],
                "qualities": [r["quality"]],
                "min_prob": r.get("mean_target_prob"),
                "count": 1,
            }
            continue

        close = r["start"] - cur["end"] <= gap

        if close:
            cur["end"] = max(cur["end"], r["end"])
            cur["tokens"].append(r["token"])
            cur["ref_indices"].append(str(r["ref_index"]))
            cur["qualities"].append(r["quality"])

            p = r.get("mean_target_prob")
            if p is not None:
                cur["min_prob"] = min(cur["min_prob"], p) if cur["min_prob"] is not None else p

            cur["count"] += 1
        else:
            zones.append(cur)
            cur = {
                "start": r["start"],
                "end": r["end"],
                "tokens": [r["token"]],
                "ref_indices": [str(r["ref_index"])],
                "qualities": [r["quality"]],
                "min_prob": r.get("mean_target_prob"),
                "count": 1,
            }

    if cur is not None:
        zones.append(cur)

    out = []

    for z in zones:
        if "very_weak" in z["qualities"]:
            severity = "strong_check"
        elif "weak" in z["qualities"]:
            severity = "check"
        else:
            severity = "soft_check"

        zone = {
            "start": round(z["start"], 3),
            "end": round(z["end"], 3),
            "duration": round(z["end"] - z["start"], 3),
            "tokens": " ".join(z["tokens"]),
            "ref_indices": " ".join(z["ref_indices"]),
            "qualities": " ".join(z["qualities"]),
            "min_prob": round(float(z["min_prob"]), 4) if z["min_prob"] is not None else None,
            "count": z["count"],
            "severity": severity,
        }

        out.append(classify_product_zone(zone))

    return out


def build_user_summary(decision: str, shown_zones: List[Dict[str, Any]]) -> str:
    if decision == "recognized" and not shown_zones:
        return "Récitation reconnue."

    if decision == "recognized" and shown_zones:
        return "Récitation reconnue. Quelques zones peuvent être vérifiées."

    if decision == "recognized_with_checks":
        return "Récitation reconnue. Quelques zones sont à vérifier."

    if decision == "probably_wrong_ayah":
        return "La récitation ne correspond probablement pas au verset attendu."

    if decision == "audio_uncertain":
        return "Audio incertain. Réessaie avec une récitation plus claire."

    return "Résultat disponible."


@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>FASSEH V2 Demo</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 980px; margin: 40px auto; padding: 0 20px; }
    input, button { padding: 10px; margin: 8px 0; }
    button { cursor: pointer; }
    pre { background: #111; color: #eee; padding: 16px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; }
    .card { border: 1px solid #ddd; padding: 18px; border-radius: 10px; margin-bottom: 20px; }
  </style>
</head>
<body>
  <h1>FASSEH V2 Demo</h1>
  <p>Prototype privé : upload un WAV + ayah_key. Le système retourne le JSON complet.</p>

  <div class="card">
    <label>Ayah key, ex: 078:001 ou 002:255</label><br>
    <input id="ayah" value="078:001" style="width: 240px"><br>

    <label>Audio WAV</label><br>
    <input id="audio" type="file" accept=".wav,audio/wav"><br>

    <button onclick="score()">Analyser</button>
  </div>

  <h2>Résultat</h2>
  <pre id="out">En attente...</pre>

<script>
async function score() {
  const ayah = document.getElementById("ayah").value;
  const audio = document.getElementById("audio").files[0];
  const out = document.getElementById("out");

  if (!audio) {
    out.textContent = "Choisis un fichier WAV.";
    return;
  }

  out.textContent = "Analyse en cours...";

  const fd = new FormData();
  fd.append("ayah_key", ayah);
  fd.append("file", audio);

  try {
    const res = await fetch("/score", { method: "POST", body: fd });
    const data = await res.json();
    out.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    out.textContent = "Erreur: " + e;
  }
}
</script>
</body>
</html>
"""


@app.get("/health")
def health():
    return {
        "status": "ok",
        "root": str(ROOT),
        "model": MODEL_PATH,
        "refs": REFS_PATH,
        "vocab": VOCAB_PATH,
    }


@app.post("/score")
async def score(
    ayah_key: str = Form(...),
    file: UploadFile = File(...),
):
    run_id = uuid.uuid4().hex[:10]
    safe_ayah = ayah_key.replace(":", "_")

    audio_path = UPLOAD_DIR / f"{run_id}_{file.filename}"
    scorer_out = OUT_DIR / f"{run_id}_{safe_ayah}_score.json"
    align_out = OUT_DIR / f"{run_id}_{safe_ayah}_forced_alignment.json"

    with open(audio_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        run_cmd([
            PYTHON_EXE,
            SCORE_SCRIPT,
            "--model", MODEL_PATH,
            "--audio", str(audio_path),
            "--ayah-key", ayah_key,
            "--refs", REFS_PATH,
            "--vocab", VOCAB_PATH,
            "--config", CONFIG_PATH,
            "--out", str(scorer_out),
        ])

        run_cmd([
            PYTHON_EXE,
            ALIGN_SCRIPT,
            "--model", MODEL_PATH,
            "--audio", str(audio_path),
            "--ayah-key", ayah_key,
            "--refs", REFS_PATH,
            "--vocab", VOCAB_PATH,
            "--out", str(align_out),
        ])

        scorer_json = read_json(scorer_out)
        alignment_json = read_json(align_out)

        weak = extract_weak_phonemes(alignment_json)
        zones = group_weak_zones(weak)

        shown_zones = [z for z in zones if z["show_to_user"]]
        hidden_zones = [z for z in zones if not z["show_to_user"]]

        decision = scorer_json.get("decision", "unknown")
        main_message = build_user_summary(decision, shown_zones)

        app_json = {
            "version": "fasseh_v2_github_demo_001",
            "ayah_key": ayah_key,
            "audio_filename": file.filename,
            "decision": decision,
            "display": {
                "show_score_to_user": False,
                "main_message": main_message,
                "zones_to_show": shown_zones,
                "num_zones_to_show": len(shown_zones),
            },
            "internal": {
                "model": MODEL_PATH,
                "scorer_json_path": str(scorer_out),
                "alignment_json_path": str(align_out),
                "scores": scorer_json.get("internal_scores", {}),
            },
            "model_outputs": {
                "reference_phonemes_text": scorer_json.get("reference_phonemes_text"),
                "predicted_phonemes_text": scorer_json.get("predicted_phonemes_text"),
                "major_errors": scorer_json.get("major_errors", []),
                "soft_warnings": scorer_json.get("soft_warnings", []),
                "uncertain_zones": scorer_json.get("uncertain_zones", []),
            },
            "forced_alignment": {
                "summary": alignment_json.get("summary", {}),
                "audio_duration": alignment_json.get("audio_duration"),
                "num_reference_tokens": alignment_json.get("num_reference_tokens"),
            },
            "gop_like": {
                "all_zones_count": len(zones),
                "shown_zones_count": len(shown_zones),
                "hidden_zones_count": len(hidden_zones),
                "shown_zones": shown_zones,
                "hidden_or_soft_zones": hidden_zones,
            },
            "raw_debug": {
                "scorer_json": scorer_json,
                "alignment_json": alignment_json,
            },
            "notes": [
                "Prototype privé.",
                "Les zones sont des zones à vérifier, pas des fautes tajwid certifiées.",
                "Les scores sont internes et ne doivent pas être affichés comme note utilisateur finale."
            ]
        }

        return JSONResponse(app_json)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "ayah_key": ayah_key,
                "audio_filename": file.filename,
                "hint": "Vérifie que l'audio est bien un WAV lisible et que le ayah_key existe."
            }
        )
