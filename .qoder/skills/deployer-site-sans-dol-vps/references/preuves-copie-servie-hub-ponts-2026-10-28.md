# Preuves — copie réellement servie et doublon de page (28/10/2026)

## Source

| Élément | Valeur |
| :--- | :--- |
| Session | `527776b5-c1d9-4dc9-9f08-ded973d156c9`, titre « Implémentation CSS Mizan » |
| Lecture | 2026-10-28, `runtimeState = ready`, `activeTurnId = null`, `queuedTurnCount = 0`, `pendingInteractionCount = 0`, `revision = 272`, `hasMoreBefore = false`, `turnLimit = 20`, `includeToolOutputs = true` |
| Messages | 14 (7 tours utilisateur, 7 tours assistant) |
| Demandes | 10:01:16Z « Applique ce layout à l'original » ; 10:03:43Z « Prépare le déploiement sur al-mizan.world » ; 10:11:45Z « Supprime le doublon HUB_PONTS_SYNCHRONES_AL_MIZAN.html à la racine » ; 10:13:15Z « Oui, supprime aussi la sauvegarde » ; 10:13:32Z « Supprime aussi la copie temporaire » |
| Correction | aucune correction verbale de l'utilisateur ; l'assistant découvre le bon fichier en préparant le déploiement |

Les heures des messages sont en UTC. Les heures de fichiers sont celles imprimées par `ls`/`stat` sous Windows (+0200 le 23/10, +0100 le 27–28/10) ou par le serveur.

## Chronologie vérifiée

1. **10:01:16Z — retouche du mauvais fichier.** Le layout est appliqué à `HUB_PONTS_SYNCHRONES_AL_MIZAN.html`, à la racine du workspace. Sauvegarde préalable : 24 756 o, sha `af016c49f4dde651f9cef4c3d62b113cbba893053673c35822af5b8f98998c81`, mtime 2026-10-23 15:07:57 +0200. Juste après écriture, `ls` montre 26 132 o à 11:01 locale ; le dernier relevé avant suppression donne 25 900 o, sha `86719d152468a30d60cc1adeb4c5ed45778a2efb2048d82fb64d19676bf6e58f`. La cause de l'écart de 232 octets n'est pas enregistrée dans les sorties lues.
2. **10:03:43Z — découverte du fichier réellement servi.** Le handler `passerelle_api_vps_mizan.py` lignes 922-931 ouvre `web_cloud/hub_ponts_synchrones.html`. État local avant retouche : 28 440 o, sha `af301dbf5963bb9c96e7a91cb9acf02b9a5d51546bc528f27fcc2c4357b90c2e`, mtime 2026-10-27 13:15:09 +0100. État public : 27 848 o, sha `330d0a3c12279be85f74672e1b8b9e1a69f3b0ceeb4b59f085f5dbd793852379`, servi par `/ponts` et `/hub-ponts`.
3. **Diff local/production avant déploiement.** Les seuls écarts sont trois liens de navigation présents en local et absents de la production : `CGU`, `CGV`, `Signalement`. Les trois routes répondent 200. L'assistant indique « Déploiement autorisé, liens inclus » ; la réponse d'interaction elle-même n'apparaît pas dans l'extrait lu.
4. **Diff doublon racine / fichier servi.** Le fichier servi porte le bandeau de transparence, les formulations auditées et l'avertissement contrat ; la copie racine porte les formulations pré-audit.
5. **Déploiement du seul fichier servi.** Après layout : 29 409 o, sha `a63d6885758225dbb1621dd2ddea3508b3a07da73c8b3c606c74c482d1f620bf`. Sauvegarde distante `.bak-20261028-100833` (sha `330d0a3c…`), installation en `ubuntu:ubuntu 666`, routes publiques `/ponts`, `/hub-ponts`, `/ponts-synchrones` en 200 avec le même hash, aucun redémarrage.
6. **10:11:45Z — suppression du doublon racine.** Vérification des références : la passerelle ne lit que `web_cloud/hub_ponts_synchrones.html` ; le JSON `memoire_aq/almizan_acte_a086_architecture_ponts_synchrones_tetrade_mzn_usdc.json` pointe vers `C:\Users\Administrateur\Desktop\HUB_PONTS_SYNCHRONES_AL_MIZAN.html`, chemin inexistant. Suppression du fichier 25 900 o, sha `86719d15…`.
7. **10:13:15Z — suppression de la sauvegarde.** 24 756 o, sha `af016c49…`, mtime 2026-10-23 15:07:57 +0200.
8. **10:13:32Z — suppression de la copie temporaire.** `.qoder/tmp/hub_ponts_synchrones.html.bak-local-20261028-110445`, 28 440 o, sha `af301dbf…`, mtime 2026-10-27 13:15:09 +0100. Le fichier servi reste 29 409 o, sha `a63d6885…`.

## Handler et copies

| Route(s) | Handler | Fichier ouvert |
| :--- | :--- | :--- |
| `/ponts`, `/hub-ponts`, `/ponts-synchrones`, `/hub` | `passerelle_api_vps_mizan.py:922-931` | `Path(__file__).resolve().parent / "web_cloud" / "hub_ponts_synchrones.html"` |

Extrait exact :

```text
923:        elif chemin in ["/ponts", "/hub-ponts", "/ponts-synchrones", "/hub"]:
924:            chemin_ponts = Path(__file__).resolve().parent / "web_cloud" / "hub_ponts_synchrones.html"
```

