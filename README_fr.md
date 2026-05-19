# FASEEH AI V2

FASEEH AI V2 est un prototype privé de feedback phonémique pour la récitation coranique.

Cette version n'est pas encore un correcteur tajwid final. Elle ne confirme pas qu'une faute est certaine. Elle permet plutôt d'identifier des zones temporelles à vérifier dans une récitation.

Le système reconnaît le verset récité, compare la récitation avec une référence phonémique, localise les zones qui semblent faibles ou incohérentes, puis retourne un JSON complet utilisable pour une future application.

---

## Sommaire

1. [Présentation générale](#présentation-générale)
2. [Fonctionnalités](#fonctionnalités)
3. [Format des versets](#format-des-versets)
4. [Définitions rapides](#définitions-rapides)
5. [Modèle utilisé](#modèle-utilisé)
6. [Structure recommandée du projet](#structure-recommandée-du-projet)
7. [Installation Windows](#installation-windows)
8. [Installation Mac / Linux](#installation-mac--linux)
9. [Lancer la démo](#lancer-la-démo)
10. [Comment tester](#comment-tester)
11. [Sortie JSON](#sortie-json)
12. [Wording recommandé](#wording-recommandé)
13. [État actuel](#état-actuel)
14. [Limites actuelles](#limites-actuelles)
15. [Roadmap](#roadmap)
16. [Avertissement](#avertissement)

---

## Présentation générale

FASEEH AI V2 est conçu pour analyser une récitation coranique à partir d'un fichier audio WAV.

L'utilisateur fournit un fichier audio ainsi qu'un `ayah_key`, c'est-à-dire l'identifiant du verset attendu. Le système utilise ensuite un modèle phonémique pour reconnaître la récitation, comparer l'audio avec la référence attendue, puis produire une sortie structurée.

Le but de cette version est de fournir un feedback technique exploitable pour une future interface utilisateur.

Important : cette version ne doit pas être présentée comme un jugement religieux ou tajwid définitif. Elle indique seulement des zones qui peuvent mériter une vérification.

---

## Fonctionnalités

- Upload d'un fichier audio WAV
- Saisie d'un `ayah_key`, par exemple `067:001`
- Reconnaissance phonémique avec un modèle wav2vec2 CTC
- Scoring produit V2
- Rejet probable du mauvais verset
- Forced alignment avec la référence phonémique
- GOP-like scoring
- Détection de zones temporelles à vérifier
- Retour d'un JSON complet de debug
- Interface locale simple via FastAPI
- Compatible Windows, Mac et Linux si les chemins sont correctement configurés

---

## Format des versets

`ayah_key` désigne un verset au format suivant :

```text
sourate:verset
```

Exemples :

```text
001:001
067:001
078:001
112:001
002:255
```

Pour les premiers tests, il est conseillé d'utiliser des versets courts :

```text
001:001 à 001:007
067:001
078:001 à 078:012
112:001 à 112:004
113:001 à 113:005
114:001 à 114:006
```

Les longs versets comme `002:255` peuvent fonctionner, mais ils génèrent plus de zones à vérifier.

---

## Définitions rapides

### CTC

`CTC` signifie `Connectionist Temporal Classification`.

C'est une méthode utilisée en reconnaissance vocale pour apprendre à prédire une séquence de caractères ou de phonèmes sans avoir besoin de connaître à l'avance le timing exact de chaque son.

Dans FASEEH AI V2, le modèle reçoit l'audio et prédit une suite de phonèmes.

### Phonème

Un phonème est une unité sonore. Ici, le modèle ne cherche pas seulement à transcrire du texte arabe classique. Il cherche à reconnaître une suite de sons correspondant à une récitation coranique.

Exemple simplifié :

```text
t a b a a R a k a
```

### PER

`PER` signifie `Phoneme Error Rate`.

C'est un taux d'erreur entre la séquence phonémique attendue et la séquence prédite par le modèle.

Dans ce projet, le PER reste une métrique interne. Il ne doit pas être affiché comme une note utilisateur brute.

### Forced alignment

`Forced alignment` signifie alignement forcé.

Le système prend l'audio et la séquence de phonèmes attendue du verset, puis cherche à quel moment chaque phonème attendu apparaît dans l'audio.

Cela permet d'obtenir des timings comme :

```json
{
  "token": "q",
  "start": 6.94,
  "end": 6.96
}
```

### GOP-like scoring

`GOP` signifie `Goodness of Pronunciation`.

Ici, on utilise une version `GOP-like`, c'est-à-dire un score approximatif qui estime si chaque phonème attendu semble bien soutenu par l'audio.

Ce n'est pas encore un jugement tajwid final. C'est un signal technique utilisé pour repérer des zones faibles.

### Waqf

Le `waqf` correspond à l'arrêt ou à la pause dans la récitation. Dans cette version, les différences de fin de mot ou de fin de verset sont traitées avec prudence.

### Ghunnah / Tanwin / Madd

Ces éléments font partie du tajwid. La version actuelle peut parfois détecter des zones liées à la nasalisation, aux voyelles longues ou aux fins de récitation, mais elle ne certifie pas encore les règles tajwid de manière finale.

---

## Modèle utilisé

Le modèle principal actuel est :

```text
models/fasseh_v2_native_iqraeval_10000_001/best
```

Important : ce dossier modèle n'est pas inclus dans GitHub car il contient des fichiers lourds.

Pour lancer la démo, il faut récupérer le modèle séparément puis le placer ici :

```text
FASEEH_AI_V2/models/fasseh_v2_native_iqraeval_10000_001/best
```

Le dossier `best` doit contenir les fichiers du modèle Hugging Face, par exemple :

```text
config.json
model.safetensors
preprocessor_config.json
tokenizer_config.json
vocab.json
special_tokens_map.json
```

Si ce dossier est absent, l'application ne pourra pas analyser les audios.

---

## Structure recommandée du projet

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

## Installation Windows

Ouvrir un terminal PowerShell dans le dossier du projet :

```powershell
cd C:\Users\Admin\Desktop\FASEEH_AI_V2
```

Créer un environnement Python :

```powershell
python -m venv .venv
```

Activer l'environnement :

```powershell
.\.venv\Scripts\activate
```

Installer les dépendances :

```powershell
pip install -r requirements.txt
```

Si `uvicorn` ou `fastapi` manque, installer manuellement :

```powershell
pip install fastapi uvicorn python-multipart
```

Si les dépendances audio ou modèle manquent :

```powershell
pip install torch transformers numpy pandas soundfile librosa scipy safetensors
```

---

## Installation Mac / Linux

Ouvrir un terminal dans le dossier du projet :

```bash
cd FASEEH_AI_V2
```

Créer un environnement Python :

```bash
python3 -m venv .venv
```

Activer l'environnement :

```bash
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Si besoin :

```bash
pip install fastapi uvicorn python-multipart torch transformers numpy pandas soundfile librosa scipy safetensors
```

---

## Lancer la démo

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

Puis ouvrir dans le navigateur :

```text
http://127.0.0.1:8000
```

---

## Comment tester

1. Ouvrir la page locale.
2. Entrer un `ayah_key`, par exemple `067:001`.
3. Uploader un fichier WAV.
4. Cliquer sur `Analyser`.
5. Lire le JSON retourné.

Le système retournera une décision générale, des scores internes, les phonèmes prédits, l'alignement temporel, et les zones à vérifier.

---

## Sortie JSON

La démo retourne un JSON avec plusieurs sections :

- `decision` : décision produit globale
- `display` : ce que l'application peut afficher
- `zones_to_show` : zones temporelles à vérifier
- `internal` : scores internes
- `model_outputs` : sortie phonémique du modèle
- `forced_alignment` : résumé de l'alignement temporel
- `gop_like` : zones faibles détectées
- `raw_debug` : JSON complet de debug

Exemple de décision positive :

```json
{
  "decision": "recognized",
  "display": {
    "show_score_to_user": false,
    "main_message": "Récitation reconnue."
  }
}
```

Exemple avec zones à vérifier :

```json
{
  "decision": "recognized_with_checks",
  "display": {
    "show_score_to_user": false,
    "main_message": "Récitation reconnue. Quelques zones sont à vérifier.",
    "num_zones_to_show": 2
  }
}
```

---

## Wording recommandé

Les scores sont internes. Il ne faut pas afficher une note brute à l'utilisateur.

Bon wording :

```text
Récitation reconnue.
```

ou :

```text
Récitation reconnue. Quelques zones peuvent être vérifiées.
```

ou :

```text
Vérifie cette zone de récitation.
```

Mauvais wording :

```text
Tu as fait une faute tajwid certaine.
```

ou :

```text
Tu récites à 54 %.
```

Cette version indique seulement des zones à vérifier. Elle ne certifie pas encore des erreurs tajwid.

---

## État actuel

Nom de la baseline :

```text
FASSEH V2 BASELINE 003
```

Modèle actuel :

```text
models/fasseh_v2_native_iqraeval_10000_001/best
```

Cette baseline contient :

- ASR phonémique V2
- Scorer produit V2
- Rejet mauvais verset
- Forced alignment référence
- GOP-like scoring
- Groupement en zones temporelles
- Filtrage produit
- JSON final pour app

---

## Limites actuelles

Cette version n'a pas encore :

- jugement tajwid final
- règles déterministes complètes pour madd, ghunnah, ikhfa, idgham, qalqalah, etc.
- calibration experte sur un grand dataset utilisateur
- annotation humaine suffisante
- affichage précis lettre par lettre en arabe
- certitude religieuse sur les erreurs

Les zones affichées doivent être considérées comme des indices techniques pour aider à réécouter la récitation.

---

## Roadmap

Prochaines étapes prévues :

1. Collecter des retours utilisateurs sur la démo.
2. Inspecter les faux positifs et faux négatifs.
3. Ajuster les seuils produit.
4. Ajouter une couche mot / lettre arabe.
5. Ajouter des règles tajwid déterministes.
6. Faire annoter des cas réels par des personnes compétentes.
7. Réentraîner le modèle avec davantage de données user-like.
8. Transformer le prototype en vraie API stable.

---

## Avertissement

Ce projet est expérimental.

Il ne doit pas être utilisé comme autorité religieuse ou correction tajwid définitive. Les résultats doivent être considérés comme une aide technique à la réécoute et à l'amélioration.
