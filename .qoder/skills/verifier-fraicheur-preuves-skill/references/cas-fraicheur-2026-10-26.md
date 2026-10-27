# Cas de fraîcheur des preuves — 2026-10-26

**Objet** : vérifier si les valeurs présentées comme « courantes » dans l'archive de `verifier-reecriture-concurrente-paquet-skill` étaient encore vraies après sa rédaction, puis appliquer la porte de livraison de `verifier-fraicheur-preuves-skill`.

**Paquet audité** : `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule`

**Skill livré examiné** : `C:\Users\Administrateur\.qoder\skills\verifier-reecriture-concurrente-paquet-skill`

**Statut** : dérive confirmée ; la phrase « quatre fichiers n'ont pas changé » de la §13 n'était vraie que dans sa fenêtre d'échantillonnage ; les valeurs postérieures sont `PROVISIONAL` comme valeurs « courantes » ; l'auteur reste non identifié. Aucun fichier du paquet audité ni du Skill livré n'a été modifié par cette vérification.

## 1. Artefacts et empreintes

### 1.1 Skill livré au moment de la vérification

| Artefact | Taille | mtime | SHA-256 |
|---|---:|---|---|
| `SKILL.md` | 15 799 B | 2026-10-26T13:55:24.960147000+01:00 | `f6fb7518e2c0f9e2e2d51c9e2235f341b8ab84995ca0375b58250ea3eb23c6b5` |
| `references/cas-reecriture-2026-10-26.md` | 21 424 B | 2026-10-26T14:00:17.806785100+01:00 | `f3b218368efe5f18127fc741b805679825e86ed907c8327d0ab158c52a8e3e60` |

La QA relancée le 2026-10-26 à 15:31+01:00 donne `RESULT PASS`, code 0, 9 pass / 0 fail / 0 warn, `Files (2)`, description 806 caractères, corps 219 lignes, 1 référence locale, 10 références de Skills résolues. Elle ne couvre que `SKILL.md` : elle ne valide pas les affirmations de l'archive.

### 1.2 Affirmations de l'archive

| Fichier du paquet audité | Section | Taille | mtime | SHA-256 |
|---|---|---:|---|---|
| `SKILL.md` | §1, ligne 13 | 15 154 B | 2026-10-26T13:29:08.317483200+01:00 | `6d755440b877d69484533eee0eba663abfb0f23dca54673364102f5fd3f6b632` |
| `references/cas-entite-2026-10-26.md` | §1, ligne 14 | 9 792 B | 2026-10-26T13:29:35.563770600+01:00 | `bf4a778a1868bbe548eb9ce7f3940970b1d07627fc65459c1f5799570fd8319c` |
| `references/protocole-restauration.md` | §1, ligne 15 | 15 676 B | 2026-10-26T13:36:15.187788200+01:00 | `1de3f4edd8b7e7b3f489d7d83586588f4b706876efeab1b8b87fe7659481fff9` |
| `scripts/instantane_effets_de_bord.py` | §1, ligne 16 | 29 761 B | 2026-10-26T13:35:36.191303400+01:00 | `a500711817f826e03b0903cbb3aed78b73a2bbc638c919887f17578316723081` |
| `scripts/tester_instantane.py` | §13, ligne 316 | 24 235 B | 2026-10-26T13:58:50.306317500+01:00 | `6184122ec59f21afb7489253b03d63d4e4ea542be017e256920174a1f8d5c924` |

La §13, ligne 317, affirme que « les quatre fichiers documentés au §1 n'ont pas changé » et que la dérive est `AJOUTE`, pas `MODIFIE`. La §13, ligne 318, précise que trois échantillons identiques ont été pris entre 13:59:59 et 14:00:04+01:00, mais qu'une écriture venait d'avoir lieu et que l'état est `PROVISIONAL`, pas `FINAL`.

### 1.3 Mesure de la session source à 14:02:47+01:00

Relevé dans le JSONL de la session `f2c34999-188f-40a5-bb95-57c17939dd95`, lignes 151 et 160, horodatage de l'outil 2026-10-26T13:02:47.464Z :

