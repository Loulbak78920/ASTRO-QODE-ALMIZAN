---
name: qualifier-chemins-references-skill
description: "Pré-qualifier les références locales d'un SKILL.md avant skill-file-qa : reproduire la collecte du validateur (liens Markdown comptés après normalisation ; jetons entre backticks retenus seulement pour scripts/, references/, assets/ ou un chemin avec « / » et extension connue), expliquer chaque jeton ignoré (URL, absolu, ~, $, .., ancre) qui ne prouve rien, résoudre chaque référence comptée contre le dossier du Skill puis --workspace, sans remontée de répertoire, préfixer le sous-dossier projet (ex. ASTRO-Q°ODE_SYSTEME/) au lieu d'un chemin partiel, vérifier à la main references/*.md que le validateur ne lit jamais, et mesurer description (YAML parsé, ≤1024) et corps (<500 lignes). Utiliser avant création ou mise à jour, ou pour corriger un chemin du dépôt qui existe sous un sous-dossier, ou un chemin absolu ; après un FAIL, la réparation revient à corriger-references-locales-skill-sous-projet. 中文触发：Skill 本地引用预检、skill-file-qa 路径失败。"
---

# Qualifier les références locales d'un SKILL.md avant le QA

## Portée

Pré-résoudre, en lecture seule, les références locales d'un `SKILL.md` avant de lancer `skill-file-qa` : lister ce que le validateur comptera réellement, expliquer ce qu'il ignore en silence, résoudre chaque chemin contre le dossier du Skill puis `--workspace`, et vérifier à part les références des fichiers du dossier de références.

Ce Skill ne remplace pas la validation : il évite un FAIL prévisible et empêche qu'un chemin absolu ou un jeton incomplet passe pour une preuve. La sortie du validateur reste l'autorité.

| Besoin | Skill |
| :--- | :--- |
| Acceptation statique complète du paquet | `skill-file-qa` |
| Vivacité des noms de Skills cités, y compris non installés | `verify-cross-skill-reference-liveness` |
| Contenu des citations `fichier:ligne` | `verifier-citations-lignes-skill` |
| Audit de livraison d'un module projet avec son workspace | `auditer-livraison-skill-module-projet` |
| Parité entre la doc et les sorties d'un script | `verifier-parite-doc-script-skill` |
| Réparation d'un FAIL sur un chemin de sous-projet | `corriger-references-locales-skill-sous-projet` |

## 1. Invariants

1. **Un jeton ignoré ne prouve rien.** Un chemin absolu, `..`, `~`, une URL ou un jeton contenant un espace ou `=` n'est jamais vérifié ; sa présence dans le Skill ne prouve pas que le fichier existe.
2. **La résolution est fermée.** Le validateur n'essaie que `<dossier-skill>/<réf>` puis `<workspace>/<réf>`. Aucune remontée de répertoire, aucune recherche par nom.
3. **Le validateur installé fait foi.** Le script charge ses fonctions ; ne pas recopier ses expressions régulières dans la documentation ni dans un autre script.
4. **Un seul workspace, relatif exact.** Un chemin du dépôt s'écrit depuis la racine passée à `--workspace`, sous-dossier projet compris.
5. **Les fichiers de références ne sont jamais lus par le validateur.** Un `RESULT PASS` ne couvre pas les chemins qui y sont cités ; il faut un contrôle manuel daté.
6. **La description se mesure sur le YAML parsé.** Longueur ≤ 1024 caractères, une seule ligne ; le corps reste sous 500 lignes.
7. **Aucune écriture.** La qualification ne modifie ni le Skill, ni le workspace, ni le validateur.

## 2. Lancer la qualification

Depuis n'importe quel répertoire, avec le script du Skill installé :

```bash
py -3 "$HOME/.qoder/skills/qualifier-chemins-references-skill/scripts/qualifier_references.py" \
  "<skill-dir>" --workspace "<workspace-root>" --scan-references
```

