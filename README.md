# FASEEH AI V2

FASEEH AI V2 est un prototype privé de feedback phonémique pour la récitation coranique.

Cette version n'est pas encore un correcteur tajwid final. Elle ne dit pas qu'une faute est certaine.

Le système reconnaît le verset récité, compare la récitation avec une référence phonémique, localise des zones temporelles à vérifier, puis retourne un JSON complet utilisable pour une future application.

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
- JSON complet de debug

---

## Format des versets

`ayah_key` désigne un verset au format :

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
114:006
```

Exemple pour sourate Al-Mulk :

```text
067:001
067:002
```

---

## Définitions rapides

### CTC

CTC signifie **Connectionist Temporal Classification**.

C'est la méthode utilisée par le modèle speech-to-text pour apprendre à sortir une séquence de phonèmes sans avoir besoin d'annotations temporelles exactes pour chaque son.

### Forced alignment

Le forced alignment signifie **alignement forcé**.

Le système prend l'audio et la séquence de phonèmes attendue du verset, puis cherche à quel moment chaque phonème attendu apparaît dans l'audio.

### GOP-like scoring

GOP signifie **Goodness of Pronunciation**.

Ici, on utilise une version **GOP-like**, c'est-à-dire un score approximatif qui estime si chaque phonème attendu semble bien soutenu par l'audio.

Ce n'est pas encore un jugement tajwid final.

---

## Modèle utilisé

Le modèle principal actuel est :

```text
models/fasseh_v2_native_iqraeval_10000_001/best
```

Important : ce dossier modèle n'est pas inclus dans GitHub car il est trop lourd.

Pour lancer la démo, il faut récupérer le modèle séparément puis le placer ici :

```text
FASEEH_AI_V2/models/fasseh_v2_native_iqraeval_10000_001/best
```

Chez le créateur du projet, le modèle source se trouve ici :

```text
C:\Users\Admin\Desktop\FASSEHMODEL_V2\models\fasseh_v2_native_iqraeval_10000_001\best
```

Le dossier `best` doit contenir les fichiers du modèle Hugging Face, par exemple :

```text
config.json
model.safetensors
pytorch_model.bin
preprocessor_config.json
tokenizer_config.json
vocab.json
special_tokens_map.json
```

Selon la version du modèle, il peut y avoir soit `model.safetensors`, soit `pytorch_model.bin`.

---

## Structure recommandée du projet

```text
FASEEH_AI_V2/
├── apps/
│   └── fasseh_demo_api.py
├── models/
│   └── fasseh_v2_native_iqraeval_10000_001/
│       └── best/
│           ├── config.json
│           ├── model.safetensors
│           ├── preprocessor_config.json
│           ├── tokenizer_config.json
│           ├── vocab.json
│           └── special_tokens_map.json
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Fichiers à ne pas push sur GitHub

Le dossier du modèle ne doit pas être envoyé sur GitHub.

Exemple de `.gitignore` recommandé :

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.venv/
venv/
env/

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Modèles lourds
models/
*.safetensors
*.bin
*.pt
*.pth

# Audio de test
*.wav
*.mp3
*.flac

# Debug / outputs
outputs/
debug/
```

Important : pour GitHub, on push le code.  
Pour lancer réellement la démo, il faut fournir séparément le dossier modèle en ZIP.

---

## Installation Windows

Cloner le projet :

```bash
git clone https://github.com/TON-USERNAME/FASEEH_AI_V2.git
cd FASEEH_AI_V2
```

Créer un environnement Python :

```bash
python -m venv .venv
```

Activer l'environnement :

```powershell
.\.venv\Scripts\activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

## Ajout du modèle

Créer le dossier du modèle si nécessaire.

Sur Git Bash ou Linux/macOS :

```bash
mkdir -p models/fasseh_v2_native_iqraeval_10000_001/best
```

Sur Windows PowerShell :

```powershell
mkdir models\fasseh_v2_native_iqraeval_10000_001\best
```

Puis copier les fichiers du modèle dans :

```text
models/fasseh_v2_native_iqraeval_10000_001/best
```

Le modèle peut être fourni séparément sous forme de fichier ZIP.

Exemple :

```text
fasseh_v2_native_iqraeval_10000_001_best.zip
```

Après extraction, vérifier que le chemin final est bien :

```text
FASEEH_AI_V2/models/fasseh_v2_native_iqraeval_10000_001/best/config.json
```

et non pas :

```text
FASEEH_AI_V2/models/fasseh_v2_native_iqraeval_10000_001/best/best/config.json
```

---

## Lancer la démo

Toujours dans le dossier du projet :

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"
python -m uvicorn apps.fasseh_demo_api:app --host 127.0.0.1 --port 8000
```

Puis ouvrir dans le navigateur :

```text
http://127.0.0.1:8000
```

---

## Comment tester

1. Choisir un verset court pour commencer.
2. Entrer le `ayah_key`, par exemple :

```text
067:001
```

3. Uploader un fichier audio WAV.
4. Lire le résultat JSON.

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

## Sortie JSON

La démo retourne un JSON avec plusieurs sections :

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

Description des sections :

| Section | Description |
|---|---|
| `decision` | Décision produit globale |
| `display` | Informations que l'application peut afficher |
| `zones_to_show` | Zones temporelles à vérifier |
| `internal` | Scores internes |
| `model_outputs` | Sortie phonémique du modèle |
| `forced_alignment` | Résumé de l'alignement temporel |
| `gop_like` | Zones faibles détectées |
| `raw_debug` | JSON complet de debug |

---

## Wording recommandé

Les scores internes ne doivent pas être affichés comme une note utilisateur.

Bon wording :

```text
Récitation reconnue. Quelques zones peuvent être vérifiées.
```

ou :

```text
Récitation reconnue. Quelques zones sont à vérifier.
```

Wording à éviter :

```text
Tu as fait une faute tajwid certaine.
```

Cette version indique seulement des zones à vérifier.

Le jugement tajwid final nécessitera encore :

- des règles tajwid déterministes
- une calibration des seuils
- des annotations humaines expertes
- des tests sur davantage d'audios utilisateurs
- une amélioration du lien phonèmes → mots → lettres arabes

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
- Rejet du mauvais verset
- Forced alignment avec référence
- GOP-like scoring
- Groupement en zones temporelles
- Filtrage produit
- JSON final pour application

---

## Git : commandes utiles

Initialiser le repo si ce n'est pas encore fait :

```bash
git init
```

Ajouter les fichiers :

```bash
git add .
```

Faire un commit :

```bash
git commit -m "Initial FASEEH AI V2 baseline"
```

Ajouter le dépôt distant GitHub :

```bash
git remote add origin https://github.com/TON-USERNAME/FASEEH_AI_V2.git
```

Pousser sur GitHub :

```bash
git branch -M main
git push -u origin main
```

Vérifier les fichiers suivis par Git :

```bash
git status
```

Vérifier que le dossier `models/` n'est pas push :

```bash
git status --ignored
```

---

## Distribution du modèle

Le code peut être envoyé sur GitHub.

Le modèle doit être partagé séparément, par exemple en ZIP :

```text
fasseh_v2_native_iqraeval_10000_001_best.zip
```

La personne qui reçoit le projet doit placer le modèle ici :

```text
FASEEH_AI_V2/models/fasseh_v2_native_iqraeval_10000_001/best
```

---
