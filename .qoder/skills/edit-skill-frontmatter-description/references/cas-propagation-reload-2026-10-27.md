# Cas vérifié — propagation de la description (2026-10-27)

## Sources

- Session `4ce15155-ee0c-4859-8bbd-8c44384aa5b3`, lue le 2026-10-27 (`runtimeState=running`, `revision=11` au premier instantané) puis JSONL relu directement pendant que la session continuait.
- Cible : `edit-skill-frontmatter-description`, état avant l'édition de propagation : 13,196 B, SHA-256 `4f144f2a6e51d7b20b5503d7379ac4c3db62b56a903725f4da02e2aa58981fe6`, description 978 caractères, corps 224 lignes.
- Les valeurs ci-dessous ont été reproduites avec des scripts de lecture indépendants (`injection-probe`, `listing-probe`, puis `scripts/propagation_check.py`) ; elles ne sont pas reprises d'un résumé tiers.

## Chronologie observée (UTC)

| Heure | Événement |
|---|---|
| 12:03:31.286 | L'utilisateur demande « reload skills » ; l'agent ne peut pas exécuter `/skills reload` |
| 12:03:43.662 | `skill_listing` de 97 compétences ; entrée du Skill en nom seul, 36 caractères |
| 12:04:29.758 | Deuxième `skill_listing`, toujours en nom seul |
| 12:04:32.702 | Injection du Skill : première ligne `Base directory for this skill:`, 11 911 caractères |
| 12:05:08.952 | `skill_listing` avec description : segment de 300 caractères, 299 premiers identiques au disque, ellipse finale |
| 12:06:17.714 | `skill_listing` de 98 compétences, même segment |
| 12:10:02.573 / 12:13:23.732 | Listings ultérieurs, même segment : rechargements successifs pendant la relecture |

## Enregistrement d'injection

| Élément | Valeur observée |
|---|---|
| Forme | `type: user`, `isMeta: true`, `message.content` de type chaîne |
| Sorties d'outils | `isMeta: null`, `content` de type liste de `tool_result` |
| Filtre par sous-chaîne | 5 faux positifs (sorties d'outils et scripts de vérification citant la chaîne) |
| Filtre correct | `startswith("Base directory for this skill:")` |
| Première ligne | `C:\Users\Administrateur\.qoder\skills\edit-skill-frontmatter-description`, égale au dossier résolu |
| Corps injecté | texte après la première ligne vide, `strip()` : 11 806 caractères |
| SHA-256 du corps | `eb2a411c48990b79ecf5248eabf23bc473ca0531700a8c82427234ced0f88b80`, égal au corps disque `strip()` |
| Longueurs brutes | injecté 11 807, disque 11 808 |

Le hachage n'est égal qu'après normalisation `strip()` : annoncer « identique après normalisation », pas « octet pour octet ».

## Bloc `ARGUMENTS:` des appels avec arguments

| Élément | Valeur observée |
|---|---|
| Appel | Skill invoqué avec `read-only propagation check for 963-char description` (12:17:06.184Z) |
| Corps injecté brut | 16 542 caractères, SHA-256 `7107c5d4…` : différent du disque malgré un corps à jour |
| Cause | la plateforme ajoute `\n\nARGUMENTS: <args>` après le corps |
| Bloc ajouté | 63 caractères, présent avant `strip()` |
| Après retrait et `strip()` | 16 372 caractères, SHA-256 `fdeef7ed0a501b6352c5df3986f9be8552cdbd3dd1c341f98c6d713998fddf8b`, égal au disque |

`scripts/propagation_check.py` retire ce bloc et expose `arguments_trailer_present` et `arguments_trailer_chars`. Un hachage différent sur un appel avec arguments ne prouve pas un corps périmé.

## Entrées de liste

| Heure | Entrée | Interprétation |
|---|---|---|
| 12:03:43.662 | 36 caractères, nom seul | normal avant rechargement, pas une régression |
| 12:04:29.758 | 36 caractères, nom seul | idem |
| 12:05:08.952 | 338 caractères au total, segment 300, préfixe commun 299, ellipse | couche liste passée à la nouvelle description |
| 12:06:17 / 12:10:02 / 12:13:23 | même segment | rechargements ultérieurs |

Après le préfixe de 299 caractères, le disque contient ` du Skill, ne rempla` ; le 300e caractère de l'entrée est l'ellipse `…`.

## Sentinelles utilisées

| Sentinelle | Occurrences dans le corps injecté |
|---|---|
| `remplacer la ligne de description` | 1 |
| `RESULT PASS` | 2 |
| `description_guard.py` | 3 |

Un compte supérieur à 1 est normal pour un chemin de référence ou un libellé répété ; l'exigence est ≥ 1, avec explication.

## Statuts

| Affirmation | Statut |
|---|---|
| Injection `isMeta` avec dossier exact | observé |
| Égalité du hachage du corps après `strip()` | observé et reproduit |
| Liste passée à la description (299 + ellipse) | observé et reproduit |
| Entrée de liste sans description avant rechargement | observé |
| Panneau client rafraîchi | non vérifié ; action manuelle |

## Règles de réutilisation

- Filtrer `type: user`, `isMeta: true`, puis `startswith` ; ne jamais chercher la chaîne par sous-chaîne.
- Comparer le corps après `strip()` des deux côtés et déclarer la normalisation.
- Retirer un bloc final `ARGUMENTS:` avant le hachage ; sinon un corps à jour paraît périmé.
- N'accepter une preuve de liste que si son horodatage est postérieur au `mtime` de `SKILL.md` ; sinon écrire « liste non vérifiée ».
- Choisir la session par injection exacte (première ligne = dossier résolu), jamais par le JSONL le plus récent : un fichier plus récent peut n'en contenir aucune.
- Une entrée en nom seul n'est pas une panne : elle précède le rechargement.
- Le panneau client reste manuel ; ne jamais écrire dans `SKILL.md` pour forcer un rechargement.
- Sous Windows/Git Bash, ne pas placer un chemin Windows dans `py -3 -c "..."` : écrire un `.py` temporaire hors du Skill et lancer `py -3 -B`.
