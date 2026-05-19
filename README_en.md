# FASEEH AI V2

FASEEH AI V2 is a private prototype for phonemic feedback on Quranic recitation.

This version is not yet a final tajwid corrector. It does not confirm that an error is certain. Instead, it helps identify time segments that should be reviewed in a recitation.

The system recognizes the recited verse, compares the recitation with a phonemic reference, locates areas that seem weak or inconsistent, and then returns a complete JSON output that can be used in a future application.

---

## Table of Contents

1. [General Overview](#general-overview)
2. [Features](#features)
3. [Verse Format](#verse-format)
4. [Quick Definitions](#quick-definitions)
5. [Model Used](#model-used)
6. [Recommended Project Structure](#recommended-project-structure)
7. [Windows Installation](#windows-installation)
8. [Mac / Linux Installation](#mac--linux-installation)
9. [Run the Demo](#run-the-demo)
10. [How to Test](#how-to-test)
11. [JSON Output](#json-output)
12. [Recommended Wording](#recommended-wording)
13. [Current State](#current-state)
14. [Current Limitations](#current-limitations)
15. [Roadmap](#roadmap)
16. [Disclaimer](#disclaimer)

---

## General Overview

FASEEH AI V2 is designed to analyze a Quranic recitation from a WAV audio file.

The user provides an audio file along with an `ayah_key`, which is the identifier of the expected verse. The system then uses a phonemic model to recognize the recitation, compare the audio with the expected reference, and produce structured output.

The purpose of this version is to provide technical feedback that can be used in a future user interface.

Important: this version must not be presented as a definitive religious or tajwid judgment. It only indicates areas that may deserve further review.

---

## Features

- WAV audio file upload
- Input of an `ayah_key`, for example `067:001`
- Phonemic recognition using a wav2vec2 CTC model
- V2 product scoring
- Probable rejection of the wrong verse
- Forced alignment with the phonemic reference
- GOP-like scoring
- Detection of time segments to review
- Complete debug JSON output
- Simple local interface via FastAPI
- Compatible with Windows, Mac, and Linux if paths are configured correctly

---

## Verse Format

`ayah_key` refers to a verse using the following format:

```text
surah:verse
```

Examples:

```text
001:001
067:001
078:001
112:001
002:255
```

For initial testing, it is recommended to use short verses:

```text
001:001 to 001:007
067:001
078:001 to 078:012
112:001 to 112:004
113:001 to 113:005
114:001 to 114:006
```

Long verses such as `002:255` may work, but they generate more areas to review.

---

## Quick Definitions

### CTC

`CTC` stands for `Connectionist Temporal Classification`.

It is a method used in speech recognition to learn how to predict a sequence of characters or phonemes without needing to know the exact timing of each sound in advance.

In FASEEH AI V2, the model receives the audio and predicts a sequence of phonemes.

### Phoneme

A phoneme is a sound unit. Here, the model is not only trying to transcribe classical Arabic text. It is trying to recognize a sequence of sounds corresponding to Quranic recitation.

Simplified example:

```text
t a b a a R a k a
```

### PER

`PER` stands for `Phoneme Error Rate`.

It is an error rate between the expected phonemic sequence and the sequence predicted by the model.

In this project, PER remains an internal metric. It should not be displayed as a raw user-facing score.

### Forced Alignment

`Forced alignment` means forced temporal alignment.

The system takes the audio and the expected phoneme sequence for the verse, then searches for when each expected phoneme appears in the audio.

This makes it possible to obtain timings such as:

```json
{
  "token": "q",
  "start": 6.94,
  "end": 6.96
}
```

### GOP-like Scoring

`GOP` stands for `Goodness of Pronunciation`.

Here, a `GOP-like` version is used, meaning an approximate score that estimates whether each expected phoneme seems well supported by the audio.

This is not yet a final tajwid judgment. It is a technical signal used to detect weak areas.

### Waqf

`Waqf` refers to a stop or pause in recitation. In this version, differences at the end of a word or verse are handled carefully.

### Ghunnah / Tanwin / Madd

These elements are part of tajwid. The current version may sometimes detect areas related to nasalization, long vowels, or recitation endings, but it does not yet certify tajwid rules in a final way.

---

## Model Used

The current main model is:

```text
models/fasseh_v2_native_iqraeval_10000_001/best
```

Important: this model folder is not included in GitHub because it contains large files.

To run the demo, the model must be retrieved separately and placed here:

```text
FASEEH_AI_V2/models/fasseh_v2_native_iqraeval_10000_001/best
```

The `best` folder must contain the Hugging Face model files, for example:

```text
config.json
model.safetensors
preprocessor_config.json
tokenizer_config.json
vocab.json
special_tokens_map.json
```

If this folder is missing, the application will not be able to analyze audio files.

---

## Recommended Project Structure

```text
FASEEH_AI_V2/
│
├─ apps/
│  └─ fasseh_demo_api.py
│
├─ scripts/
│  ├─ score_ayah_v2_native_product.py
│  └─ forced_align_v2_reference.py
│
├─ configs/
│  └─ scoring_v2_native_baseline_002_prudent.json
│
├─ outputs/
│  └─ v2_native/
│     ├─ quran_refs_v2_native_full.csv
│     └─ vocab_quran_phonemizer_v2_native.json
│
├─ models/
│  └─ fasseh_v2_native_iqraeval_10000_001/
│     └─ best/
│        ├─ config.json
│        ├─ model.safetensors
│        └─ ...
│
├─ requirements.txt
├─ README.md
└─ .gitignore
```

---

## Windows Installation

Open a PowerShell terminal in the project folder:

```powershell
cd C:\Users\Admin\Desktop\FASEEH_AI_V2
```

Create a Python environment:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\activate
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

If `uvicorn` or `fastapi` is missing, install them manually:

```powershell
pip install fastapi uvicorn python-multipart
```

If audio or model dependencies are missing:

```powershell
pip install torch transformers numpy pandas soundfile librosa scipy safetensors
```

---

## Mac / Linux Installation

Open a terminal in the project folder:

```bash
cd FASEEH_AI_V2
```

Create a Python environment:

```bash
python3 -m venv .venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

If needed:

```bash
pip install fastapi uvicorn python-multipart torch transformers numpy pandas soundfile librosa scipy safetensors
```

---

## Run the Demo

### Windows

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"

python -m uvicorn apps.fasseh_demo_api:app --host 127.0.0.1 --port 8000
```

### Mac / Linux

```bash
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

python -m uvicorn apps.fasseh_demo_api:app --host 127.0.0.1 --port 8000
```

Then open this in the browser:

```text
http://127.0.0.1:8000
```

---

## How to Test

1. Open the local page.
2. Enter an `ayah_key`, for example `067:001`.
3. Upload a WAV file.
4. Click `Analyze`.
5. Read the returned JSON.

The system will return a general decision, internal scores, predicted phonemes, temporal alignment, and the areas to review.

---

## JSON Output

The demo returns a JSON object with several sections:

- `decision`: global product decision
- `display`: what the application can display
- `zones_to_show`: time segments to review
- `internal`: internal scores
- `model_outputs`: phonemic output from the model
- `forced_alignment`: summary of the temporal alignment
- `gop_like`: detected weak areas
- `raw_debug`: complete debug JSON

Example of a positive decision:

```json
{
  "decision": "recognized",
  "display": {
    "show_score_to_user": false,
    "main_message": "Recitation recognized."
  }
}
```

Example with areas to review:

```json
{
  "decision": "recognized_with_checks",
  "display": {
    "show_score_to_user": false,
    "main_message": "Recitation recognized. A few areas should be reviewed.",
    "num_zones_to_show": 2
  }
}
```

---

## Recommended Wording

Scores are internal. A raw score must not be displayed to the user.

Good wording:

```text
Recitation recognized.
```

or:

```text
Recitation recognized. A few areas may be reviewed.
```

or:

```text
Review this area of the recitation.
```

Bad wording:

```text
You made a definite tajwid mistake.
```

or:

```text
You recite at 54%.
```

This version only indicates areas to review. It does not yet certify tajwid errors.

---

## Current State

Baseline name:

```text
FASSEH V2 BASELINE 003
```

Current model:

```text
models/fasseh_v2_native_iqraeval_10000_001/best
```

This baseline includes:

- V2 phonemic ASR
- V2 product scorer
- Wrong-verse rejection
- Reference forced alignment
- GOP-like scoring
- Grouping into time segments
- Product filtering
- Final JSON for the app

---

## Current Limitations

This version does not yet include:

- final tajwid judgment
- complete deterministic rules for madd, ghunnah, ikhfa, idgham, qalqalah, etc.
- expert calibration on a large user dataset
- sufficient human annotation
- precise letter-by-letter display in Arabic
- religious certainty regarding errors

The displayed areas should be considered technical indicators to help users listen back to and improve their recitation.

---

## Roadmap

Planned next steps:

1. Collect user feedback on the demo.
2. Inspect false positives and false negatives.
3. Adjust product thresholds.
4. Add an Arabic word / letter layer.
5. Add deterministic tajwid rules.
6. Have real cases annotated by qualified people.
7. Retrain the model with more user-like data.
8. Turn the prototype into a stable real API.

---

## Disclaimer

This project is experimental.

It must not be used as a religious authority or as a definitive tajwid correction system. The results should be considered a technical aid for listening back and improving recitation.
