import argparse
import json
import os
from typing import List, Dict, Any

import numpy as np
import torch
import torch.nn.functional as F

from score_ayah_v2_native_product import (
    load_refs,
    load_vocab_tokens,
    split_phonemes,
    load_audio_16k,
    load_model_bundle,
    clean_decoded_text,
)


def get_token_id_map(processor):
    vocab = processor.tokenizer.get_vocab()
    return vocab, {v: k for k, v in vocab.items()}


def get_blank_id(processor, model_vocab_size: int, model=None):
    """
    Trouve un blank_id valide pour les logits du modèle.
    Certains tokenizers gardent un pad_token_id hors taille réelle du head CTC.
    """
    candidates = []

    if model is not None:
        cfg_pad = getattr(model.config, "pad_token_id", None)
        if cfg_pad is not None:
            candidates.append(int(cfg_pad))

    tok_pad = getattr(processor.tokenizer, "pad_token_id", None)
    if tok_pad is not None:
        candidates.append(int(tok_pad))

    vocab = processor.tokenizer.get_vocab()
    for tok in ["<pad>", "[PAD]", "<s>", "</s>"]:
        if tok in vocab:
            candidates.append(int(vocab[tok]))

    candidates.append(0)

    for c in candidates:
        if 0 <= int(c) < model_vocab_size:
            return int(c)

    raise ValueError(
        f"Impossible de trouver un blank_id valide. "
        f"candidates={candidates}, model_vocab_size={model_vocab_size}"
    )


def build_extended_labels(label_ids: List[int], blank_id: int):
    """
    CTC extended sequence:
    blank, y1, blank, y2, blank, ...
    """
    ext_ids = []
    ref_positions = []

    ext_ids.append(blank_id)
    ref_positions.append(None)

    for i, lid in enumerate(label_ids):
        ext_ids.append(lid)
        ref_positions.append(i)

        ext_ids.append(blank_id)
        ref_positions.append(None)

    return ext_ids, ref_positions


def ctc_viterbi_align(log_probs: np.ndarray, label_ids: List[int], blank_id: int):
    """
    Viterbi CTC forced alignment.
    log_probs: [T, V]
    label_ids: expected reference token ids
    returns best state path over extended CTC labels.
    """
    T, V = log_probs.shape
    if len(label_ids) == 0:
        raise ValueError("label_ids vide")

    ext_ids, ref_positions = build_extended_labels(label_ids, blank_id)
    S = len(ext_ids)

    neg_inf = -1e30
    dp = np.full((T, S), neg_inf, dtype=np.float32)
    bp = np.full((T, S), -1, dtype=np.int32)

    # init t=0
    dp[0, 0] = log_probs[0, ext_ids[0]]
    if S > 1:
        dp[0, 1] = log_probs[0, ext_ids[1]]

    for t in range(1, T):
        for s in range(S):
            candidates = [(dp[t - 1, s], s)]

            if s - 1 >= 0:
                candidates.append((dp[t - 1, s - 1], s - 1))

            # skip transition, allowed only for non-blank and non-repeat
            if s - 2 >= 0:
                cur = ext_ids[s]
                prev2 = ext_ids[s - 2]

                if cur != blank_id and cur != prev2:
                    candidates.append((dp[t - 1, s - 2], s - 2))

            best_score, best_prev = max(candidates, key=lambda x: x[0])
            dp[t, s] = best_score + log_probs[t, ext_ids[s]]
            bp[t, s] = best_prev

    # final state can be final blank or final label
    final_candidates = [(dp[T - 1, S - 1], S - 1)]
    if S - 2 >= 0:
        final_candidates.append((dp[T - 1, S - 2], S - 2))

    best_final_score, best_s = max(final_candidates, key=lambda x: x[0])

    path = [best_s]
    cur = best_s

    for t in range(T - 1, 0, -1):
        cur = int(bp[t, cur])
        if cur < 0:
            cur = 0
        path.append(cur)

    path.reverse()

    return {
        "path_states": path,
        "extended_ids": ext_ids,
        "ref_positions": ref_positions,
        "score": float(best_final_score),
    }


def summarize_reference_segments(
    path_states: List[int],
    ext_ids: List[int],
    ref_positions: List[Any],
    label_ids: List[int],
    ref_tokens: List[str],
    probs: np.ndarray,
    log_probs: np.ndarray,
    audio_duration: float,
):
    T = len(path_states)
    frame_dur = audio_duration / max(1, T)

    frames_by_ref = {i: [] for i in range(len(ref_tokens))}

    for t, s in enumerate(path_states):
        ref_i = ref_positions[s]
        if ref_i is not None:
            frames_by_ref[ref_i].append(t)

    segments = []

    for i, tok in enumerate(ref_tokens):
        frames = frames_by_ref.get(i, [])
        lid = label_ids[i]

        if not frames:
            segments.append({
                "ref_index": i,
                "token": tok,
                "start": None,
                "end": None,
                "duration": 0.0,
                "mean_target_prob": 0.0,
                "mean_frame_max_prob": 0.0,
                "gop_like_logprob": None,
                "quality": "missing_alignment",
                "num_frames": 0,
            })
            continue

        start_f = min(frames)
        end_f = max(frames) + 1

        target_probs = probs[frames, lid]
        frame_max_probs = probs[frames, :].max(axis=-1)
        target_log_probs = log_probs[frames, lid]

        mean_target_prob = float(np.mean(target_probs))
        mean_frame_max_prob = float(np.mean(frame_max_probs))
        gop_like_logprob = float(np.mean(target_log_probs))

        if mean_target_prob >= 0.75:
            quality = "good"
        elif mean_target_prob >= 0.45:
            quality = "check"
        elif mean_target_prob >= 0.20:
            quality = "weak"
        else:
            quality = "very_weak"

        segments.append({
            "ref_index": i,
            "token": tok,
            "start": round(start_f * frame_dur, 4),
            "end": round(end_f * frame_dur, 4),
            "duration": round((end_f - start_f) * frame_dur, 4),
            "mean_target_prob": round(mean_target_prob, 4),
            "mean_frame_max_prob": round(mean_frame_max_prob, 4),
            "gop_like_logprob": round(gop_like_logprob, 4),
            "quality": quality,
            "num_frames": len(frames),
            "start_frame": int(start_f),
            "end_frame": int(end_f),
        })

    return segments