| Option | Effet |
| :--- | :--- |
| `--workspace DIR` | racine de résolution ; toujours l'expliciter (défaut : répertoire courant) |
| `--validator FILE` | autre copie du validateur |
| `--scan-references` | contrôle indicatif des chemins cités dans les fichiers de références |
| `--strict-references` | rend ce contrôle bloquant (rc 1) |
| `--show-skipped` | détaille chaque jeton ignoré au lieu d'un échantillon |

Codes de retour : `0` tout chemin compté résout ; `1` au moins un `COUNTED … MISSING` (ou un manuel manquant avec `--strict-references`) ; `2` usage ou environnement (validateur absent, API changée, dossier introuvable, UTF-8 invalide, désaccord de contrat).

Le script imprime l'empreinte du validateur utilisé. La consigner avec le rapport : elle borne la portée des conclusions.

## 3. Lire le rapport

- `COUNTED <réf> RESOLVED skill|workspace via link,span` : le validateur vérifiera cette référence et elle existe.
- `COUNTED <réf> MISSING` : le validateur échouera avec `local reference not found`. Corriger avant de lancer le QA.
- `SKIPPED <n> <raison>` : jamais vérifié. Accepter chaque catégorie explicitement.
- `MANUAL <fichier>:<ligne> <réf> MISSING` : chemin d'un fichier de références, hors contrôle du validateur.

Raisons d'ignorance :

| Raison | Forme typique | Conséquence |
| :--- | :--- | :--- |
| `url` | http://… ou https://… | lien externe, hors sujet |
| `anchor` | #section, ou jeton backtick contenant # | ancre interne, non vérifiée |
| `mailto` | mailto:… | hors sujet |
| `absolute_posix` | /etc/passwd | aucune preuve d'existence locale |
| `windows_absolute` | C:\… ou C:/… | aucune preuve d'existence locale |
| `home` | ~/… | aucune preuve, dépend de la machine |
| `variable` | $HOME/… | non développé |
| `parent` | ../… | interdit, pas de remontée |
| `shape` | espace, <>, {}, \*, ?, = | non reconnu comme chemin inline |
| `no_slash` | fichier.md, nom-de-skill | pas de « / » : jamais `COUNTED`, même pour un Skill installé |
| `unknown_extension` | dossier/fichier.xyz | extension hors liste connue |

Un lien Markdown est compté **après normalisation**, même sans « / » ni extension connue : une cible relative manquante fait échouer le QA. Un jeton backtick, lui, doit avoir la forme d'un chemin inline pour être compté.

Un nom de Skill en backticks (`skill-file-qa`, `rotation-secret-systemd-vps-mizan`) n'a ni « / » ni extension : il tombe toujours en `no_slash`, installé ou non, et n'entre jamais dans `counted`. L'ajouter laisse donc `counted`, `resolved` et `QUALIFIER` inchangés — sans `--show-skipped`, il peut même ne pas apparaître dans l'échantillon. La preuve est le compteur `skill references` du validateur (noms hors blocs de code), qui doit citer le nom, avec une empreinte de `SKILL.md` différente de l'avant.

## 4. Résoudre un chemin du dépôt

Le piège observé : citer un fichier depuis la racine du projet alors qu'il vit dans un sous-dossier.

```text
workspace = <racine-projet>
réf = deploiement_vps/deployer_vers_vps.py                     -> COUNTED ... MISSING
réf = ASTRO-Q°ODE_SYSTEME/deploiement_vps/deployer_vers_vps.py -> RESOLVED workspace
```

Procédure :

1. Localiser le fichier réel sans ambiguïté (plusieurs copies possibles) :
   ```bash
   find "<workspace>" -name "<fichier>" -not -path "*/.git/*"
   ```
2. Prendre le chemin relatif au workspace, sous-dossier compris, et le citer tel quel.
3. Garder un seul workspace pour tout le Skill ; ne pas déplacer la racine pour un seul fichier, sinon les autres références cassent.
4. Rejouer la qualification, puis le QA :
   ```bash
   py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<skill-dir>" \
     --workspace "<workspace-root>" --stable-seconds 2 --stability-timeout 30
   ```

