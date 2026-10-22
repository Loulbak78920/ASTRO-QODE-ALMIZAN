# -*- coding: utf-8 -*-
"""
Interface en Ligne de Commande Universelle d'ASTRO-Q°ODE (`astro_qode_cli.py`)
==============================================================================
Outil principal permettant de :
- `run <fichier.aq>`       : Exécuter un programme ASTRO-Q°ODE V1.0 ou V2.0
- `check <fichier.aq>`     : Valider la syntaxe et l'intégrité ontologique (MECQUOIS / MEDINOIS)
- `format <fichier.aq>`    : Formater canoniquement un script ASTRO-Q°ODE
- `transpile <fichier.aq>` : Transpiler un script ASTRO-Q°ODE en code Python exécutable
- `asm <fichier.aq>`       : Générer le listing assembleur biomécanique (Omoplate / Bras / 5 Doigts)
- `inspect`                : Afficher le rapport matriciel complet des 4 couches d'IMAM8MAHDI
- `repl`                   : Lancer la console interactive ASTRO-Q°ODE
- `test`                   : Exécuter la suite de tests unitaires et d'intégration complète
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Assurer l'encodage UTF-8 sous Windows pour tous les symboles mathématiques et ontologiques
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE_SYSTEME = Path(__file__).resolve().parent
if str(RACINE_SYSTEME) not in sys.path:
    sys.path.insert(0, str(RACINE_SYSTEME))

from bibliotheques.lib_matrice_unisson_or_argent import MatriceFondatriceUnisson
from bibliotheques.lib_pont_materiel_emule import PontMaterielEmuleAlmizan
from lang.compilateur_qasm_isa import CompilateurQasmIsaAstroQode
from lang.interpreter import InterpreteurAstroQode
from lang.transpiler import TranspilateurPythonAstroQode
from outils.assembleur_scapulaire import AssembleurScapulaire
from outils.formateur_code import FormateurAstroQode
from outils.inspecteur_matriciel import InspecteurMatricielAstroQode
from outils.repl_interactif import ReplAstroQode
from outils.scelleur_cryptographique import ScelleurMemoireAstroQode
from outils.studio_dashboard import StudioDashboardAstroQode
from outils.validateur_syntaxique import ValidateurOntologiqueAstroQode
from tests.test_suite_complete import executer_tous_les_tests


def _lire_fichier(chemin: str) -> str:
    candidats = [
        Path(chemin),
        RACINE_SYSTEME / chemin,
        RACINE_SYSTEME.parent / chemin,
        RACINE_SYSTEME / "bibliotheques" / "stdlib_aq" / Path(chemin).name,
    ]
    for p in candidats:
        if p.exists() and p.is_file():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Fichier introuvable : {chemin} (cherché aussi dans {RACINE_SYSTEME})")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="astro_qode_cli",
        description="Chaîne d'outils officielle du langage et système ASTRO-Q°ODE (V1.0 & V2.0)",
    )
    subparsers = parser.add_subparsers(dest="commande", help="Sous-commandes disponibles")

    # 1. run
    p_run = subparsers.add_parser("run", help="Exécute un script ASTRO-Q°ODE (.aq ou .txt)")
    p_run.add_argument("fichier", help="Chemin du fichier source ASTRO-Q°ODE")
    p_run.add_argument("--json", action="store_true", help="Affiche le rapport complet de la VM en JSON")

    # 2. check
    p_check = subparsers.add_parser("check", help="Vérifie la syntaxe et l'ontologie d'un script")
    p_check.add_argument("fichier", help="Chemin du fichier source ASTRO-Q°ODE")

    # 3. format
    p_fmt = subparsers.add_parser("format", help="Formate canoniquement un script ASTRO-Q°ODE")
    p_fmt.add_argument("fichier", help="Chemin du fichier source ASTRO-Q°ODE")
    p_fmt.add_argument("--write", "-w", action="store_true", help="Écrit le résultat directement dans le fichier")

    # 4. transpile
    p_tr = subparsers.add_parser("transpile", help="Transpile un script .aq en code Python .py")
    p_tr.add_argument("fichier", help="Chemin du fichier source ASTRO-Q°ODE")
    p_tr.add_argument("--out", "-o", help="Fichier Python de sortie optionnel")

    # 5. asm
    p_asm = subparsers.add_parser("asm", help="Génère le listing assembleur biomécanique (Omoplate/5 Doigts)")
    p_asm.add_argument("fichier", help="Chemin du fichier source ASTRO-Q°ODE")

    # 6. inspect
    p_insp = subparsers.add_parser("inspect", help="Affiche le rapport d'inspection des 4 couches IMAM8MAHDI")
    p_insp.add_argument("--json", action="store_true", help="Exporte l'inspection au format JSON")

    # 7. repl
    subparsers.add_parser("repl", help="Lance la console interactive REPL ASTRO-Q°ODE")

    # 8. test
    subparsers.add_parser("test", help="Exécute la suite complète de tests du système")

    # 9. ports (Brique 1 V4.0 : Pont TCP/JSON Al-Mizan :5025, :5026, :5030)
    subparsers.add_parser("ports", help="Sonde les ports locaux Al-Mizan (:5025 SCPI, :5026 Cryo, :5030 Die)")

    # 10. qasm (Brique 2 V4.0 : Compilateur OpenQASM 2.0 & Trames ISA DIE)
    p_qasm = subparsers.add_parser("qasm", help="Compile un script .aq ou un circuit (BELL/GROVER/QFT) en OpenQASM 2.0 et l'exécute sur :5030")
    p_qasm.add_argument("cible", nargs="?", default="BELL", help="Chemin d'un fichier .aq ou nom de circuit (BELL, GROVER, QFT)")
    p_qasm.add_argument("--shots", type=int, default=1024, help="Nombre de shots quantiques")

    # 11. seal (Brique 3 V4.0 : Scelleur Cryptographique SHA-256)
    p_seal = subparsers.add_parser("seal", help="Scelle ou vérifie le registre cryptographique SHA-256 dans memoire_aq/")
    p_seal.add_argument("--verify", action="store_true", help="Vérifie l'intégrité de tous les sceaux SHA-256")

    # 12. studio (Brique 4 V4.0 : Studio Visuel HTML5/SVG 27 Formes & Sphère Holographique)
    subparsers.add_parser("studio", help="Génère le Dashboard HTML5/SVG interactif d'ASTRO-Q°ODE V4.0")

    # 13. unisson (V5.0 : Matrice Fondatrice de l'Unisson & Calcul Valeur Or et Argent)
    p_uni = subparsers.add_parser("unisson", help="Calcule la Matrice Fondatrice de l'Unisson (4x4) et la valeur de l'Or (Au) et de l'Argent (Ag)")
    p_uni.add_argument("--or-g", type=float, default=85.0, help="Masse d'Or pur en grammes (défaut: 85.0 g = 1 Nisab / 20 Mithqal)")
    p_uni.add_argument("--argent-g", type=float, default=595.0, help="Masse d'Argent pur en grammes (défaut: 595.0 g = 1 Nisab / 200 Dirhams)")
    p_uni.add_argument("--json", action="store_true", help="Affiche le rapport complet de la Matrice d'Unisson en JSON")

    args = parser.parse_args()

    if not args.commande:
        print(InspecteurMatricielAstroQode.formater_rapport_console())
        return 0

    if args.commande == "inspect":
        if args.json:
            print(json.dumps(InspecteurMatricielAstroQode.rapport_global_dictionnaire(), indent=2, ensure_ascii=False))
        else:
            print(InspecteurMatricielAstroQode.formater_rapport_console())
        return 0

    if args.commande == "repl":
        ReplAstroQode().lancer_boucle_interactive()
        return 0

    if args.commande == "test":
        ok = executer_tous_les_tests()
        return 0 if ok else 1

    if args.commande == "run":
        source = _lire_fichier(args.fichier)
        interp = InterpreteurAstroQode()
        res = interp.executer_source(source)
        if args.json:
            print(json.dumps(res.rapport_vm, indent=2, ensure_ascii=False))
        else:
            print("=" * 80)
            print(f"EXÉCUTION ASTRO-Q°ODE : {args.fichier}")
            print("=" * 80)
            for msg in res.sorties_console:
                print(f"  [SORTIE] {msg}")
            print(f"  • Statut           : {'SUCCÈS' if res.succes else 'INVERSION ¿ (' + str(res.erreur) + ')'}")
            print(f"  • Valeur finale    : {res.valeur_finale!r}")
            print(f"  • Forme Matière    : {interp.vm.forme_active.code_court} ({interp.vm.forme_active.nom_complet})")
            print(f"  • Registre MECQUOIS: { {k: repr(v) for k, v in res.registre_mecquois.items()} }")
            print(f"  • Mémoire MEDINOIS : { {k: repr(v) for k, v in res.memoire_medinoise.items()} }")
            print(f"  • Cycles dt consom.: {interp.vm.horloge.dt_consomme} / {interp.vm.horloge.dt_max}")
            print("=" * 80)
        return 0 if res.succes else 1

    if args.commande == "check":
        source = _lire_fichier(args.fichier)
        rapport = ValidateurOntologiqueAstroQode().valider_source(source)
        print(f"Validation de {args.fichier} : {'VALIDE' if rapport.valide else 'INVALIDE'}")
        print(f"  Constantes MECQUOIS : {rapport.constantes_mecquoises}")
        print(f"  Variables MEDINOIS  : {rapport.variables_medinoises}")
        for d in rapport.diagnostics:
            print(f"  [{d.niveau}] ({d.code}) {d.message}")
        return 0 if rapport.valide else 1

    if args.commande == "format":
        source = _lire_fichier(args.fichier)
        code_fmt = FormateurAstroQode().formater_source(source)
        if args.write:
            Path(args.fichier).write_text(code_fmt, encoding="utf-8")
            print(f"Fichier formaté avec succès : {args.fichier}")
        else:
            print(code_fmt)
        return 0

    if args.commande == "transpile":
        source = _lire_fichier(args.fichier)
        code_py = TranspilateurPythonAstroQode().transpiler_source(source)
        if args.out:
            Path(args.out).write_text(code_py, encoding="utf-8")
            print(f"Code Python généré dans : {args.out}")
        else:
            print(code_py)
        return 0

    if args.commande == "asm":
        source = _lire_fichier(args.fichier)
        print(AssembleurScapulaire().formater_listing(source))
        return 0

    if args.commande == "ports":
        diag = PontMaterielEmuleAlmizan.diagnostic_complet_pont_materiel()
        print(json.dumps(diag, indent=2, ensure_ascii=False))
        return 0

    if args.commande == "qasm":
        compil = CompilateurQasmIsaAstroQode()
        cible = args.cible
        if cible.upper() in ("BELL", "GROVER", "QFT"):
            res_q = compil.compiler_et_executer_circuit(cible.upper(), shots=args.shots)
        else:
            source = _lire_fichier(cible)
            res_q = compil.compiler_source_aq(source, shots=args.shots, executer_sur_5030=True)
        print("=" * 80)
        print(f"COMPILATION OPENQASM 2.0 & EXÉCUTION DIE SILICIUM (:5030) — {res_q.nom_programme}")
        print("=" * 80)
        print(res_q.code_openqasm_2)
        print("-" * 80)
        print("TRAMES ISA DIE SILICIUM :")
        for trame in res_q.trames_isa_die:
            print(f"  {trame}")
        print("-" * 80)
        print("RÉSULTAT EXÉCUTION SUR :5030 :")
        print(json.dumps(res_q.execution_die_5030, indent=2, ensure_ascii=False))
        return 0

    if args.commande == "seal":
        if args.verify:
            verif = ScelleurMemoireAstroQode.verifier_integrite_registre()
            print(json.dumps(verif, indent=2, ensure_ascii=False))
            return 0 if verif["integrite_globale_valide"] else 1
        interp = InterpreteurAstroQode()
        chemin_v4 = RACINE_SYSTEME / "bibliotheques" / "stdlib_aq" / "suite_logique_silicium_qasm_v4.aq"
        res_exec = interp.executer_source(chemin_v4.read_text(encoding="utf-8"))
        sceau = ScelleurMemoireAstroQode.sceller_etat_execution(
            nom_sceau="sceau_cli_astro_qode_v4",
            rapport_vm=res_exec.rapport_vm,
            diagnostic_pont=PontMaterielEmuleAlmizan.diagnostic_complet_pont_materiel(),
        )
        print(json.dumps(sceau, indent=2, ensure_ascii=False))
        return 0

    if args.commande == "studio":
        chemin_html = StudioDashboardAstroQode.generer_dashboard_html()
        print(f"Dashboard HTML5/SVG généré avec succès : {chemin_html}")
        return 0

    if args.commande == "unisson":
        if args.json:
            rap = MatriceFondatriceUnisson.calculer_matrice_unisson_complete(
                masse_or_grammes=args.or_g,
                masse_argent_grammes=args.argent_g,
            )
            print(json.dumps(rap, indent=2, ensure_ascii=False))
        else:
            print(
                MatriceFondatriceUnisson.formater_rapport_console(
                    masse_or_grammes=args.or_g,
                    masse_argent_grammes=args.argent_g,
                )
            )
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