def decode_prediction(processor, pred_ids):
    try:
        decoded = processor.batch_decode(pred_ids.unsqueeze(0), skip_special_tokens=True)[0]
    except TypeError:
        decoded = processor.batch_decode(pred_ids.unsqueeze(0))[0]

    return clean_decoded_text(decoded)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--ayah-key", required=True)
    ap.add_argument("--refs", required=True)
    ap.add_argument("--vocab", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    refs = load_refs(args.refs)
    vocab_tokens = load_vocab_tokens(args.vocab)
    model, processor = load_model_bundle(args.model, args.vocab)

    if args.ayah_key not in refs:
        raise ValueError(f"ayah_key introuvable dans refs: {args.ayah_key}")

    ref_text = refs[args.ayah_key]
    ref_tokens = split_phonemes(ref_text, vocab_tokens)

    token_to_id, id_to_token = get_token_id_map(processor)
    blank_id = get_blank_id(processor, model_vocab_size=model.config.vocab_size, model=model)

    missing = [t for t in ref_tokens if t not in token_to_id]
    if missing:
        raise ValueError(f"Tokens référence absents du tokenizer: {sorted(set(missing))}")

    label_ids = [int(token_to_id[t]) for t in ref_tokens]

    wav, sr = load_audio_16k(args.audio)
    audio_duration = len(wav) / sr

    inputs = processor(
        wav,
        sampling_rate=16000,
        return_tensors="pt",
        padding=True,
    )

    with torch.no_grad():
        logits = model(inputs.input_values).logits[0]
        log_probs_t = F.log_softmax(logits, dim=-1)
        probs_t = F.softmax(logits, dim=-1)
        pred_ids = torch.argmax(logits, dim=-1)

    log_probs = log_probs_t.cpu().numpy()
    probs = probs_t.cpu().numpy()

    align = ctc_viterbi_align(
        log_probs=log_probs,
        label_ids=label_ids,
        blank_id=blank_id,
    )

    reference_segments = summarize_reference_segments(
        path_states=align["path_states"],
        ext_ids=align["extended_ids"],
        ref_positions=align["ref_positions"],
        label_ids=label_ids,
        ref_tokens=ref_tokens,
        probs=probs,
        log_probs=log_probs,
        audio_duration=audio_duration,
    )

    decoded = decode_prediction(processor, pred_ids)

    weak_segments = [
        s for s in reference_segments
        if s["quality"] in {"weak", "very_weak", "missing_alignment"}
    ]

    check_segments = [
        s for s in reference_segments
        if s["quality"] == "check"
    ]

    result = {
        "type": "forced_reference_alignment_v1",
        "ayah_key": args.ayah_key,
        "audio": args.audio,
        "audio_duration": round(audio_duration, 4),
        "model": args.model,
        "reference_phonemes_text": ref_text,
        "reference_phonemes": ref_tokens,
        "predicted_phonemes_text": decoded,
        "blank_id": blank_id,
        "num_frames": int(log_probs.shape[0]),
        "num_reference_tokens": len(ref_tokens),
        "alignment_score": align["score"],
        "reference_phoneme_timings": reference_segments,
        "summary": {
            "good_count": sum(1 for s in reference_segments if s["quality"] == "good"),
            "check_count": sum(1 for s in reference_segments if s["quality"] == "check"),
            "weak_count": sum(1 for s in reference_segments if s["quality"] == "weak"),
            "very_weak_count": sum(1 for s in reference_segments if s["quality"] == "very_weak"),
            "missing_alignment_count": sum(1 for s in reference_segments if s["quality"] == "missing_alignment"),
            "weak_or_missing_preview": weak_segments[:10],
            "check_preview": check_segments[:10],
        },
        "note": "V1 forced alignment of expected reference phonemes using CTC Viterbi. GOP-like scores are preliminary, not final tajwid judgement."
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True) if os.path.dirname(args.out) else None

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "ayah_key": result["ayah_key"],
        "audio_duration": result["audio_duration"],
        "num_reference_tokens": result["num_reference_tokens"],
        "num_frames": result["num_frames"],
        "summary": result["summary"],
        "predicted_preview": result["predicted_phonemes_text"][:200],
        "out": args.out,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

