import argparse
import csv
import json
import os
import re
from typing import Dict, List, Tuple, Any

import torch
import torch.nn.functional as F
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor, Wav2Vec2FeatureExtractor, Wav2Vec2CTCTokenizer


SPECIAL_TOKENS = {
    "<pad>", "<s>", "</s>", "<unk>", "[PAD]", "[UNK]", "|"
}

VOWELS = {"a", "aa", "i", "ii", "u", "uu"}


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path: str) -> Dict[str, Any]:
    cfg = load_json(path)
    cfg.setdefault("soft_equivalences", [["a", "aa"], ["i", "ii"], ["u", "uu"]])
    cfg.setdefault("soft_tokens", [":", "ŋ"])
    cfg.setdefault("ending_tokens_soft", True)
    cfg.setdefault("waqf_soft", True)
    cfg.setdefault("tanwin_soft", True)
    cfg.setdefault("ghunnah_soft", True)
    cfg.setdefault("decision_thresholds", {
        "recognized": 0.18,
        "recognized_with_checks": 0.30,
        "uncertain": 0.45,
        "probably_wrong": 0.45
    })
    return cfg


def load_refs(refs_path: str) -> Dict[str, str]:
    refs = {}
    with open(refs_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []

        key_col = None
        for c in ["ayah_key", "key", "ayah", "verse_key"]:
            if c in fields:
                key_col = c
                break

        ref_col = None
        for c in ["phoneme_ref_v2_tokens", "phoneme_ref_v2_raw", "phoneme_sequence", "phoneme_ref", "phonemes", "quran_phonemizer", "native_phonemes", "text"]:
            if c in fields:
                ref_col = c
                break

        if not key_col:
            raise ValueError(f"Impossible de trouver la colonne ayah_key dans {refs_path}. Colonnes: {fields}")
        if not ref_col:
            raise ValueError(f"Impossible de trouver la colonne phonèmes dans {refs_path}. Colonnes: {fields}")

        for row in reader:
            k = str(row[key_col]).strip()
            v = str(row[ref_col]).strip()
            if k and v:
                refs[k] = v

    return refs


def load_vocab_tokens(vocab_path: str) -> List[str]:
    vocab = load_json(vocab_path)

    if isinstance(vocab, dict):
        tokens = list(vocab.keys())
    elif isinstance(vocab, list):
        tokens = vocab
    else:
        raise ValueError("Format vocab non reconnu")

    tokens = [str(t) for t in tokens if str(t) not in SPECIAL_TOKENS]
    tokens = sorted(tokens, key=len, reverse=True)
    return tokens


def clean_decoded_text(text: str) -> str:
    # Nettoyage robuste des tokens spéciaux CTC / tokenizer
    for sp in ["[PAD]", "[UNK]", "<pad>", "<unk>", "<s>", "</s>"]:
        text = text.replace(sp, "")

    text = text.replace("|", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def split_phonemes(text: str, vocab_tokens: List[str]) -> List[str]:
    """
    Découpe une sortie quran_phonemizer en tokens phonémiques.
    Important: même si le texte contient des espaces entre mots,
    on tokenize chaque mot caractère/token par caractère/token.
    """
    text = clean_decoded_text(text)

    if not text:
        return []

    tokens = []
    i = 0

    while i < len(text):
        if text[i].isspace():
            i += 1
            continue

        matched = None

        for tok in vocab_tokens:
            if not tok or tok in SPECIAL_TOKENS:
                continue

            if text.startswith(tok, i):
                matched = tok
                break

        if matched is None:
            matched = text[i]

        if matched not in SPECIAL_TOKENS and matched.strip():
            tokens.append(matched)

        i += len(matched)

    return tokens

def load_audio_16k(path: str):
    """
    Loader audio robuste pour WAV PCM.
    Évite librosa. Utilise d'abord wave/numpy, puis resample si besoin.
    """
    import os
    import wave
    import numpy as np

    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio introuvable: {path}")

    try:
        with wave.open(path, "rb") as wf:
            sr = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if sampwidth == 2:
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            audio = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        elif sampwidth == 1:
            audio = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            raise RuntimeError(f"Format WAV non supporté: sampwidth={sampwidth}")

        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)

        if sr != 16000:
            try:
                from scipy.signal import resample_poly
                import math
                g = math.gcd(sr, 16000)
                audio = resample_poly(audio, 16000 // g, sr // g).astype(np.float32)
                sr = 16000
            except Exception as e:
                raise RuntimeError(
                    f"Audio chargé mais sr={sr}, resampling impossible sans scipy. "
                    f"Convertis en WAV 16k avec ffmpeg. Erreur: {e}"
                )

        return audio.astype(np.float32), 16000

    except Exception as e:
        raise RuntimeError(f"Impossible de charger l'audio WAV: {path}. Erreur: {e}")

def load_model_bundle(model_dir: str, vocab_path: str):
    model = Wav2Vec2ForCTC.from_pretrained(model_dir)
    model.eval()

    try:
        processor = Wav2Vec2Processor.from_pretrained(model_dir)
    except Exception:
        tokenizer = Wav2Vec2CTCTokenizer(
            vocab_path,
            unk_token="<unk>",
            pad_token="<pad>",
            word_delimiter_token="|"
        )
        feature_extractor = Wav2Vec2FeatureExtractor(
            feature_size=1,
            sampling_rate=16000,
            padding_value=0.0,
            do_normalize=True,
            return_attention_mask=False
        )
        processor = Wav2Vec2Processor(
            feature_extractor=feature_extractor,
            tokenizer=tokenizer
        )

    return model, processor


def predict_phonemes(model, processor, audio_path: str, vocab_tokens: List[str]) -> Tuple[str, List[str], float]:
    wav, sr = load_audio_16k(audio_path)

    inputs = processor(
        wav,
        sampling_rate=16000,
        return_tensors="pt",
        padding=True
    )

    with torch.no_grad():
        logits = model(inputs.input_values).logits
        probs = F.softmax(logits, dim=-1)
        frame_conf = probs.max(dim=-1).values.mean().item()
        pred_ids = torch.argmax(logits, dim=-1)

    try:
        decoded = processor.batch_decode(pred_ids, skip_special_tokens=True)[0]
    except TypeError:
        decoded = processor.batch_decode(pred_ids)[0]
    decoded = clean_decoded_text(decoded)
    tokens = split_phonemes(decoded, vocab_tokens)

    return decoded, tokens, float(frame_conf)


def align_tokens(ref: List[str], pred: List[str]) -> Tuple[List[Dict[str, Any]], int]:
    n, m = len(ref), len(pred)

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = i
        back[i][0] = "delete"

    for j in range(1, m + 1):
        dp[0][j] = j
        back[0][j] = "insert"

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost_sub = 0 if ref[i - 1] == pred[j - 1] else 1

            choices = [
                (dp[i - 1][j] + 1, "delete"),
                (dp[i][j - 1] + 1, "insert"),
                (dp[i - 1][j - 1] + cost_sub, "match" if cost_sub == 0 else "substitute")
            ]

            best = min(choices, key=lambda x: x[0])
            dp[i][j] = best[0]
            back[i][j] = best[1]

    alignment = []
    i, j = n, m

    while i > 0 or j > 0:
        op = back[i][j]

        if op == "match":
            alignment.append({
                "ref_index": i - 1,
                "pred_index": j - 1,
                "ref": ref[i - 1],
                "pred": pred[j - 1],
                "op": "match"
            })
            i -= 1
            j -= 1

        elif op == "substitute":
            alignment.append({
                "ref_index": i - 1,
                "pred_index": j - 1,
                "ref": ref[i - 1],
                "pred": pred[j - 1],
                "op": "substitute"
            })
            i -= 1
            j -= 1

        elif op == "delete":
            alignment.append({
                "ref_index": i - 1,
                "pred_index": None,
                "ref": ref[i - 1],
                "pred": None,
                "op": "delete"
            })
            i -= 1

        elif op == "insert":
            alignment.append({
                "ref_index": None,
                "pred_index": j - 1,
                "ref": None,
                "pred": pred[j - 1],
                "op": "insert"
            })
            j -= 1

        else:
            break

    alignment.reverse()
    return alignment, dp[n][m]


def is_soft_equivalent(a: str, b: str, cfg: Dict[str, Any]) -> bool:
    if a == b:
        return True

    pairs = {tuple(x) for x in cfg.get("soft_equivalences", [])}
    pairs |= {(b, a) for a, b in pairs}

    return (a, b) in pairs


def classify_alignment(alignment: List[Dict[str, Any]], cfg: Dict[str, Any], ref_len: int):
    """
    Classification prudente produit V2.

    Principe:
    - Les durées, voyelles, ŋ, :, fins de verset => soft_warning.
    - Les petits trous isolés => uncertain, pas major_error.
    - Les vrais clusters de sons manquants => major_error.
    - Les substitutions consonantiques restent major sauf cas connus doux.
    """
    major_errors = []
    soft_warnings = []
    uncertain_zones = []
    enriched = []

    soft_tokens = set(cfg.get("soft_tokens", []))
    vowels = {"a", "aa", "i", "ii", "u", "uu"}
    semivowels = {"w", "y"}
    lam_variants = {"l", "L"}

    def is_near_end(ref_index):
        if ref_index is None or ref_len <= 0:
            return False
        return ref_index >= max(0, ref_len - 4)

    def is_soft_ref_or_pred(ref, pred):
        if ref in soft_tokens or pred in soft_tokens:
            return True

        if ref in vowels and pred in vowels:
            return True

        if ref in vowels and pred in semivowels:
            return True

        if ref in semivowels and pred in vowels:
            return True

        if ref in lam_variants and pred in lam_variants:
            return True

        if ref and pred and is_soft_equivalent(ref, pred, cfg):
            return True

        return False

    def strong_delete_run_size(pos):
        """
        Compte un cluster local de deletes consonantiques.
        Un delete isolé est souvent un artefact CTC/alignment.
        Un vrai mot oublié crée généralement plusieurs deletes forts proches.
        """
        count = 0

        # gauche
        k = pos
        while k >= 0:
            it = alignment[k]
            if it.get("op") == "delete":
                r = it.get("ref")
                if r not in vowels and r not in soft_tokens:
                    count += 1
                    k -= 1
                    continue
            break

        # droite
        k = pos + 1
        while k < len(alignment):
            it = alignment[k]
            if it.get("op") == "delete":
                r = it.get("ref")
                if r not in vowels and r not in soft_tokens:
                    count += 1
                    k += 1
                    continue
            break

        return count

    for idx, item in enumerate(alignment):
        ref = item.get("ref")
        pred = item.get("pred")
        op = item.get("op")
        ref_index = item.get("ref_index")

        severity = "ok"
        cls = "match"
        message = None
        near_end = is_near_end(ref_index)

        if op == "match":
            severity = "ok"
            cls = "match"

        elif op == "substitute":
            if is_soft_ref_or_pred(ref, pred):
                severity = "soft_warning"

                if ref in lam_variants and pred in lam_variants:
                    cls = "lam_variant"
                    message = f"Variation de lām à vérifier doucement: {ref} -> {pred}"
                elif ref in vowels and pred in vowels:
                    cls = "vowel_difference"
                    message = f"Voyelle à vérifier: {ref} -> {pred}"
                elif (ref in vowels and pred in semivowels) or (ref in semivowels and pred in vowels):
                    cls = "vowel_or_glide_alignment"
                    message = f"Zone voyelle/waqf à vérifier: {ref} -> {pred}"
                elif ref in soft_tokens or pred in soft_tokens:
                    cls = "soft_token_difference"
                    message = f"Différence douce à vérifier: {ref} -> {pred}"
                else:
                    cls = "soft_equivalence"
                    message = f"Différence proche à vérifier: {ref} -> {pred}"

            elif near_end and cfg.get("ending_tokens_soft", True):
                severity = "soft_warning"
                cls = "ending_or_waqf_difference"
                message = f"Fin de verset à vérifier: {ref} -> {pred}"

            else:
                severity = "major_error"
                cls = "consonant_substitution"
                message = f"Son important différent: {ref} -> {pred}"

        elif op == "delete":
            if ref in soft_tokens:
                severity = "soft_warning"
                cls = "soft_token_missing"
                message = f"Élément doux manquant: {ref}"

            elif ref in vowels:
                severity = "soft_warning"
                cls = "vowel_missing"
                message = f"Voyelle à vérifier: {ref}"

            elif near_end and cfg.get("waqf_soft", True):
                severity = "soft_warning"
                cls = "ending_or_waqf_missing"
                message = f"Fin de mot/verset à vérifier: {ref}"

            else:
                run_size = strong_delete_run_size(idx)

                if run_size >= 3:
                    severity = "major_error"
                    cls = "missing_sound_cluster"
                    message = f"Plusieurs sons attendus non retrouvés près de: {ref}"
                else:
                    severity = "uncertain"
                    cls = "isolated_missing_sound"
                    message = f"Son isolé non retrouvé ou alignement incertain: {ref}"

        elif op == "insert":
            if pred in soft_tokens:
                severity = "soft_warning"
                cls = "extra_soft_token"
                message = f"Élément doux en plus: {pred}"

            elif pred in vowels:
                severity = "soft_warning"
                cls = "extra_vowel"
                message = f"Voyelle en plus à vérifier: {pred}"

            elif near_end and cfg.get("waqf_soft", True):
                severity = "soft_warning"
                cls = "ending_extra"
                message = f"Fin de verset différente: {pred}"

            else:
                severity = "uncertain"
                cls = "extra_sound"
                message = f"Son en plus ou alignement incertain: {pred}"

        item2 = dict(item)
        item2["severity"] = severity
        item2["class"] = cls
        item2["message"] = message
        enriched.append(item2)

        zone = {
            "index": idx,
            "ref_index": ref_index,
            "ref": ref,
            "pred": pred,
            "op": op,
            "class": cls,
            "message": message
        }

        if severity == "major_error":
            major_errors.append(zone)
        elif severity == "soft_warning":
            soft_warnings.append(zone)
        elif severity == "uncertain":
            uncertain_zones.append(zone)

    return enriched, major_errors, soft_warnings, uncertain_zones

def decide(per: float, major_count: int, confidence: float, cfg: Dict[str, Any]) -> Tuple[str, str]:
    th = cfg.get("decision_thresholds", {})

    recognized = float(th.get("recognized", 0.18))
    checks = float(th.get("recognized_with_checks", 0.30))
    uncertain = float(th.get("uncertain", 0.45))

    if confidence < 0.35:
        return "audio_uncertain", "Audio incertain. Réessaie avec une récitation plus claire."

    if per <= recognized and major_count == 0:
        return "recognized", "Récitation reconnue."

    if per <= checks:
        return "recognized_with_checks", "Récitation reconnue. Quelques zones sont à vérifier."

    if per <= uncertain:
        return "uncertain", "Récitation partiellement reconnue. Vérifie plusieurs zones."

    return "probably_wrong_ayah", "La récitation ne correspond probablement pas assez au verset attendu."


def score_audio(
    model,
    processor,
    audio_path: str,
    ayah_key: str,
    refs: Dict[str, str],
    vocab_tokens: List[str],
    cfg: Dict[str, Any]
) -> Dict[str, Any]:

    if ayah_key not in refs:
        raise ValueError(f"ayah_key introuvable dans refs: {ayah_key}")

    ref_text = refs[ayah_key]
    ref_tokens = split_phonemes(ref_text, vocab_tokens)

    decoded_text, pred_tokens, confidence = predict_phonemes(
        model=model,
        processor=processor,
        audio_path=audio_path,
        vocab_tokens=vocab_tokens
    )

    alignment, edit_distance = align_tokens(ref_tokens, pred_tokens)

    ref_len = max(1, len(ref_tokens))
    per = edit_distance / ref_len

    enriched_alignment, major_errors, soft_warnings, uncertain_zones = classify_alignment(
        alignment=alignment,
        cfg=cfg,
        ref_len=len(ref_tokens)
    )

    major_rate = len(major_errors) / ref_len
    soft_rate = len(soft_warnings) / ref_len

    memory_score = max(0.0, min(100.0, 100.0 * (1.0 - per)))
    phoneme_score = max(0.0, min(100.0, 100.0 * (1.0 - major_rate)))
    confidence_score = max(0.0, min(100.0, confidence * 100.0))

    decision, user_message = decide(
        per=per,
        major_count=len(major_errors),
        confidence=confidence,
        cfg=cfg
    )

    return {
        "ayah_key": ayah_key,
        "audio": audio_path,
        "decision": decision,
        "user_message": user_message,
        "reference_phonemes_text": ref_text,
        "predicted_phonemes_text": decoded_text,
        "reference_phonemes": ref_tokens,
        "predicted_phonemes": pred_tokens,
        "major_errors": major_errors[:20],
        "soft_warnings": soft_warnings[:30],
        "uncertain_zones": uncertain_zones[:20],
        "internal_scores": {
            "per": round(per, 6),
            "edit_distance": int(edit_distance),
            "ref_len": int(len(ref_tokens)),
            "pred_len": int(len(pred_tokens)),
            "memory_score": round(memory_score, 2),
            "phoneme_score": round(phoneme_score, 2),
            "confidence_score": round(confidence_score, 2),
            "major_error_count": int(len(major_errors)),
            "soft_warning_count": int(len(soft_warnings)),
            "uncertain_zone_count": int(len(uncertain_zones)),
            "soft_warning_rate": round(soft_rate, 6)
        },
        "alignment": enriched_alignment
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--ayah-key", required=True)
    ap.add_argument("--refs", required=True)
    ap.add_argument("--vocab", required=True)
    ap.add_argument("--config", default="configs/scoring_v2_native_baseline_001.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = load_config(args.config)
    refs = load_refs(args.refs)
    vocab_tokens = load_vocab_tokens(args.vocab)
    model, processor = load_model_bundle(args.model, args.vocab)

    result = score_audio(
        model=model,
        processor=processor,
        audio_path=args.audio,
        ayah_key=args.ayah_key,
        refs=refs,
        vocab_tokens=vocab_tokens,
        cfg=cfg
    )

    os.makedirs(os.path.dirname(args.out), exist_ok=True) if os.path.dirname(args.out) else None

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "ayah_key": result["ayah_key"],
        "decision": result["decision"],
        "user_message": result["user_message"],
        "internal_scores": result["internal_scores"],
        "major_errors_preview": result["major_errors"][:5],
        "soft_warnings_preview": result["soft_warnings"][:5]
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()




