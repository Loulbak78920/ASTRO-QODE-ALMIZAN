# Preuves — session 7b17d684-a43b-45e9-b265-a2b37026a622

## Cadre de lecture

- Session lue par `read_chat_session` avec `turnLimit=12`, `includeToolOutputs=true`, `maxOutputCharsPerItem=6000`.
- Snapshot : `runtimeState=ready`, `activeTurnId=null`, `revision=113`, 13 messages, `hasMoreBefore=false`.
- Titre enregistré : « 创建 Triniter 等离子体观测者 Skill ». La chaîne Markdown → PDF occupe les messages 2 à 11 du snapshot ; elle ne correspond pas au titre, qui vise la création d'un autre Skill.
- Seules les sorties d'outils et les messages utilisateur sont utilisées comme preuves. Les phrases de l'assistant ne sont retenues que si une sortie les étaye.
- Horodatage : messages en UTC (`2026-10-27T15:13:35.929Z` pour le premier tour) ; sorties d'outils en heure locale UTC+1 (`16:26`, `16:29`, `16:30`).

## Faits étayés

| Fait | Preuve observée | Statut |
|---|---|---|
| `start` renvoie 0 sans ouvrir de fenêtre | Deux appels Bash : `RC=0` puis sortie vide ; `assoc .md` échoue ensuite | SUPPORTED |
| `.md` sans association | `Exit code 1` + « Association de fichier introuvable pour l'extension .md » + « Le type de fichier 'Markdown.Document' n'a pas été trouvé » | SUPPORTED |
| `.pdf` sans association | « Association de fichier introuvable pour l'extension .pdf » | SUPPORTED |
| Repli VS Code | Découverte de `Code.exe` (exit 2 lors du balayage des `bin`), puis titre `RAPPORT_...md - Visual Studio Code` | SUPPORTED |
| Rendu sans dépendance Node | `Traceback ... no marked` lors d'un essai Node ; le rendu final est produit par un script Python local | SUPPORTED |
| Première version : liste ordonnée perdue | `rapport.html 5553 octets`, `tables 2 | h1 1 | h2 7 | li 5 | pre 1 | strong 4 | code 40` — aucune entrée `ol` | SUPPORTED (fusion signalée par l'assistant, corroborée par `li=5` au lieu de 8) |
| Correction du rendu | 3 `Edit` réussis, puis `5620 octets`, `tables 2 | h1 1 | h2 7 | ul 1 | ol 1 | li 8 | pre 1`, `items ol: 3`, `backticks litteraux: 0 | lignes pipe: 0` | SUPPORTED |
| PDF produit | `244516 bytes written`, `%PDF-1.4`, `/Type /Page` = 2, `/Count` = 2, `pypdf pages 2`, `p1 chars 1433`, `%%EOF` | SUPPORTED |
| Échec cp1252 après contrôles | `UnicodeEncodeError ... cp1252` en imprimant le texte extrait ; les valeurs étaient déjà sorties et le processus a fini en `Exit code 1` | SUPPORTED |
| Nettoyage | `rapport.html 7032` et `rendre_md.py 5643`, puis « No such file or directory » pour `%TEMP%\rapport_preview` | SUPPORTED |

## Points non étayés ou ambigus

- **« 5 条无序列表 » (recommandation)** : la sortie finale ne donne que `ul 1 | ol 1 | li 8` et `items ol: 3`. Le nombre 5 s'obtient par 8 − 3 ; il est **INFERRED**, pas mesuré directement.
- **Ordre de protection du code inline** : le contenu des trois `Edit` n'apparaît pas dans le snapshot. L'affirmation est **UNVERIFIED** pour la session source. Le script livré implémente sa propre protection (masquage des spans avant découpage des cellules et avant gras/italique) ; la fixture vérifie `code_inline=3`, `backticks=0` et l'absence de lignes commençant par `|`.
- **Taille finale du HTML** : 5830 octets mesurés au tour d'export, 7032 octets au nettoyage, sans sortie intermédiaire expliquant l'écart. Seuls les comptages structurels sont repris comme assertions ; aucune taille HTML n'est promise par le Skill.
- **« Deux échecs d'outil »** : exact pour les deux `assoc`, mais incomplet si l'on compte les découvertes de chemins (`Exit code 2`) et l'`UnicodeEncodeError` (rc=1) du test pypdf.

## Recontrôle local (2026-10-27, UTC+1)

| Sonde | Résultat |
|---|---|
| `assoc .md` / `assoc .pdf` | rc=1, même message « Association de fichier introuvable » |
| Chrome | `C:\Program Files\Google\Chrome\Application\chrome.exe` présent |
| pypdf | 6.19.0 |
| Interpréteur | `py -3` = 3.14.7 ; `python` = stub Microsoft Store |
| Fixture de validation | 1 H1, 7 H2, 2 tableaux, 1 `ul` de 5 entrées, 1 `ol` de 3 entrées, 1 bloc bash |
| Rendu | `COUNTS h1=1 h2=7 table=2 ul=1 ol=1 li=8 pre=1 code_inline=3`, `backticks=0`, `pipe_lines=0`, `RESULT=PASS`, rc=0 |
| Export | `PDF_BYTES=78978`, `HEADER=%PDF-1.4`, `TAIL_EOF=1`, `PAGE_OBJ=2`, `COUNT=2`, `PYPDF_PAGES=2`, `P1_CHARS=564`, `RESULT=PASS`, rc=0 |
| Négatifs | attente `h1=2` → rc=1 ; entrée absente → rc=2 ; HTML absent → rc=2 ; Chrome inexistant → rc=2 ; texte sous `--min-chars` → rc=1 ; PDF factice ou tronqué → `taille`/`queue`/`pypdf_lecture` |

## Ce que ce paquet ne prétend pas

- Ce n'est pas un rendu CommonMark complet : listes imbriquées, citations, images, notes et liens de référence ne sont pas pris en charge.
- `--min-chars` prouve l'existence de texte extractible, pas la fidélité visuelle ni l'absence de coupure de tableau.
- Aucune conclusion n'est tirée sur le code du script d'origine de la session, qui n'était pas visible.
- Les fichiers du Bureau (`RAPPORT_SKILL_OBSERVATEUR_TRINITER_2026-10-27.md` et `.pdf`) n'ont pas été modifiés par ce travail.
