# Bilan du projet FASSEH AI V2

Ce document résume l'état du projet FASSEH jusqu'à la baseline actuelle.

FASSEH AI V2 est aujourd'hui une pipeline complète de feedback phonémique pour la récitation coranique. Le système ne se limite plus à prédire une suite de phonèmes : il peut reconnaître si l'audio correspond probablement au bon verset, produire une décision produit, localiser des zones temporelles à vérifier, calculer des scores internes et générer un JSON exploitable par une future application.

Important : cette version n'est pas encore un correcteur tajwid final. Elle ne doit pas affirmer qu'une faute est certaine. Elle indique seulement des zones à vérifier.

---

## Sommaire

1. [Résumé rapide](#résumé-rapide)
2. [État actuel du projet](#état-actuel-du-projet)
3. [Modèle actuel](#modèle-actuel)
4. [Ce qui existe déjà](#ce-qui-existe-déjà)
5. [Ce qui manque encore](#ce-qui-manque-encore)
6. [Début du projet : exploration des données](#début-du-projet--exploration-des-données)
7. [Premiers tests sur Al-Fatiha](#premiers-tests-sur-al-fatiha)
8. [Nettoyage et audit des références phonémiques](#nettoyage-et-audit-des-références-phonémiques)
9. [Construction de la V1 produit](#construction-de-la-v1-produit)
10. [Référence Hafs : ayah, mots, phonèmes et lettres](#référence-hafs--ayah-mots-phonèmes-et-lettres)
11. [Tests contrôlés sur erreurs volontaires](#tests-contrôlés-sur-erreurs-volontaires)
12. [Premiers tests user-like avec RetaSy](#premiers-tests-user-like-avec-retasy)
13. [Passage vers quran_phonemizer](#passage-vers-quran_phonemizer)
14. [Construction du pack V2 natif](#construction-du-pack-v2-natif)
15. [Premiers entraînements V2](#premiers-entraînements-v2)
16. [Scorer produit V2](#scorer-produit-v2)
17. [Modèle IqraEval 2845](#modèle-iqraeval-2845)
18. [Alignement temporel](#alignement-temporel)
19. [GOP-like scoring](#gop-like-scoring)
20. [Groupement des zones faibles](#groupement-des-zones-faibles)
21. [Filtrage produit des zones](#filtrage-produit-des-zones)
22. [JSON final pour application](#json-final-pour-application)
23. [Fichiers importants](#fichiers-importants)
24. [Limites actuelles](#limites-actuelles)
25. [Prochaines étapes](#prochaines-étapes)
26. [Conclusion](#conclusion)

---

## Résumé rapide

La V1 a prouvé que le concept produit était possible : prendre un audio, un verset attendu, comparer la récitation à une référence phonémique, puis produire un retour exploitable.

La V2 native a ensuite remplacé l'alphabet phonémique maison par une base plus propre construite avec `quran_phonemizer`.

La baseline actuelle ajoute une capacité importante : la localisation temporelle. Grâce au forced alignment et au GOP-like scoring, le système peut maintenant indiquer des zones précises à vérifier dans l'audio.

Le projet est donc passé d'un simple modèle de reconnaissance phonémique à une pipeline produit complète.

---

## État actuel du projet

Nom de la baseline actuelle :

```text
FASSEH V2 BASELINE 003
```

Cette baseline contient :

- un ASR phonémique V2 ;
- un scorer produit V2 ;
- un rejet probable du mauvais verset ;
- des warnings doux ;
- un forced alignment avec la référence phonémique ;
- un GOP-like scoring par phonème ;
- un groupement des phonèmes faibles en zones temporelles ;
- un filtrage produit des zones à afficher ;
- un JSON final utilisable par une application.

Le système peut actuellement :

1. recevoir un audio et un `ayah_key` ;
2. prédire une séquence de phonèmes V2 ;
3. comparer la prédiction avec la référence attendue ;
4. décider si le verset est probablement reconnu ou non ;
5. localiser des zones faibles dans le temps ;
6. produire un message utilisateur prudent ;
7. retourner un JSON complet pour debug et intégration app.

---

## Modèle actuel

Le modèle principal actuel est :

```text
models\fasseh_v2_native_iqraeval_10000_001\best
```

Même si le nom du dossier contient `10000`, ce modèle a réellement été entraîné sur :

```text
2 845 exemples IqraEval matchés proprement
```

Ces exemples ont été reconstruits avec les références phonémiques V2 basées sur `quran_phonemizer`.

Métriques approximatives du modèle actuel :

| Métrique | Valeur |
|---|---:|
| `eval_loss` | 0.5404 |
| `eval_per` | 0.1225 |
| `eval_score` | 87.75 |
| PER moyen sur Naba, tests Redwane | ~0.072 |
| PER sur Ayat al-Kursi, test Redwane | ~0.1453 |
| Rejet des mauvais versets | 6/6 |

Ce modèle est actuellement la meilleure baseline ASR phonémique du projet.

---

## Ce qui existe déjà

Le projet possède déjà les éléments suivants :

| Élément | Statut |
|---|---|
| ASR phonémique V2 | Oui |
| Scorer produit V2 | Oui |
| Rejet du mauvais verset | Oui |
| Warnings doux | Oui |
| JSON app | Oui |
| Alignement temporel fiable | Oui |
| GOP par phonème | Oui |

---

## Ce qui manque encore

Le projet n'a pas encore les éléments suivants :

| Élément | Statut |
|---|---|
| Filtres produit parfaitement calibrés | À améliorer |
| Gestion fine fin de verset / waqf | À améliorer en priorité |
| Tests larges sur erreurs volontaires | À faire |
| Tests larges sur RetaSy / user-like | À faire |
| Règles tajwid déterministes | À construire |
| Annotations expertes | À obtenir |
| Dataset massif user-like | À construire |

Priorités immédiates :

1. améliorer les filtres produit, surtout sur les fins de verset et le waqf ;
2. tester la baseline sur davantage d'erreurs volontaires ;
3. tester la pipeline sur plus d'audios RetaSy ou user-like.

---

## Début du projet : exploration des données

Au début du projet, plusieurs sources de données audio liées à la récitation coranique ont été explorées.

Les sources étudiées incluaient notamment :

- IqraEval ;
- des datasets de récitations professionnelles ;
- des datasets plus proches d'utilisateurs réels ;
- des audios de test enregistrés manuellement.

L'objectif initial était de vérifier si un modèle de speech recognition arabe pouvait être adapté à une tâche spécifique : non pas transcrire du texte arabe classique, mais reconnaître une suite de phonèmes correspondant à une récitation coranique.

Les premières étapes ont consisté à :

- inspecter les datasets ;
- vérifier les chemins audio ;
- convertir certains fichiers en WAV 16 kHz ;
- créer des manifests exploitables pour l'entraînement ;
- préparer des références phonémiques pour les premiers tests.

---

## Premiers tests sur Al-Fatiha

Al-Fatiha a servi de cas de test contrôlé.

Des références phonémiques ont été générées ou récupérées pour les versets. Plusieurs modèles CTC basés sur wav2vec2 ont ensuite été entraînés et comparés.

Les premières versions testées incluaient :

- un modèle phonémique entraîné sur un petit subset ;
- un modèle entraîné sur un dataset plus large ;
- une adaptation spécifique sur des récitations professionnelles.

À ce stade, IqraEval servait surtout de benchmark externe. Il permettait de vérifier si les modèles entraînés sur d'autres données généralisaient un minimum sur des audios différents, en particulier sur Al-Fatiha.

---

## Nettoyage et audit des références phonémiques

Les premiers résultats étaient parfois difficiles à interpréter.

Plusieurs problèmes ont été identifiés :

- références phonémiques bruitées ;
- différences de notation entre datasets ;
- voyelles longues ou courtes incohérentes ;
- styles de récitation non adaptés ;
- lectures comme Warsh alors que le projet visait une référence Hafs ;
- fichiers audio manquants ;
- doublons ;
- colonnes CSV incomplètes ou mal formées.

Une étape importante d'audit et de nettoyage a donc été ajoutée.

Cette étape consistait à :

- vérifier les phonèmes ;
- supprimer les entrées problématiques ;
- exclure les styles non adaptés ;
- contrôler les doublons ;
- vérifier que les fichiers audio existaient ;
- nettoyer les colonnes essentielles des CSV.

Ce nettoyage a permis d'obtenir un dataset professionnel plus strict et plus fiable, utilisé ensuite comme base principale pour l'adaptation du modèle.

---

## Construction de la V1 produit

Après le nettoyage, plusieurs modèles ont été comparés sur les mêmes références.

Les tests sur Al-Fatiha avec les références IqraEval ont montré que le modèle entraîné sur le dataset professionnel propre obtenait les meilleurs résultats parmi les versions testées.

Cette phase a permis de clarifier la direction du projet : il ne fallait pas viser directement le tajwid détaillé dès le départ. Il fallait d'abord construire une base robuste capable de :

1. reconnaître si l'utilisateur récite globalement le bon verset ;
2. mesurer la proximité phonémique ;
3. localiser progressivement les erreurs ;
4. ajouter ensuite une couche tajwid plus fine.

La V1 produit a donc été construite autour de cette logique.

À partir d'un audio et d'un `ayah_key`, le système pouvait :

- prédire une séquence de phonèmes ;
- comparer la prédiction avec la référence attendue ;
- calculer des scores internes ;
- produire un JSON exploitable par une application.

Le JSON V1 contenait notamment :

- un score global ;
- le PER ;
- les erreurs importantes ;
- les warnings doux ;
- les mots colorés ;
- les lettres approximatives suspectes ;
- une décision produit claire.

Les décisions produit possibles étaient par exemple :

```text
accept
check_some_zones
reject
retry_uncertain_audio
```

La V1 séparait aussi plusieurs niveaux de jugement :

| Score | Rôle |
|---|---|
| `memory_score` | Vérifier si c'est probablement le bon verset |
| `phoneme_score` | Évaluer les sons principaux |
| `vowel_score` | Évaluer les voyelles et durées |
| `confidence_score` | Évaluer la fiabilité globale |
| `tajweed_score` | Prévu plus tard pour les règles fines |

L'idée importante était de ne pas être trop dur.

Une différence du type `u` vs `uu`, une durée imprécise ou une variation de fin de mot ne doit pas être traitée comme une faute de lettre certaine. Elle doit plutôt être classée comme zone à vérifier ou comme futur warning tajwid.

---

## Référence Hafs : ayah, mots, phonèmes et lettres

Une autre étape importante a été la construction d'une référence Hafs plus propre.

Objectif :

```text
ayah → mots → phonèmes → lettres arabes
```

Une map Hafs a été créée avec des overrides manuels pour corriger les frontières entre mots et phonèmes.

Au début, plusieurs versets étaient marqués en `needs_review`.

Après l'ajout des overrides, la map est passée à :

```text
0 ayah à revoir
```

Les entrées ont ensuite été classées avec des statuts comme :

```text
manual_verified
high_auto
```

Cette étape est essentielle. Le modèle peut donner un bon score global, mais pour afficher précisément une lettre en vert, orange ou rouge, il faut que l'alignement entre phonèmes, mots et lettres soit beaucoup plus stable.

---

## Tests contrôlés sur erreurs volontaires

La pipeline a ensuite été testée sur des erreurs contrôlées.

Six cas ont été enregistrés sur le verset :

```text
001:002
```

Les six cas étaient :

1. récitation correcte ;
2. mauvaise lettre volontaire ;
3. mauvaise voyelle ;
4. mot oublié ;
5. mauvais verset ;
6. prolongation volontairement trop longue.

Le système a validé les six familles de comportement :

| Cas testé | Comportement observé |
|---|---|
| Récitation correcte | Reconnue correctement |
| Mauvaise lettre | Détection dans `الْعَالَمِينَ` |
| Mauvaise voyelle | Signalement dans `رَبِّ` |
| Mot oublié | Repéré |
| Mauvais verset | Confiance fortement diminuée |
| Prolongation trop longue | Classée comme warning doux |

Cette phase a confirmé que la logique produit commençait à fonctionner.

Le système ne se limite plus à un score brut : il produit une interprétation exploitable.

---

## Premiers tests user-like avec RetaSy

RetaSy a ensuite été utilisé comme source d'audios plus proches d'utilisateurs réels.

Étapes réalisées :

- export de 300 audios ;
- contournement des problèmes TorchCodec ;
- export sans décodage Python ;
- conversion avec ffmpeg ;
- inférence des `ayah_key` à partir du texte arabe présent dans les métadonnées.

Sur les 300 audios :

```text
80 audios étaient scorables avec la map Hafs actuelle
```

Parmi eux :

```text
33 audios exploitables pour une première évaluation externe
```

Répartition :

| Classe | Nombre |
|---|---:|
| `clean_user_like` | 6 |
| `usable_user_like_with_checks` | 9 |
| `imperfect_user_like` | 18 |

Résultats moyens observés :

| Classe | `memory_score` moyen | Observation |
|---|---:|---|
| `clean_user_like` | ~95.5 | Quasiment aucune erreur importante |
| `usable_user_like_with_checks` | ~86.7 | Utilisable avec vérifications |
| `imperfect_user_like` | ~71.6 | Plus d'erreurs importantes |

Cette évaluation a donné une première base réaliste pour calibrer les seuils produit.

RetaSy reste cependant bruité et pas toujours facile à utiliser comme dataset propre.

---

## Passage vers quran_phonemizer

La V1 restait utile, mais elle utilisait encore un alphabet phonémique maison ou compatible.

Cette limite devenait problématique pour aller vers un diagnostic tajwid plus fin.

Le projet a donc commencé à intégrer :

```text
quran_phonemizer
```

Objectif :

- construire un alphabet phonémique plus propre ;
- utiliser une base plus sérieuse pour les phénomènes de récitation ;
- préparer une future couche tajwid ;
- éviter de forcer les références dans l'ancien alphabet V1.

Les premières étapes ont été :

1. inspecter la librairie ;
2. comparer les références V1 avec les sorties `quran_phonemizer` sur Al-Fatiha ;
3. générer une première référence pour Sourate An-Naba ;
4. produire deux formats :
   - une sortie native `quran_phonemizer` ;
   - une conversion compatible V1.

Les tests sur les audios de Naba ont montré que la conversion V1 était imparfaite, notamment sur :

- les shadda ;
- les doubles consonnes ;
- les fins de verset ;
- les durées ;
- le tanwīn ;
- la ghunnah.

Conclusion : à long terme, il valait mieux entraîner directement un modèle avec l'alphabet natif de `quran_phonemizer`.

---

## Construction du pack V2 natif

Un pack V2 natif basé sur `quran_phonemizer` a ensuite été construit.

Ce pack contient :

- des références phonémiques natives pour tout le Coran ;
- des CSV par sourate ;
- un vocabulaire V2 ;
- un tokenizer V2 ;
- un manifest d'entraînement reliant les audios professionnels aux nouvelles cibles phonémiques.

Le fichier principal des références V2 contient :

```text
6236 ayahs
```

Le vocabulaire V2 natif contient :

```text
36 tokens
```

Le manifest d'entraînement disponible à ce stade contenait :

```text
456 audios professionnels
```

Il faut distinguer deux choses :

| Élément | Couverture |
|---|---|
| Références V2 | Tout le Coran |
| Audios d'entraînement disponibles à ce stade | 456 audios professionnels |

Les références couvrent donc tout le Coran, mais le modèle n'était entraîné que sur les audios disponibles.

---

## Premiers entraînements V2

Le premier entraînement V2 natif a échoué en pratique.

Le modèle tournait, mais prédisait presque uniquement :

```text
w
```

ou rien.

Les métriques étaient mauvaises :

| Métrique | Valeur approximative |
|---|---:|
| `eval_per` | ~0.976 |
| `eval_score` | ~2/100 |

Un test overfit a ensuite été créé sur quelques audios répétés.

Objectif : vérifier si le problème venait du vocabulaire, du CSV, de `quran_phonemizer` ou du script d'entraînement.

Le test overfit a été concluant :

| Métrique | Résultat |
|---|---:|
| `eval_per` | 0.0 |
| `eval_score` | 100 |

Cela a prouvé que la pipeline V2 native était techniquement valide et que le modèle pouvait apprendre l'alphabet `quran_phonemizer`.

Un entraînement V2 plus intelligent a ensuite été lancé avec :

- feature encoder non gelé ;
- learning rate plus fort ;
- 200 exemples d'entraînement ;
- 40 exemples d'évaluation ;
- 10 epochs ;
- batch size 1 ;
- gradient accumulation 4.

Résultat :

| Métrique | Valeur approximative |
|---|---:|
| `eval_loss` | ~0.508 |
| `eval_per` | ~0.102 |
| `eval_score` | ~89.77 |

Les décodages sur le split d'évaluation ont montré que le modèle produisait maintenant de vraies séquences phonétiques V2.

Beaucoup de versets étaient entre :

```text
0.0 et 0.05 de PER
```

Quelques cas plus difficiles étaient entre :

```text
0.10 et 0.25 de PER
```

Cela a confirmé que le modèle V2 natif fonctionnait réellement.

---

## Tests V2 sur audios personnels

Le modèle V2 a ensuite été testé sur :

- Ayat al-Kursi ;
- les 12 premiers versets de Sourate An-Naba.

Sur les 12 versets de Naba, les PER étaient globalement bons :

```text
souvent entre 0.06 et 0.18
```

Un verset a même été reconnu avec :

```text
PER = 0.0
```

La moyenne approximative sur Naba tournait autour de :

```text
0.13 de PER
```

Sur Ayat al-Kursi, le PER était autour de :

```text
0.1985
```

Ce résultat restait encourageant vu la longueur du verset.

Le modèle suivait bien la structure générale, même s'il ratait encore des détails comme :

- les durées ;
- la nasalisation ;
- les fins de mot ;
- certains sons proches.

Conclusion : le modèle V2 reconnaissait globalement la récitation et le bon verset, mais il fallait construire une couche de scoring produit plus intelligente avant de parler d'erreurs précises.

---

## Scorer produit V2

Le scorer produit V2 a ensuite été construit.

Script principal :

```text
scripts\score_ayah_v2_native_product.py
```

Ce scorer prend :

- un fichier audio ;
- un `ayah_key`.

Le `ayah_key` désigne l'identifiant du verset au format :

```text
sourate:verset
```

Exemples :

```text
078:001
002:255
```

Le scorer :

1. prédit les phonèmes V2 ;
2. compare la prédiction avec la référence issue de :

```text
outputs\v2_native\quran_refs_v2_native_full.csv
```

3. calcule des scores internes ;
4. sépare les erreurs importantes des warnings doux ;
5. produit une décision produit.

Les décisions produit peuvent être :

```text
recognized
recognized_with_checks
probably_wrong_ayah
audio_uncertain
```

Le scorer ne doit pas afficher une note brute à l'utilisateur.

Il doit plutôt afficher un message prudent comme :

```text
Récitation reconnue. Quelques zones sont à vérifier.
```

et non :

```text
Tu as 54 %.
```

Le scorer sépare notamment :

- les erreurs importantes ;
- les warnings doux ;
- les zones incertaines ;
- les différences de voyelles ;
- les fins de verset ;
- les variations de waqf ;
- les éléments comme `:` et `ŋ` ;
- les substitutions de consonnes importantes.

---

## Validation du scorer V2

Le scorer V2 a été validé sur les audios Redwane :

- les 12 premiers versets de Sourate An-Naba ;
- Ayat al-Kursi ;
- des tests de mauvais versets.

Sur les bons versets, le système reconnaissait correctement les récitations.

Sur les mauvais couples audio / `ayah_key`, il rejetait correctement les 6 cas testés :

```text
6/6 mauvais versets rejetés
```

Cela a confirmé que le scorer ne se contente pas de donner un score phonémique. Il sait aussi distinguer un bon verset d'un mauvais verset probable.

Les premières erreurs importantes restantes étaient principalement des substitutions de consonnes comme :

```text
Z -> D
k -> q
T -> q
Z -> d
```

Ces cas n'ont pas été supprimés automatiquement.

Ils devront être inspectés humainement, car ce sont exactement les familles de sons importantes qu'il ne faut pas lisser sans preuve.

---

## Modèle IqraEval 2845

IqraEval a ensuite été repris plus proprement.

Au début du projet, une première tentative avait utilisé beaucoup d'exemples IqraEval de manière trop naïve, avec l'alphabet phonémique du dataset.

Cette approche posait problème, car cet alphabet ne correspondait pas parfaitement au vocabulaire V2.

La nouvelle stratégie a été différente :

1. utiliser l'audio IqraEval ;
2. utiliser le texte arabe IqraEval ;
3. matcher le texte arabe avec les ayahs de référence ;
4. régénérer les cibles phonémiques avec `quran_phonemizer` ;
5. garder une cohérence totale avec le vocabulaire V2.

Un premier pilot sur 200 exemples a amélioré les résultats :

| Test | Résultat approximatif |
|---|---:|
| PER moyen sur Naba | ~0.09 |
| PER sur Ayat al-Kursi | ~0.1788 |
| Rejet mauvais versets | 6/6 |

Un manifest plus grand a ensuite été généré.

Même si l'objectif initial était 10 000 lignes, le script a trouvé :

```text
2 845 exemples
```

Ces 2 845 exemples sont ceux dont le texte arabe matchait proprement une ayah des références V2.

Ce n'est pas une erreur : le matching strict texte arabe → ayah a gardé seulement les exemples les plus propres.

Le modèle entraîné sur ces 2 845 exemples est :

```text
models\fasseh_v2_native_iqraeval_10000_001\best
```

Métriques approximatives :

| Métrique | Valeur |
|---|---:|
| `eval_loss` | 0.5404 |
| `eval_per` | 0.1225 |
| `eval_score` | 87.75 |
| PER moyen sur Naba, tests Redwane | ~0.072 |
| PER sur Ayat al-Kursi | ~0.1453 |
| Rejet mauvais versets | 6/6 |

Ce modèle est actuellement la meilleure baseline ASR phonémique du projet.

---

## Alignement temporel

Une première couche d'alignement temporel a ensuite été ajoutée.

L'objectif de l'alignement temporel est de savoir où se trouve chaque phonème dans l'audio.

Sans alignement, le système peut dire qu'un phonème est suspect, mais il ne sait pas précisément à quel moment l'utilisateur doit réécouter.

Avec l'alignement, le système peut produire des informations du type :

```text
Zone à vérifier entre 3.49s et 3.57s
```

Une première V0 d'alignement CTC a été créée.

CTC signifie :

```text
Connectionist Temporal Classification
```

C'est la méthode utilisée par wav2vec2 pour produire une séquence de phonèmes sans annotation temporelle frame par frame.

La V0 fonctionnait, mais elle alignait surtout ce que le modèle pensait avoir entendu. Elle était utile techniquement, mais pas suffisante pour localiser chaque phonème attendu du verset.

---

## Forced alignment référence

Un forced alignment référence V1 a ensuite été construit.

Script principal :

```text
scripts\forced_align_v2_reference.py
```

Le forced alignment consiste à forcer le modèle à aligner l'audio avec la séquence de phonèmes attendue, et non seulement avec la séquence prédite.

En pratique, on donne au système :

- l'audio ;
- le `ayah_key` ;
- la référence phonémique attendue.

Le système cherche ensuite à quel moment chaque phonème attendu apparaît dans l'audio.

Cette étape permet de passer de :

```text
Le modèle a prédit quelque chose de proche.
```

à :

```text
Voici où chaque phonème attendu se situe dans le temps.
```

Résultats observés :

| Test | Résultat |
|---|---|
| Naba 1 à 12 | Tous les phonèmes attendus alignés |
| `missing_alignment_count` sur Naba | 0 partout |
| Ayat al-Kursi | Alignement réussi |
| Ayat al-Kursi, phonèmes attendus | 358 |
| Ayat al-Kursi, durée audio | ~50 secondes |
| Ayat al-Kursi, phonèmes non alignés | 0 |

Cela montre que la méthode n'est pas spécifique à Sourate An-Naba. Elle est générique et peut s'appliquer à n'importe quelle ayah, tant que l'on dispose de :

- l'audio ;
- le `ayah_key` ;
- le modèle V2 ;
- le vocabulaire V2 ;
- les références phonémiques du Coran.

---

## GOP-like scoring

À partir du forced alignment, des scores de qualité par phonème ont été calculés.

Ces scores sont appelés ici :

```text
GOP-like
```

GOP signifie :

```text
Goodness of Pronunciation
```

L'idée du GOP est d'estimer, pour chaque phonème attendu, à quel point l'audio soutient bien ce phonème.

Exemple :

Si le phonème attendu est :

```text
q
```

le système regarde la probabilité que le modèle donne à `q` sur les frames temporelles alignées.

Dans cette version, le GOP-like n'est pas encore un GOP académique parfaitement calibré. C'est une première version pratique.

Chaque phonème reçoit :

- un timestamp ;
- une durée ;
- une probabilité moyenne du phonème attendu ;
- une qualité.

Qualités possibles :

```text
good
check
weak
very_weak
```

Cela permet de repérer des zones faibles sans prétendre détecter une faute tajwid certaine.

---

## Groupement des zones faibles

Des scripts ont ensuite été créés pour extraire et grouper les phonèmes faibles.

Script d'extraction :

```text
scripts\extract_v2_weak_phonemes.py
```

Ce script extrait les phonèmes classés :

```text
check
weak
very_weak
missing_alignment
```

Script de groupement :

```text
scripts\group_v2_weak_phoneme_zones.py
```

Ce script regroupe les phonèmes proches dans le temps.

Objectif : éviter d'afficher une erreur par phonème.

Par exemple, au lieu d'afficher séparément :

```text
u
w
n
:
:
```

le système peut regrouper tout cela en une seule zone de fin de verset.

La sortie contient des zones avec :

- début ;
- fin ;
- durée ;
- tokens concernés ;
- indices de référence ;
- sévérité ;
- message utilisateur.

Cette étape est essentielle pour rendre le feedback utilisable dans une application.

L'utilisateur ne doit pas recevoir une liste brute de 50 phonèmes. Il doit recevoir quelques zones claires à réécouter.

---

## Filtrage produit des zones

Un filtre produit a ensuite été ajouté.

Script principal :

```text
scripts\filter_v2_gop_product_zones.py
```

Ce filtre décide :

- quelles zones doivent être affichées à l'utilisateur ;
- quelles zones doivent être masquées ;
- quelles zones doivent être adoucies ;
- quelles zones doivent être traitées comme variation douce.

Les tokens suivants sont traités prudemment :

- voyelles simples ;
- `:`;
- `ŋ`;
- fins de verset ;
- durées ;
- variations de waqf.

Les consonnes importantes sont traitées plus strictement, par exemple :

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

Le système distingue plusieurs classes produit :

```text
important_check
light_check
soft_warning
hide_or_soft
```

Cette couche n'est pas définitive, mais elle réduit déjà fortement le bruit.

Exemple observé sur Ayat al-Kursi :

| Étape | Nombre de zones |
|---|---:|
| Zones brutes GOP-like | 42 |
| Zones conservées pour affichage | 15 |

Les autres zones ont été masquées ou adoucies.

---

## JSON final pour application

Le JSON final destiné à l'application a été construit.

Script principal :

```text
scripts\build_v2_app_feedback_json.py
```

Ce JSON combine :

- le scorer produit V2 ;
- les sorties du modèle ;
- les erreurs importantes ;
- les warnings doux ;
- les zones incertaines ;
- le forced alignment ;
- les zones GOP-like filtrées.

Structure générale :

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

La section `display` est prévue pour l'application.

Elle contient notamment :

```text
main_message
zones_to_show
show_score_to_user = false
```

Le message utilisateur reste prudent :

```text
Récitation reconnue. Quelques zones sont à vérifier.
```

Les zones sont présentées comme des zones à vérifier, pas comme des fautes certaines.

Le JSON donne beaucoup d'informations à l'application, tout en permettant de choisir ce qui sera vraiment montré à l'utilisateur.

---

## Fichiers importants

Fichiers et dossiers importants de la baseline actuelle :

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

## Limites actuelles

La baseline actuelle est fonctionnelle, mais elle a encore des limites importantes.

Le système ne doit pas être présenté comme un correcteur tajwid final.

Le GOP-like actuel est une première approximation de qualité phonémique. Ce n'est pas une preuve définitive d'erreur.

Les zones suivantes doivent encore être calibrées :

- fins de verset ;
- waqf ;
- voyelles longues ;
- nasalisation ;
- durée ;
- tanwīn ;
- ghunnah ;
- sons proches ;
- substitutions de consonnes importantes.

Certaines zones comme :

```text
n : :
```

en fin de verset, ou :

```text
L L
```

dans Ayat al-Kursi, doivent probablement être adoucies dans le filtre produit.

Les major errors restantes doivent être inspectées humainement, notamment les substitutions de consonnes importantes.

Il faudra aussi tester la pipeline sur :

- plus d'audios user-like ;
- des erreurs volontaires contrôlées ;
- plusieurs voix ;
- plusieurs micros ;
- différents environnements sonores ;
- des datasets externes comme RetaSy.

La couche tajwid déterministe reste à construire.

Elle devra utiliser :

- des règles tajwid par ayah ;
- les timestamps ;
- les durées ;
- les scores GOP-like ;
- les annotations humaines.

---

## Prochaines étapes

Les prochaines étapes prioritaires sont les suivantes.

### 1. Améliorer les filtres produit

Priorité forte :

```text
fin de verset / waqf
```

Objectifs :

- réduire les faux positifs ;
- mieux distinguer les variations acceptables ;
- éviter d'afficher trop de zones faibles ;
- garder les vraies substitutions importantes.

---

### 2. Tester sur erreurs volontaires

Créer davantage de tests contrôlés :

- mauvaise lettre ;
- mauvaise voyelle ;
- mot oublié ;
- mauvais verset ;
- prolongation trop longue ;
- nasalisation exagérée ;
- ghunnah absente ;
- qalqalah absente ou trop forte ;
- madd trop court ou trop long.

Objectif : vérifier que chaque famille d'erreur est traitée avec le bon niveau de sévérité.

---

### 3. Tester sur RetaSy et audios user-like

Objectifs :

- tester plus de voix ;
- tester plus de micros ;
- tester plus de conditions audio ;
- mieux calibrer les seuils ;
- identifier les faux rejets ;
- identifier les faux warnings.

---

### 4. Relier phonèmes, mots et lettres arabes

Objectif : améliorer le passage suivant :

```text
phonèmes → mots → lettres arabes
```

Cela permettra plus tard d'afficher précisément :

- le mot concerné ;
- la lettre concernée ;
- la zone audio correspondante ;
- le type de problème probable.

---

### 5. Ajouter les règles tajwid déterministes

La future couche tajwid devra ajouter des règles explicites, par exemple :

- madd ;
- ghunnah ;
- ikhfa ;
- idgham ;
- iqlab ;
- qalqalah ;
- règles de waqf ;
- règles liées aux lettres emphatiques ;
- règles liées aux voyelles longues.

Ces règles devront être croisées avec :

- la référence phonémique ;
- l'alignement temporel ;
- les durées ;
- le GOP-like ;
- les annotations expertes.

---

### 6. Ajouter des annotations expertes

Les annotations humaines expertes seront nécessaires pour passer progressivement de :

```text
zone à vérifier
```

à :

```text
diagnostic de plus en plus fiable
```

Ces annotations permettront de calibrer :

- les seuils ;
- les messages ;
- la sévérité ;
- les faux positifs ;
- les faux négatifs.

---

## Conclusion

La V1 a prouvé le concept produit.

La V2 native a apporté un alphabet phonémique plus propre grâce à `quran_phonemizer`.

Le modèle IqraEval 2845 a amélioré la reconnaissance phonémique et constitue aujourd'hui la meilleure baseline ASR du projet.

La baseline actuelle, FASSEH V2 BASELINE 003, ajoute une capacité essentielle : la localisation temporelle des zones faibles grâce au forced alignment et au GOP-like scoring.

Le projet est maintenant capable de produire un JSON app avec :

- décision produit ;
- message utilisateur ;
- zones temporelles à vérifier ;
- scores internes ;
- sorties modèle ;
- données de forced alignment ;
- données GOP-like ;
- informations de debug.

La prochaine grande étape n'est pas de réentraîner à l'aveugle.

La priorité est maintenant de :

1. tester la baseline sur plus de cas réels ;
2. calibrer les zones affichées ;
3. améliorer la gestion fin de verset / waqf ;
4. relier les phonèmes aux mots et lettres arabes ;
5. ajouter les règles tajwid déterministes ;
6. intégrer des annotations expertes.

À ce stade, FASSEH AI V2 est une base solide pour une future application de feedback de récitation, mais le wording doit rester prudent : le système indique des zones à vérifier, pas des fautes tajwid certaines.
