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
   - [CTC](#ctc)
   - [Forced alignment](#forced-alignment)
   - [GOP-like scoring](#gop-like-scoring)
5. [Structure recommandée du projet](#structure-recommandée-du-projet)
6. [Installation Windows](#installation-windows)
7. [Lancer la démo](#lancer-la-démo)
8. [Comment tester](#comment-tester)
9. [Sortie JSON](#sortie-json)
10. [Wording recommandé](#wording-recommandé)
11. [État actuel](#état-actuel)

---

## Présentation générale

FASEEH AI V2 est conçu pour analyser une récitation coranique à partir d'un fichier audio WAV.

L'utilisateur fournit un fichier audio ainsi qu'un `ayah_key`, c'est-à-dire l'identifiant du verset attendu. Le système utilise ensuite un modèle phonémique pour reconnaître la récitation, comparer l'audio avec la référence attendue, puis produire une sortie structurée.

Le but de cette version est de fournir un feedback technique et exploitable pour une future interface utilisateur.

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

---

## Format des versets

`ayah_key` désigne un verset au format suivant :

```text
sourate:verset