Copies observées le 28/10/2026 (liste non exhaustive, voir la concurrence ci-dessous) :

| Chemin | Octets | SHA-256 | Servi | Note |
| :--- | ---: | :--- | :--- | :--- |
| `ASTRO-Q°ODE_SYSTEME/web_cloud/hub_ponts_synchrones.html` | 29 409 | `a63d6885758225dbb1621dd2ddea3508b3a07da73c8b3c606c74c482d1f620bf` | oui | version auditée + layout |
| `ASTRO-Q°ODE_SYSTEME/ponts_synchrones_al_mizan.html` | 15 385 | `2ca9fea1c6a76d143f85c72ec69ccea8a2645910bce327e01f59fe0b40df76ac` | non | autre titre, aucun handler de la passerelle ne la référence, diff de 670 lignes |
| `HUB_PONTS_SYNCHRONES_AL_MIZAN.html` (racine) | 25 900 | `86719d15…` | non | pré-audit, supprimé à 10:11Z |

La troisième variante est un constat complémentaire de lecture seule, pas une copie citée par la session. Son titre est `HUB DES PONTS SYNCHRONES AL-MIZAN — BASE MAINNET`, alors que le fichier servi porte `HUB DES PONTS SYNCHRONES & AUTO-VALORISATION SOUVERAINE AL-MIZAN — BASE MAINNET`. Elle ne contient aucun marqueur de transparence (`BANNIERE DE TRANSPARENCE`, `Statut de cette page`) et n'est référencée dans `passerelle_api_vps_mizan.py`. La recherche globale des références a dépassé le délai de la commande et n'a pas été conclue ; elle n'a pas été supprimée.

## Marqueurs pré-audit / audité

| Marqueur | Doublon racine | Fichier servi |
| :--- | :--- | :--- |
| Bandeau de transparence | absent | présent (`BANNIERE DE TRANSPARENCE`, `Statut de cette page`) |
| Bride | `Bride 0.6225 Scellée` | `Bride 0.6225 · paramètre de conception` |
| Stabilité | `Stabilité 99.83%` | `Métrique simulée du modèle` |
| Principe | `Principe Inviolable` | `Principe du modèle interne` |
| Avertissement contrat | absent | présent (`À vérifier avant exécution`) |

Le diff entre la sauvegarde racine et le fichier servi montre aussi l'ajout de la navigation, du bandeau et de l'avertissement, et le remplacement des formulations physiques par des paramètres de modèle.

## Déploiement du fichier servi

| Élément | Valeur |
| :--- | :--- |
| Local avant retouche | 28 440 o, sha `af301dbf…` |
| Production avant | 27 848 o, sha `330d0a3c…`, `ubuntu:ubuntu 666` |
| Local après layout | 29 409 o, sha `a63d6885…` |
| Sauvegarde distante | `/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/hub_ponts_synchrones.html.bak-20261028-100833`, sha `330d0a3c…` |
| Fichier installé | 29 409 o, `ubuntu:ubuntu 666`, sha `a63d6885…` |
| Routes publiques | `/ponts`, `/hub-ponts`, `/ponts-synchrones` → 200, 29 409 o, sha `a63d6885…` |
| Redémarrage | aucun (page relue à chaque requête) |
| Journaux | `access.log` 1 794 lignes ; `/ponts` 7×200 ; aucun 5xx sur le lot ; un 501 de scan (`YHKR /`) à 02:32, antérieur au déploiement |

Commande de restauration :

```bash
sudo -n install -o ubuntu -g ubuntu -m 666 \
  "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/hub_ponts_synchrones.html.bak-20261028-100833" \
  "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/hub_ponts_synchrones.html"
```

## Concurrence observée pendant la rédaction

Le 28/10/2026 à 11:21:11 +0100, `ASTRO-Q°ODE_SYSTEME/web_cloud/hub_ponts_synchrones.PROTO_70-30.html` est apparu : 29 409 o, sha `88ff31b90ec3453d5e251096d57a58ea80ce3782a79e693eb8a68d289fae95fe`, même titre que le fichier servi, marqueurs d'audit présents. Le handler ne la sert pas. Le fichier est resté stable pendant la double mesure (3 s). D'autres sessions du workspace étaient actives au même moment (dont « 创建布局变体 Skill » et « 创建布局测量 Skill ») ; l'attribution exacte de l'écriture n'a pas été vérifiée. Sa présence confirme que la liste des copies est volatile : la résoudre à chaque intervention.

## Limites

- Le doublon racine n'a jamais été déployé : c'est un quasi-accident, pas une violation de production constatée.
- Aucune correction verbale de l'utilisateur n'apparaît dans l'extrait ; l'assistant s'est corrigé en préparant le déploiement, puis l'utilisateur a demandé les suppressions.
- L'écart 26 132 o → 25 900 o sur le doublon racine n'est pas expliqué par les sorties lues ; la valeur finale avant suppression est 25 900 o et le hash `86719d15…`.
- La troisième variante est un candidat par tokens, pas un doublon prouvé ; aucune suppression n'est recommandée.
- Certaines sorties d'outils étaient tronquées à 8 000 caractères (notamment le `Grep` des références) ; seules les portions visibles sont citées.
- Le déploiement des trois liens de navigation est constaté dans les routes publiques ; l'accord explicite de l'utilisateur est rapporté par l'assistant, pas observé comme message séparé.