| Fichier | Taille | mtime | SHA-256 |
|---|---:|---|---|
| `SKILL.md` | 16 025 B | 2026-10-26T14:02:32.994351300+01:00 | `79862dc9f60aa85e71bd99a60b4a421664eb9b84432357b152abaf37b76da07d` |
| `references/cas-entite-2026-10-26.md` | 9 792 B | 2026-10-26T13:29:35.563770600+01:00 | `bf4a778a1868bbe548eb9ce7f3940970b1d07627fc65459c1f5799570fd8319c` |
| `references/protocole-restauration.md` | 18 767 B | 2026-10-26T14:00:56.768598800+01:00 | `d88e1fb29054deae6ea597feb3d8e5016a3e30fb9b47d6d07ccdbd870b8c9cb9` |
| `scripts/instantane_effets_de_bord.py` | 29 761 B | 2026-10-26T13:35:36.191303400+01:00 | `a500711817f826e03b0903cbb3aed78b73a2bbc638c919887f17578316723081` |
| `scripts/tester_instantane.py` | 24 235 B | 2026-10-26T13:58:50.306317500+01:00 | `6184122ec59f21afb7489253b03d63d4e4ea542be017e256920174a1f8d5c924` |

### 1.4 Mesure indépendante à 15:25:42+01:00

| Fichier | Taille | mtime | SHA-256 |
|---|---:|---|---|
| `SKILL.md` | 18 050 B | 2026-10-26T14:07:07.552720200+01:00 | `9130744f2ac16cebc475d9252f29b8e46555c5ec3fa1e91d8b9c93e94fac7a62` |
| `references/cas-entite-2026-10-26.md` | 12 710 B | 2026-10-26T14:08:00.062598200+01:00 | `8cbf252102e2bbf0183f7bb7375f95eec04bc6bfbfa1c701c7fee36ae6f0cbc1` |
| `references/protocole-restauration.md` | 20 419 B | 2026-10-26T14:07:54.296405700+01:00 | `d73d511a423d9035efb4fae9f7e7cf5faa04c3bfb0b02ee396beab54b27c4cb2` |
| `scripts/instantane_effets_de_bord.py` | 29 809 B | 2026-10-26T14:05:58.248147800+01:00 | `160b874f8f2c0259a302a9db8b20418b2d02ca5c7ac837a4ac7696b841b200ad` |
| `scripts/tester_instantane.py` | 27 787 B | 2026-10-26T14:06:26.572831700+01:00 | `2f97208b020f871157d98c67e88921d3d9c2bdb57a0faa3e1f19afad3dfb9389` |

État Git au même moment : `HEAD` `ddd3246` (`feat(skill): adopter verifier-effets-de-bord-verification-lecture-seule`) a livré 4 fichiers à 13:44:49+01:00 ; `git status --short` montre `M` sur les quatre fichiers suivis et `??` sur `scripts/tester_instantane.py`.

## 2. Chronologie

| Heure locale (+01:00) | UTC | Fait | Source |
|---|---|---|---|
| 13:55:24.960 | 12:55:24.960Z | Écriture du `SKILL.md` livré | mtime |
| 13:57:53.262 | 12:57:53.262Z | Apparition de `scripts/tester_instantane.py` | archive §13 |
| 13:58:50.306 | 12:58:50.306Z | Réécriture du même fichier, hash `6184122e…` | archive §13 |
| 13:59:59–14:00:04 | 12:59:59–13:00:04Z | Trois échantillons identiques de la §13 | archive §13 |
| 14:00:17.806 | 13:00:17.806Z | Écriture de l'archive `cas-reecriture-2026-10-26.md` | mtime |
| 14:00:56.768 | 13:00:56.768Z | Réécriture du protocole, hash `d88e1fb2…` | mtime |
| 14:02:32.994 | 13:02:32.994Z | Réécriture du `SKILL.md` audité, hash `79862dc9…` | mtime |
| 14:02:47.464 | 13:02:47.464Z | Mesure de la session source | JSONL ligne 151 |
| 14:03:11.609 | 13:03:11.609Z | Deuxième mesure et hashes complets | JSONL ligne 160 |
| 14:03:56.325 | 13:03:56.325Z | La session source propose une mise à jour minimale | JSONL lignes 171–172 |
| 15:25:42 | 14:25:42Z | Mesure indépendante de ce cas | cette session |
| 15:31:30 | 14:31:30Z | Snapshot avant écriture ; cible absente | cette session |

L'intervalle entre l'archive (14:00:17) et la première réécriture non couverte (14:00:56) est de 39 secondes ; la seconde (14:02:32) arrive 2 minutes 15 secondes après l'archive.

## 3. Affirmations et verdicts

