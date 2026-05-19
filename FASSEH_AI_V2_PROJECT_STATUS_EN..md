# FASSEH AI V2 Project Status Report

This document summarizes the state of the FASSEH project up to the current baseline.

FASSEH AI V2 is now a complete phonemic feedback pipeline for Quranic recitation. The system no longer only predicts a sequence of phonemes: it can recognize whether the audio probably matches the correct verse, produce a product decision, localize time ranges to review, calculate internal scores, and generate JSON that can be used by a future application.

Important: this version is not yet a final tajwid corrector. It must not claim that an error is certain. It only indicates areas to review.

---

## Table of Contents

1. [Quick Summary](#quick-summary)
2. [Current State of the Project](#current-state-of-the-project)
3. [Current Model](#current-model)
4. [What Already Exists](#what-already-exists)
5. [What Is Still Missing](#what-is-still-missing)
6. [Project Beginning: Data Exploration](#project-beginning--data-exploration)
7. [First Tests on Al-Fatiha](#first-tests-on-al-fatiha)
8. [Cleaning and Auditing Phonemic References](#cleaning-and-auditing-phonemic-references)
9. [Building the Product V1](#building-the-product-v1)
10. [Hafs Reference: Ayah, Words, Phonemes, and Letters](#hafs-reference--ayah-words-phonemes-and-letters)
11. [Controlled Tests on Intentional Errors](#controlled-tests-on-intentional-errors)
12. [First User-like Tests with RetaSy](#first-user-like-tests-with-retasy)
13. [Transition to quran_phonemizer](#transition-to-quran_phonemizer)
14. [Building the Native V2 Pack](#building-the-native-v2-pack)
15. [First V2 Training Runs](#first-v2-training-runs)
16. [Product Scorer V2](#product-scorer-v2)
17. [IqraEval 2845 Model](#iqraeval-2845-model)
18. [Temporal Alignment](#temporal-alignment)
19. [GOP-like Scoring](#gop-like-scoring)
20. [Grouping Weak Zones](#grouping-weak-zones)
21. [Product Filtering of Zones](#product-filtering-of-zones)
22. [Final JSON for the Application](#final-json-for-the-application)
23. [Important Files](#important-files)
24. [Current Limitations](#current-limitations)
25. [Next Steps](#next-steps)
26. [Conclusion](#conclusion)

---

## Quick Summary

V1 proved that the product concept was possible: take an audio file, an expected verse, compare the recitation with a phonemic reference, then produce usable feedback.

The native V2 then replaced the custom phonemic alphabet with a cleaner foundation built with `quran_phonemizer`.

The current baseline adds an important capability: temporal localization. Thanks to forced alignment and GOP-like scoring, the system can now indicate precise zones to review in the audio.

The project has therefore moved from a simple phonemic recognition model to a complete product pipeline.

---

## Current State of the Project

Name of the current baseline:

```text
FASSEH V2 BASELINE 003
```

This baseline includes:

- a V2 phonemic ASR;
- a V2 product scorer;
- probable wrong-ayah rejection;
- soft warnings;
- forced alignment with the phonemic reference;
- GOP-like scoring per phoneme;
- grouping of weak phonemes into time zones;
- product filtering of zones to display;
- a final JSON output usable by an application.

The system can currently:

1. receive an audio file and an `ayah_key`;
2. predict a V2 phoneme sequence;
3. compare the prediction with the expected reference;
4. decide whether the verse is probably recognized or not;
5. localize weak zones in time;
6. produce a cautious user-facing message;
7. return a complete JSON output for debugging and app integration.

---

## Current Model

The current main model is:

```text
models\fasseh_v2_native_iqraeval_10000_001\best
```

Even though the folder name contains `10000`, this model was actually trained on:

```text
2,845 cleanly matched IqraEval examples
```

These examples were rebuilt with V2 phonemic references based on `quran_phonemizer`.

Approximate metrics of the current model:

| Metric | Value |
|---|---:|
| `eval_loss` | 0.5404 |
| `eval_per` | 0.1225 |
| `eval_score` | 87.75 |
| Average PER on Naba, tests | ~0.072 |
| PER on Ayat al-Kursi, test | ~0.1453 |
| Wrong-ayah rejection | 6/6 |

This model is currently the best phonemic ASR baseline of the project.

---

## What Already Exists

The project already includes the following elements:

| Element | Status |
|---|---|
| V2 phonemic ASR | Yes |
| V2 product scorer | Yes |
| Wrong-ayah rejection | Yes |
| Soft warnings | Yes |
| App JSON | Yes |
| Reliable temporal alignment | Yes |
| GOP per phoneme | Yes |

---

## What Is Still Missing

The project does not yet include the following elements:

| Element | Status |
|---|---|
| Perfectly calibrated product filters | To improve |
| Fine handling of verse endings / waqf | High-priority improvement |
| Large-scale tests on intentional errors | To do |
| Large-scale tests on RetaSy / user-like audio | To do |
| Deterministic tajwid rules | To build |
| Expert annotations | To obtain |
| Massive user-like dataset | To build |

Immediate priorities:

1. improve product filters, especially for verse endings and waqf;
2. test the baseline on more intentional errors;
3. test the pipeline on more RetaSy or user-like audio samples.

---

## Project Beginning: Data Exploration

At the beginning of the project, several audio data sources related to Quranic recitation were explored.

The studied sources included in particular:

- IqraEval;
- professional recitation datasets;
- datasets closer to real users;
- manually recorded test audio files.

The initial objective was to verify whether an Arabic speech recognition model could be adapted to a specific task: not transcribing classical Arabic text, but recognizing a sequence of phonemes corresponding to Quranic recitation.

The first steps consisted of:

- inspecting datasets;
- checking audio paths;
- converting some files to 16 kHz WAV;
- creating manifests usable for training;
- preparing phonemic references for the first tests.

---

## First Tests on Al-Fatiha

Al-Fatiha served as a controlled test case.

Phonemic references were generated or retrieved for the verses. Several CTC models based on wav2vec2 were then trained and compared.

The first tested versions included:

- a phonemic model trained on a small subset;
- a model trained on a larger dataset;
- a specific adaptation on professional recitations.

At this stage, IqraEval mainly served as an external benchmark. It made it possible to check whether models trained on other data generalized at least minimally to different audio samples, especially on Al-Fatiha.

---

## Cleaning and Auditing Phonemic References

The first results were sometimes difficult to interpret.

Several problems were identified:

- noisy phonemic references;
- notation differences between datasets;
- inconsistent long or short vowels;
- unsuitable recitation styles;
- readings such as Warsh while the project targeted a Hafs reference;
- missing audio files;
- duplicates;
- incomplete or malformed CSV columns.

An important audit and cleaning step was therefore added.

This step consisted of:

- checking phonemes;
- removing problematic entries;
- excluding unsuitable styles;
- checking duplicates;
- verifying that audio files existed;
- cleaning the essential CSV columns.

This cleaning made it possible to obtain a stricter and more reliable professional dataset, later used as the main basis for model adaptation.

---

## Building the Product V1

After cleaning, several models were compared on the same references.

The tests on Al-Fatiha with the IqraEval references showed that the model trained on the clean professional dataset obtained the best results among the tested versions.

This phase helped clarify the direction of the project: the goal should not be to target detailed tajwid directly from the start. The first step had to be building a robust foundation capable of:

1. recognizing whether the user is generally reciting the correct verse;
2. measuring phonemic proximity;
3. progressively localizing errors;
4. adding a finer tajwid layer later.

The product V1 was therefore built around this logic.

From an audio file and an `ayah_key`, the system could:

- predict a sequence of phonemes;
- compare the prediction with the expected reference;
- calculate internal scores;
- produce JSON usable by an application.

The V1 JSON included in particular:

- a global score;
- PER;
- major errors;
- soft warnings;
- colored words;
- approximate suspicious letters;
- a clear product decision.

Possible product decisions were, for example:

```text
accept
check_some_zones
reject
retry_uncertain_audio
```

V1 also separated several levels of judgment:

| Score | Role |
|---|---|
| `memory_score` | Check whether it is probably the correct verse |
| `phoneme_score` | Evaluate the main sounds |
| `vowel_score` | Evaluate vowels and durations |
| `confidence_score` | Evaluate overall reliability |
| `tajweed_score` | Planned later for fine-grained rules |

The important idea was not to be too strict.

A difference such as `u` vs `uu`, an imprecise duration, or a word-ending variation should not be treated as a certain letter mistake. It should instead be classified as a zone to review or as a future tajwid warning.

---

## Hafs Reference: Ayah, Words, Phonemes, and Letters

Another important step was building a cleaner Hafs reference.

Objective:

```text
ayah → words → phonemes → Arabic letters
```

A Hafs map was created with manual overrides to correct boundaries between words and phonemes.

At first, several verses were marked as `needs_review`.

After adding the overrides, the map reached:

```text
0 ayah to review
```

Entries were then classified with statuses such as:

```text
manual_verified
high_auto
```

This step is essential. The model can give a good global score, but to precisely display a letter in green, orange, or red, the alignment between phonemes, words, and letters must be much more stable.

---

## Controlled Tests on Intentional Errors

The pipeline was then tested on controlled errors.

Six cases were recorded on the verse:

```text
001:002
```

The six cases were:

1. correct recitation;
2. intentional wrong letter;
3. wrong vowel;
4. omitted word;
5. wrong verse;
6. intentionally over-extended prolongation.

The system validated the six families of behavior:

| Tested case | Observed behavior |
|---|---|
| Correct recitation | Correctly recognized |
| Wrong letter | Detection in `الْعَالَمِينَ` |
| Wrong vowel | Flagged in `رَبِّ` |
| Omitted word | Detected |
| Wrong verse | Confidence strongly decreased |
| Over-extended prolongation | Classified as a soft warning |

This phase confirmed that the product logic was starting to work.

The system no longer limits itself to a raw score: it produces a usable interpretation.

---

## First User-like Tests with RetaSy

RetaSy was then used as a source of audio samples closer to real users.

Steps completed:

- export of 300 audio samples;
- workaround for TorchCodec issues;
- export without Python decoding;
- conversion with ffmpeg;
- inference of `ayah_key` values from the Arabic text present in the metadata.

Out of the 300 audio samples:

```text
80 audio samples were scorable with the current Hafs map
```

Among them:

```text
33 audio samples were usable for a first external evaluation
```

Distribution:

| Class | Count |
|---|---:|
| `clean_user_like` | 6 |
| `usable_user_like_with_checks` | 9 |
| `imperfect_user_like` | 18 |

Average observed results:

| Class | Average `memory_score` | Observation |
|---|---:|---|
| `clean_user_like` | ~95.5 | Almost no major errors |
| `usable_user_like_with_checks` | ~86.7 | Usable with checks |
| `imperfect_user_like` | ~71.6 | More major errors |

This evaluation provided a first realistic basis for calibrating product thresholds.

However, RetaSy remains noisy and is not always easy to use as a clean dataset.

---

## Transition to quran_phonemizer

V1 remained useful, but it still used a custom or compatible phonemic alphabet.

This limitation was becoming problematic for moving toward a finer tajwid diagnosis.

The project therefore started integrating:

```text
quran_phonemizer
```

Objective:

- build a cleaner phonemic alphabet;
- use a more serious foundation for recitation phenomena;
- prepare a future tajwid layer;
- avoid forcing references into the old V1 alphabet.

The first steps were:

1. inspect the library;
2. compare V1 references with `quran_phonemizer` outputs on Al-Fatiha;
3. generate a first reference for Surah An-Naba;
4. produce two formats:
   - a native `quran_phonemizer` output;
   - a V1-compatible conversion.

Tests on Naba audio samples showed that the V1 conversion was imperfect, especially for:

- shadda;
- double consonants;
- verse endings;
- durations;
- tanwīn;
- ghunnah.

Conclusion: in the long term, it was better to train a model directly with the native `quran_phonemizer` alphabet.

---

## Building the Native V2 Pack

A native V2 pack based on `quran_phonemizer` was then built.

This pack contains:

- native phonemic references for the entire Quran;
- CSV files by surah;
- a V2 vocabulary;
- a V2 tokenizer;
- a training manifest linking professional audio files to the new phonemic targets.

The main V2 reference file contains:

```text
6236 ayahs
```

The native V2 vocabulary contains:

```text
36 tokens
```

The training manifest available at this stage contained:

```text
456 professional audio samples
```

Two things must be distinguished:

| Element | Coverage |
|---|---|
| V2 references | Entire Quran |
| Training audio available at this stage | 456 professional audio samples |

The references therefore cover the entire Quran, but the model was trained only on the available audio samples.

---

## First V2 Training Runs

The first native V2 training run failed in practice.

The model was running, but it predicted almost only:

```text
w
```

or nothing.

The metrics were poor:

| Metric | Approximate value |
|---|---:|
| `eval_per` | ~0.976 |
| `eval_score` | ~2/100 |

An overfit test was then created on a few repeated audio samples.

Objective: check whether the problem came from the vocabulary, the CSV, `quran_phonemizer`, or the training script.

The overfit test was successful:

| Metric | Result |
|---|---:|
| `eval_per` | 0.0 |
| `eval_score` | 100 |

This proved that the native V2 pipeline was technically valid and that the model could learn the `quran_phonemizer` alphabet.

A smarter V2 training run was then launched with:

- unfrozen feature encoder;
- stronger learning rate;
- 200 training examples;
- 40 evaluation examples;
- 10 epochs;
- batch size 1;
- gradient accumulation 4.

Result:

| Metric | Approximate value |
|---|---:|
| `eval_loss` | ~0.508 |
| `eval_per` | ~0.102 |
| `eval_score` | ~89.77 |

The decodings on the evaluation split showed that the model was now producing real V2 phonetic sequences.

Many verses were between:

```text
0.0 and 0.05 PER
```

A few more difficult cases were between:

```text
0.10 and 0.25 PER
```

This confirmed that the native V2 model was actually working.

---

## V2 Tests on Personal Audio

The V2 model was then tested on:

- Ayat al-Kursi;
- the first 12 verses of Surah An-Naba.

On the 12 Naba verses, the PER values were generally good:

```text
often between 0.06 and 0.18
```

One verse was even recognized with:

```text
PER = 0.0
```

The approximate average on Naba was around:

```text
0.13 PER
```

On Ayat al-Kursi, the PER was around:

```text
0.1985
```

This result remained encouraging given the length of the verse.

The model followed the general structure well, even though it still missed details such as:

- durations;
- nasalization;
- word endings;
- some close sounds.

Conclusion: the V2 model generally recognized the recitation and the correct verse, but a smarter product scoring layer had to be built before talking about precise errors.

---

## Product Scorer V2

The product scorer V2 was then built.

Main script:

```text
scripts\score_ayah_v2_native_product.py
```

This scorer takes:

- an audio file;
- an `ayah_key`.

The `ayah_key` designates the verse identifier in the following format:

```text
surah:verse
```

Examples:

```text
078:001
002:255
```

The scorer:

1. predicts V2 phonemes;
2. compares the prediction with the reference from:

```text
outputs\v2_native\quran_refs_v2_native_full.csv
```

3. calculates internal scores;
4. separates major errors from soft warnings;
5. produces a product decision.

Possible product decisions are:

```text
recognized
recognized_with_checks
probably_wrong_ayah
audio_uncertain
```

The scorer must not display a raw score to the user.

It should instead display a cautious message such as:

```text
Recitation recognized. Some zones should be reviewed.
```

and not:

```text
You scored 54%.
```

The scorer separates in particular:

- major errors;
- soft warnings;
- uncertain zones;
- vowel differences;
- verse endings;
- waqf variations;
- elements such as `:` and `ŋ`;
- important consonant substitutions.

---

## Validation of the V2 Scorer

The V2 scorer was validated on audio samples from:

- the first 12 verses of Surah An-Naba;
- Ayat al-Kursi;
- wrong-ayah tests.

On correct verses, the system recognized the recitations correctly.

On wrong audio / `ayah_key` pairs, it correctly rejected the 6 tested cases:

```text
6/6 wrong verses rejected
```

This confirmed that the scorer does not simply give a phonemic score. It can also distinguish a correct verse from a probable wrong verse.

The remaining first major errors were mainly consonant substitutions such as:

```text
Z -> D
k -> q
T -> q
Z -> d
```

These cases were not automatically removed.

They will need to be inspected by humans, because these are exactly the important sound families that should not be smoothed over without evidence.

---

## IqraEval 2845 Model

IqraEval was then revisited more cleanly.

At the beginning of the project, a first attempt had used many IqraEval examples too naively, with the dataset's phonemic alphabet.

This approach was problematic because that alphabet did not perfectly match the V2 vocabulary.

The new strategy was different:

1. use the IqraEval audio;
2. use the IqraEval Arabic text;
3. match the Arabic text with reference ayahs;
4. regenerate phonemic targets with `quran_phonemizer`;
5. keep full consistency with the V2 vocabulary.

A first pilot on 200 examples improved the results:

| Test | Approximate result |
|---|---:|
| Average PER on Naba | ~0.09 |
| PER on Ayat al-Kursi | ~0.1788 |
| Wrong-ayah rejection | 6/6 |

A larger manifest was then generated.

Although the initial target was 10,000 rows, the script found:

```text
2,845 examples
```

These 2,845 examples are those whose Arabic text cleanly matched an ayah from the V2 references.

This is not an error: the strict Arabic text → ayah matching kept only the cleanest examples.

The model trained on these 2,845 examples is:

```text
models\fasseh_v2_native_iqraeval_10000_001\best
```

Approximate metrics:

| Metric | Value |
|---|---:|
| `eval_loss` | 0.5404 |
| `eval_per` | 0.1225 |
| `eval_score` | 87.75 |
| Average PER on Naba, tests | ~0.072 |
| PER on Ayat al-Kursi | ~0.1453 |
| Wrong-ayah rejection | 6/6 |

This model is currently the best phonemic ASR baseline of the project.

---

## Temporal Alignment

A first temporal alignment layer was then added.

The goal of temporal alignment is to know where each phoneme is located in the audio.

Without alignment, the system can say that a phoneme is suspicious, but it does not know precisely where the user should listen again.

With alignment, the system can produce information such as:

```text
Zone to review between 3.49s and 3.57s
```

A first V0 CTC alignment was created.

CTC means:

```text
Connectionist Temporal Classification
```

It is the method used by wav2vec2 to produce a sequence of phonemes without frame-by-frame temporal annotation.

V0 worked, but it mainly aligned what the model thought it had heard. It was technically useful, but not sufficient to localize each expected phoneme of the verse.

---

## Reference Forced Alignment

A reference forced alignment V1 was then built.

Main script:

```text
scripts\forced_align_v2_reference.py
```

Forced alignment consists of forcing the model to align the audio with the expected phoneme sequence, not only with the predicted sequence.

In practice, the system is given:

- the audio;
- the `ayah_key`;
- the expected phonemic reference.

The system then searches for the moment when each expected phoneme appears in the audio.

This step makes it possible to move from:

```text
The model predicted something close.
```

to:

```text
Here is where each expected phoneme is located in time.
```

Observed results:

| Test | Result |
|---|---|
| Naba 1 to 12 | All expected phonemes aligned |
| `missing_alignment_count` on Naba | 0 everywhere |
| Ayat al-Kursi | Successful alignment |
| Ayat al-Kursi, expected phonemes | 358 |
| Ayat al-Kursi, audio duration | ~50 seconds |
| Ayat al-Kursi, unaligned phonemes | 0 |

This shows that the method is not specific to Surah An-Naba. It is generic and can apply to any ayah, as long as the following are available:

- the audio;
- the `ayah_key`;
- the V2 model;
- the V2 vocabulary;
- the Quran phonemic references.

---

## GOP-like Scoring

From forced alignment, quality scores were calculated per phoneme.

These scores are referred to here as:

```text
GOP-like
```

GOP means:

```text
Goodness of Pronunciation
```

The idea of GOP is to estimate, for each expected phoneme, how strongly the audio supports that phoneme.

Example:

If the expected phoneme is:

```text
q
```

the system looks at the probability that the model assigns to `q` on the aligned time frames.

In this version, GOP-like is not yet a perfectly calibrated academic GOP. It is a first practical version.

Each phoneme receives:

- a timestamp;
- a duration;
- an average probability of the expected phoneme;
- a quality label.

Possible qualities:

```text
good
check
weak
very_weak
```

This makes it possible to identify weak zones without claiming to detect a certain tajwid error.

---

## Grouping Weak Zones

Scripts were then created to extract and group weak phonemes.

Extraction script:

```text
scripts\extract_v2_weak_phonemes.py
```

This script extracts phonemes classified as:

```text
check
weak
very_weak
missing_alignment
```

Grouping script:

```text
scripts\group_v2_weak_phoneme_zones.py
```

This script groups phonemes that are close in time.

Objective: avoid displaying one error per phoneme.

For example, instead of displaying separately:

```text
u
w
n
:
:
```

the system can group all of this into a single verse-ending zone.

The output contains zones with:

- start time;
- end time;
- duration;
- affected tokens;
- reference indices;
- severity;
- user-facing message.

This step is essential to make the feedback usable in an application.

The user should not receive a raw list of 50 phonemes. They should receive a few clear zones to listen to again.

---

## Product Filtering of Zones

A product filter was then added.

Main script:

```text
scripts\filter_v2_gop_product_zones.py
```

This filter decides:

- which zones should be displayed to the user;
- which zones should be hidden;
- which zones should be softened;
- which zones should be treated as soft variation.

The following tokens are handled cautiously:

- simple vowels;
- `:`;
- `ŋ`;
- verse endings;
- durations;
- waqf variations.

Important consonants are handled more strictly, for example:

```text
q
k
S
D
T
Z
2
3
H
```

The system distinguishes several product classes:

```text
important_check
light_check
soft_warning
hide_or_soft
```

This layer is not final, but it already reduces noise significantly.

Example observed on Ayat al-Kursi:

| Step | Number of zones |
|---|---:|
| Raw GOP-like zones | 42 |
| Zones kept for display | 15 |

The other zones were hidden or softened.

---

## Final JSON for the Application

The final JSON intended for the application was built.

Main script:

```text
scripts\build_v2_app_feedback_json.py
```

This JSON combines:

- the V2 product scorer;
- model outputs;
- major errors;
- soft warnings;
- uncertain zones;
- forced alignment;
- filtered GOP-like zones.

General structure:

```text
decision
display
zones_to_show
internal
model_outputs
forced_alignment
gop_like
raw_debug
```

The `display` section is intended for the application.

It includes in particular:

```text
main_message
zones_to_show
show_score_to_user = false
```

The user-facing message remains cautious:

```text
Recitation recognized. Some zones should be reviewed.
```

The zones are presented as zones to review, not as certain mistakes.

The JSON gives a lot of information to the application while still allowing the app to choose what will actually be shown to the user.

---

## Important Files

Important files and folders of the current baseline:

```text
models\fasseh_v2_native_iqraeval_10000_001\best
```

```text
scripts\score_ayah_v2_native_product.py
scripts\forced_align_v2_reference.py
scripts\extract_v2_weak_phonemes.py
scripts\group_v2_weak_phoneme_zones.py
scripts\filter_v2_gop_product_zones.py
scripts\build_v2_app_feedback_json.py
```

```text
outputs\v2_native\quran_refs_v2_native_full.csv
```

```text
outputs\v2_product_eval_report_iqraeval_2845_001.csv
outputs\v2_wrong_ayah_eval_report_iqraeval_2845_001.csv
outputs\v2_forced_alignment_summary_iqraeval_2845.csv
outputs\v2_gop_product_zones_iqraeval_2845.csv
outputs\v2_app_feedback_index_iqraeval_2845.csv
```

---

## Current Limitations

The current baseline is functional, but it still has important limitations.

The system must not be presented as a final tajwid corrector.

The current GOP-like score is a first approximation of phonemic quality. It is not definitive proof of an error.

The following zones still need to be calibrated:

- verse endings;
- waqf;
- long vowels;
- nasalization;
- duration;
- tanwīn;
- ghunnah;
- close sounds;
- important consonant substitutions.

Some zones such as:

```text
n : :
```

at the end of a verse, or:

```text
L L
```

in Ayat al-Kursi, should probably be softened in the product filter.

The remaining major errors must be inspected by humans, especially important consonant substitutions.

The pipeline will also need to be tested on:

- more user-like audio;
- controlled intentional errors;
- several voices;
- several microphones;
- different sound environments;
- external datasets such as RetaSy.

The deterministic tajwid layer still needs to be built.

It will need to use:

- tajwid rules per ayah;
- timestamps;
- durations;
- GOP-like scores;
- human annotations.

---

## Next Steps

The next priority steps are the following.

### 1. Improve Product Filters

High priority:

```text
verse ending / waqf
```

Objectives:

- reduce false positives;
- better distinguish acceptable variations;
- avoid displaying too many weak zones;
- keep true important substitutions.

---

### 2. Test on Intentional Errors

Create more controlled tests:

- wrong letter;
- wrong vowel;
- omitted word;
- wrong verse;
- over-extended prolongation;
- exaggerated nasalization;
- missing ghunnah;
- missing or excessive qalqalah;
- madd too short or too long.

Objective: verify that each error family is handled with the right severity level.

---

### 3. Test on RetaSy and User-like Audio

Objectives:

- test more voices;
- test more microphones;
- test more audio conditions;
- better calibrate thresholds;
- identify false rejections;
- identify false warnings.

---

### 4. Link Phonemes, Words, and Arabic Letters

Objective: improve the following mapping:

```text
phonemes → words → Arabic letters
```

This will later make it possible to display precisely:

- the affected word;
- the affected letter;
- the corresponding audio zone;
- the probable type of issue.

---

### 5. Add Deterministic Tajwid Rules

The future tajwid layer will need to add explicit rules, for example:

- madd;
- ghunnah;
- ikhfa;
- idgham;
- iqlab;
- qalqalah;
- waqf rules;
- rules related to emphatic letters;
- rules related to long vowels.

These rules will need to be cross-checked with:

- the phonemic reference;
- temporal alignment;
- durations;
- GOP-like scores;
- expert annotations.

---

### 6. Add Expert Annotations

Expert human annotations will be necessary to gradually move from:

```text
zone to review
```

to:

```text
increasingly reliable diagnosis
```

These annotations will make it possible to calibrate:

- thresholds;
- messages;
- severity;
- false positives;
- false negatives.

---

## Conclusion

V1 proved the product concept.

The native V2 brought a cleaner phonemic alphabet thanks to `quran_phonemizer`.

The IqraEval 2845 model improved phonemic recognition and is currently the best ASR baseline of the project.

The current baseline, FASSEH V2 BASELINE 003, adds an essential capability: temporal localization of weak zones thanks to forced alignment and GOP-like scoring.

The project can now produce app JSON with:

- product decision;
- user-facing message;
- time zones to review;
- internal scores;
- model outputs;
- forced alignment data;
- GOP-like data;
- debug information.

The next major step is not blind retraining.

The priority is now to:

1. test the baseline on more real cases;
2. calibrate displayed zones;
3. improve verse-ending / waqf handling;
4. link phonemes to words and Arabic letters;
5. add deterministic tajwid rules;
6. integrate expert annotations.

At this stage, FASSEH AI V2 is a solid foundation for a future recitation feedback application, but the wording must remain cautious: the system indicates zones to review, not certain tajwid mistakes.