Quand le fichier est propre au Skill, le placer sous `scripts/` ou dans un dossier `references` et le citer depuis le dossier du Skill : la première résolution suffit, le Skill reste portable.

## 5. Contrôler les fichiers de références

Le validateur ne lit que le texte de `SKILL.md`. Pour chaque fichier de références, les chemins cités doivent être vérifiés à part :

```bash
py -3 "$HOME/.qoder/skills/qualifier-chemins-references-skill/scripts/qualifier_references.py" \
  "<skill-dir>" --workspace "<workspace-root>" --scan-references --strict-references
```

Le scan résout chaque jeton backtick contre le dossier du fichier de références, puis le dossier du Skill, puis le workspace. Il reste indicatif : un lien Markdown ou un chemin absolu dans une référence n'est pas analysé de la même façon. Consigner la date et la liste des manquants ; ne pas présenter le PASS du validateur comme une preuve pour ces chemins.

## 6. Mesurer le frontmatter avant l'écriture

```bash
py -3 - "<SKILL.md>" <<'PY'
import pathlib, sys, yaml
t = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
f, b = t.split("---", 2)[1:]
b = b[1:] if b.startswith("\n") else b
d = yaml.safe_load(f)
print("description_chars", len(d["description"]))
print("description_lines", d["description"].count("\n") + 1)
print("body_lines", len(b.splitlines()))
PY
```

Exiger `description_chars <= 1024`, `description_lines == 1`, `body_lines < 500`. La longueur est celle de la chaîne Python après parsing YAML, pas celle de la ligne source ; les caractères non ASCII comptent pour un.

## 7. Pièges vérifiés

| Piège | Effet | Parade |
| :--- | :--- | :--- |
| Chemin absolu en backticks | ignoré, QA vert sans preuve | citer un chemin relatif au workspace, ou déplacer la ressource dans le Skill |
| `..` dans une référence | ignoré | copier la ressource dans le Skill, ou préfixer depuis le workspace |
| Nom de Skill en backticks | jamais `COUNTED` ; un nom installé ne change ni `counted` ni `QUALIFIER`, un nom inconnu est ignoré sans FAIL ni WARN | exiger du QA `skill references: N checked (… <nom> …)` et une empreinte changée ; nom inconnu : `verify-cross-skill-reference-liveness` |
| Lien Markdown vers une cible absente | compté, donc FAIL | vérifier la cible, pas seulement le libellé |
| Même nom de fichier dans deux dossiers | résolution skill avant workspace ; mauvais jumeau possible | citer le chemin exact et vérifier le fichier ouvert |
| `--workspace` omis | défaut = répertoire courant, résultat non reproductible | toujours l'expliciter |
| Fichiers de références | jamais lus | `--scan-references` puis revue manuelle |
| Stabilité non attendue | le QA échoue si le fichier change pendant le contrôle | garder les valeurs documentées par `skill-file-qa` |

## 8. Critères de sortie

- `QUALIFIER PASS`, `missing=0`, avec le nombre de références comptées attendu.
- Référence inter-Skills ajoutée en backticks : `counted` et `missing` inchangés, et le QA nomme le Skill dans `skill references: N checked (…)` (`N` au moins égal à l'avant) avec une empreinte de `SKILL.md` différente ; `QUALIFIER PASS` seul ne prouve pas la résolution.
- Chaque catégorie ignorée est acceptée explicitement dans le rapport ; aucune n'est présentée comme une preuve.
- Le scan des références est `missing=0`, ou chaque manquant est corrigé ou justifié.
- La description et le corps sont mesurés.
- Puis le QA rend `RESULT PASS`, rc 0, avec l'empreinte du validateur et le nombre de fichiers consignés.
- Le rapport sépare : chemins vérifiés par le validateur, chemins contrôlés manuellement, chemins ignorés et assumés.

## Ressources

- `scripts/qualifier_references.py` — qualification en lecture seule, parité avec le validateur installé.