| Affirmation | Référence | Mesure 14:02:47 | Mesure 15:25:42 | Verdict |
|---|---|---|---|---|
| `SKILL.md` courant, 15 154 B / `6d755440…` / 13:29:08 | §1 ligne 13 | 16 025 B / `79862dc9…` / 14:02:32 | 18 050 B / `9130744f…` / 14:07:07 | `PERIME` |
| `cas-entite` courant, 9 792 B / `bf4a778a…` / 13:29:35 | §1 ligne 14 | identique | 12 710 B / `8cbf2521…` / 14:08:00 | `CONFIRME` à 14:02, `PERIME` à 15:25 |
| `protocole` courant, 15 676 B / `1de3f4ed…` / 13:36:15 | §1 ligne 15 | 18 767 B / `d88e1fb2…` / 14:00:56 | 20 419 B / `d73d511a…` / 14:07:54 | `PERIME` |
| `instantane` courant, 29 761 B / `a5007118…` / 13:35:36 | §1 ligne 16 | identique | 29 809 B / `160b874f…` / 14:05:58 | `CONFIRME` à 14:02, `PERIME` à 15:25 |
| `tester_instantane.py` 24 235 B / `6184122e…` / 13:58:50 | §13 ligne 316 | identique | 27 787 B / `2f97208b…` / 14:06:26 | `CONFIRME` à 14:02, `PERIME` à 15:25 |
| « les quatre fichiers documentés n'ont pas changé » | §13 ligne 317 | faux : `SKILL.md` et `protocole` ont changé | faux : les cinq fichiers diffèrent | `PERIME` hors de la fenêtre 13:59:59–14:00:04 |
| « 5 fichiers de contenu » | §13 ligne 316 | vrai (5) | vrai (5) | `CONFIRME` pour le nombre, pas pour le contenu |
| « `PROVISIONAL`, pas `FINAL` » | §13 ligne 318 | approprié | toujours approprié | `CONFIRME` |
| « écrivain non identifié » | §13 ligne 318 | toujours non identifié | toujours non identifié | `CONFIRME` faute de preuve Write/Edit |

## 4. Grades

- La mesure de 14:02:47 est `FINAL` pour cet horodatage : elle provient d'une sortie d'outil datée et complète. Elle est `PROVISIONAL` comme « valeur courante », car le paquet était encore modifié et l'auteur n'est pas identifié.
- La mesure de 15:25:42 est `FINAL` pour cet horodatage : elle a été prise deux fois à 2 s d'intervalle, sans changement. Elle est `PROVISIONAL` comme « valeur courante » : le paquet peut encore changer et l'auteur reste inconnu.
- La phrase « quatre fichiers n'ont pas changé » est `CONFIRME` uniquement dans la fenêtre 13:59:59–14:00:04 ; elle est `PERIME` ensuite. La §13 est conservée intacte.
- L'auteur des écritures de 14:00:56, 14:02:32 et 14:05–14:08 n'est pas identifié. Aucun Write/Edit ne relie ces mtimes à une session dans les preuves examinées.
- Le Skill livré n'a pas été corrigé : `SKILL.md` reste `f6fb7518…` et l'archive reste `f3b21836…`. La QA est `PASS` parce qu'elle ne vérifie que `SKILL.md`.

## 5. Ce que la session source a établi

La session `f2c34999-188f-40a5-bb95-57c17939dd95` a été lue avec `read_chat_session` : `runtimeState=cold`, `revision=0`, `hasMoreBefore=false`, deux messages (un utilisateur, un assistant). L'assistant a attendu la session `559fe036-513d-45ef-bc40-014daa62d893` jusqu'à `ready`/`revision 54`, constaté que le Skill existait déjà, l'a pris en reprise sans écraser, a validé la QA, puis a découvert la dérive et proposé une mise à jour minimale. Il s'est arrêté pour confirmation : aucun Write n'a suivi.

- **Correction utilisateur** : aucune. La session `559fe036` contient une confirmation de plan, pas une correction de contenu ; la session imbriquée `f8e5b9ec` n'a qu'un tour utilisateur et sa proposition n'a pas été exécutée.
- **Échec observé** : un Bash a échoué sur `UnicodeEncodeError` avec `cp1252` en imprimant du chinois. Ce n'est pas un échec métier ; la suite a utilisé `PYTHONIOENCODING=utf-8`.
- **Étapes vérifiées par la source** : le validateur ne prend l'empreinte que de `SKILL.md` ; les deux commandes de rejeu ont rendu `RC=0` et les hashes `be2b86b4…` (29 725 B) et `fc2618d6…` (15 240 B), égaux aux baselines ; le JSONL n'a pas augmenté ; l'ancien harnais `2fb80d0b…` (`snap2`) différait du courant `73ff7c5c…` (`snap3`) ; le harnais indépendant a rendu 22/22.
- **Étapes revérifiées ici** : le code du validateur appelle `finish_fingerprint(skill_md, ...)` aux lignes 372 et 525 de `skill-file-qa/scripts/validate_skill.py` ; la QA du Skill livré rend `PASS` 9/0/0 `Files (2)` ; les valeurs de 14:02:47 sont dans le JSONL lignes 151 et 160 ; l'état de 15:25:42 est mesuré sur disque.

## 6. Pourquoi « quatre fichiers inchangés » a expiré

1. Une fenêtre de stabilité de quelques secondes ne prouve que cette fenêtre. La §13 l'a écrit correctement (`PROVISIONAL`) mais la phrase « n'ont pas changé » reste facile à citer hors contexte.
2. L'archive a été écrite à 14:00:17 ; le protocole a changé 39 secondes plus tard et le `SKILL.md` 2 minutes 15 secondes plus tard.
3. Le cinquième fichier `scripts/tester_instantane.py` est apparu à 13:57:53, **avant** l'archive. La §13 le classe correctement en `AJOUTE` ; l'affirmation erronée n'est pas « un fichier a été ajouté après l'archive » mais « les quatre fichiers documentés n'ont pas changé ».
4. `Files (N)` est resté à 5, mais le contenu des cinq fichiers a changé. Un inventaire stable ne prouve pas un contenu stable.
5. Le correctif attendu est d'ajouter une §14 datée et de synchroniser la section « cas vérifié » du `SKILL.md`, pas de réécrire la §13.

## 7. Commandes reproductibles

```bash
target="C:/Users/Administrateur/.qoder/skills/verifier-effets-de-bord-verification-lecture-seule"

find "$target" -type f -not -path '*/.git/*' \
  -printf '%s %TY-%Tm-%TdT%TH:%TM:%TS %p\n' | sort

sha256sum "$target"/SKILL.md "$target"/references/*.md "$target"/scripts/*.py

git -C "$target" status --short
git -C "$target" log --oneline --stat -1
```

QA du Skill livré :

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "C:/Users/Administrateur/.qoder/skills/verifier-reecriture-concurrente-paquet-skill" \
  --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" \
  --stable-seconds 2 --stability-timeout 30
```

Sortie observée : `RESULT PASS`, `RC=0`, 9 pass / 0 fail / 0 warn, `Files (2)`, `PASS fingerprint: unchanged during validation`.

## 8. Limites

- L'auteur des écritures postérieures à l'archive n'est pas identifié ; aucune attribution n'est faite.
- Les versions intermédiaires entre 14:00 et 14:08 n'ont pas été reconstruites ; les mesures portent sur les extrémités observées (14:02:47 et 15:25:42).
- Les valeurs de 15:25:42 peuvent déjà être périmées au moment de la lecture ; les revérifier avant de les citer.
- Les rejeux de la session source (`be2b86b4…`, `fc2618d6…`), la comparaison des harnais et le 22/22 ne sont pas rejoués ici ; ils sont rapportés par la source. Seuls la portée du validateur, la QA du Skill livré et les mesures disque ont été revérifiés indépendamment.
- Aucun fichier du paquet audité ni du Skill livré n'a été modifié. Aucun script du paquet audité n'a été exécuté.

## 9. Checklist

- [x] Archive, `SKILL.md` livré et paquet audité identifiés par chemin absolu.
- [x] Affirmations « courant » et « quatre fichiers inchangés » listées avec section et ligne.
- [x] Mesures 14:02:47 et 15:25:42 avec taille, `mtime`, SHA-256 et fuseau.
- [x] Verdicts `CONFIRME` / `PERIME` et grades `FINAL` / `PROVISIONAL` séparés.
- [x] Auteur laissé « non identifié ».
- [x] §13 conservée intacte ; la correction attendue est une §14, non une réécriture.
- [x] QA relancée et portée limitée à `SKILL.md` rappelée.
- [x] Limites et pas de rejeu intermédiaire écrits explicitement.
