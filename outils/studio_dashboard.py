# -*- coding: utf-8 -*-
r"""
Outil 7 : Studio Visuel & Tableau de Bord HTML5/SVG (`studio_dashboard.py`)
===========================================================================
Génère le tableau de bord interactif complet `memoire_aq/dashboard_astro_qode.html`
réunissant sur une interface visuelle unique :
1. Le Radar en Spirale des **27 Formes (`F0` à `F26` : 14 de base + 13 Duales Al-Mizan)** en SVG vectoriel.
2. L'état en direct des **Ports Locaux (`:5025` SCPI, `:5026` Cryo, `:5030` Die Silicium, `:8000`, `:8765`)**.
3. Le Pipeline Biomécanique (**Omoplate $\alpha/\beta/\gamma$ -> Bras `dt` -> 5 Doigts**).
4. La **Sphère Holographique ($\oplus$ Calotte Haute / Corde / $\otimes$ Calotte Basse)** et la **Triade `Bit/Qubit/i-Bit`**.
5. Le Circuit **OpenQASM 2.0** généré et les **Sceaux Cryptographiques SHA-256**.
"""

from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path

from bibliotheques.lib_almizan_extension import (
    COMBLE_CIBLE,
    CONSTANTE_MECQUOISE_C,
    CONSTANTE_MEDINOISE_M,
    EPSILON,
    JAUGE_AIR,
    LES_27_FORMES_ETENDUES,
    LIGNE_REF,
    MIZAN,
    PHASES_15_CYCLE_HARMONIQUE,
    PLAFOND_EFFECTIF,
    PRODUIT_MEDINOIS,
    RMS,
    SphereHolographiqueAlmizan,
    TriadeBitQubitIBit,
)
from bibliotheques.lib_anatomie import PipelineCinqDoigts
from bibliotheques.lib_matrice_unisson_or_argent import MatriceFondatriceUnisson
from bibliotheques.lib_pont_materiel_emule import PontMaterielEmuleAlmizan
from bibliotheques.lib_temporelle import CLOCK_DT_KERNEL, CLOCK_DX_SOLEIL, CLOCK_DY_LUNE, CLOCK_DZ_TERRE
from lang.compilateur_qasm_isa import CompilateurQasmIsaAstroQode
from .scelleur_cryptographique import DOSSIER_MEMOIRE_AQ, ScelleurMemoireAstroQode


class StudioDashboardAstroQode:
    """Génère le tableau de bord HTML5/SVG autonome d'ASTRO-Q°ODE V4.0."""

    @staticmethod
    def _generer_svg_radar_27_formes() -> str:
        lignes_svg = [
            '<svg viewBox="-165 -165 330 330" width="380" height="380" style="background:#080c14;border-radius:12px;border:1px solid #1e293b;">',
            '<circle cx="0" cy="0" r="135" fill="none" stroke="#1e293b" stroke-dasharray="3,3"/>',
            '<circle cx="0" cy="0" r="95" fill="none" stroke="#1e293b" stroke-dasharray="3,3"/>',
            '<circle cx="0" cy="0" r="55" fill="none" stroke="#1e293b" stroke-dasharray="3,3"/>',
        ]
        # Forme 0 au centre
        lignes_svg.append('<circle cx="0" cy="0" r="7" fill="#facc15" stroke="#fff" stroke-width="1.5"/>')
        lignes_svg.append('<text x="0" y="-12" text-anchor="middle" font-size="8" fill="#facc15">F0: HÉLIUM</text>')

        for idx in range(1, 27):
            fe = LES_27_FORMES_ETENDUES[idx]
            rayon = 55.0 + (idx / 26.0) * 80.0
            x = rayon * math.cos(fe.phase_rad)
            y = rayon * math.sin(fe.phase_rad)
            couleur = "#38bdf8" if idx <= 13 else "#c084fc"
            lignes_svg.append(
                f'<line x1="0" y1="0" x2="{x:.1f}" y2="{y:.1f}" stroke="{couleur}" stroke-opacity="0.22" stroke-width="1"/>'
            )
            lignes_svg.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{couleur}"/>'
            )
            lignes_svg.append(
                f'<text x="{x * 1.11:.1f}" y="{y * 1.11:.1f}" text-anchor="middle" font-size="6.5" fill="#e2e8f0">F{idx}</text>'
            )

        lignes_svg.append("</svg>")
        return "\n".join(lignes_svg)

    @classmethod
    def generer_dashboard_html(cls, chemin_sortie: Path | None = None) -> Path:
        DOSSIER_MEMOIRE_AQ.mkdir(parents=True, exist_ok=True)
        cible = chemin_sortie or (DOSSIER_MEMOIRE_AQ / "dashboard_astro_qode.html")

        etat_ports = PontMaterielEmuleAlmizan.sonder_tous_les_ports()
        cryo = PontMaterielEmuleAlmizan.lire_capteur_cryo_5026()
        sphere = SphereHolographiqueAlmizan.cartographier(float(cryo["temp_mK"]))
        triade = TriadeBitQubitIBit.synchroniser(8)
        qasm_exec = CompilateurQasmIsaAstroQode.compiler_et_executer_sur_die_5030("BELL")
        audit_sceaux = ScelleurMemoireAstroQode.verifier_integrite_sceaux()
        unisson = MatriceFondatriceUnisson.calculer_matrice_unisson_complete(85.0, 595.0)
        pipeline = PipelineCinqDoigts().tableau_pipeline_complet()
        svg_radar = cls._generer_svg_radar_27_formes()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lignes_ports = ""
        for p_str, info in etat_ports["detail_ports"].items():
            badge = (
                '<span style="color:#4ade80;font-weight:bold;">ACTIF</span>'
                if info["actif"]
                else '<span style="color:#94a3b8;">STANDBY (Fallback Actif)</span>'
            )
            lignes_ports += f"<tr><td><code>:{p_str}</code></td><td>{info['description']}</td><td>{badge}</td></tr>"

        lignes_formes = ""
        for idx, fe in LES_27_FORMES_ETENDUES.items():
            lignes_formes += (
                f"<tr><td><b>F{idx:02d}</b></td><td><code>{fe.code_court}</code></td>"
                f"<td>{fe.forme_geometrique}</td><td>{fe.octave}</td>"
                f"<td>{fe.phase_rad:.4f}</td><td>{fe.image_fonction_d:.4f}</td></tr>"
            )

        lignes_doigts = ""
        for seg in pipeline:
            lignes_doigts += (
                f"<tr><td><b>{seg['segment']}</b></td><td>{seg['role_systeme']}</td>"
                f"<td><code>{seg['symbole']}</code></td><td>{seg['paradigme']}</td></tr>"
            )

        lignes_unisson = ""
        for nom_dim, vals in unisson["matrice_4x4"]["lignes"].items():
            lignes_unisson += (
                f"<tr><td><b>{nom_dim}</b></td><td><code>{vals[0]:.6f}</code></td>"
                f"<td><code>{vals[1]:.6f}</code></td><td><code>{vals[2]:.6f}</code></td>"
                f"<td><code>{vals[3]:.6f}</code></td></tr>"
            )
        v_or = unisson["valeur_or"]
        v_ag = unisson["valeur_argent"]

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <title>STUDIO VISUEL ASTRO-Q°ODE V4.0 — IMAM8MAHDI × Al-Mizan</title>
  <style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0b0f19; color: #e2e8f0; margin: 0; padding: 24px; }}
    h1, h2, h3 {{ color: #38bdf8; margin-top: 0; }}
    .header {{ background: linear-gradient(135deg, #0f172a, #1e1b4b); padding: 20px 24px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; margin-bottom: 24px; }}
    .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 18px; box-shadow: 0 4px 16px rgba(0,0,0,0.35); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ text-align: left; padding: 7px 9px; border-bottom: 1px solid #1f2937; }}
    th {{ color: #93c5fd; background: #1e293b; }}
    code, pre {{ font-family: Consolas, monospace; background: #0f172a; color: #f8fafc; padding: 2px 6px; border-radius: 5px; }}
    pre {{ padding: 12px; overflow-x: auto; border: 1px solid #1e293b; }}
    .pill {{ display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; background: #1e293b; color: #38bdf8; margin-right: 8px; margin-bottom: 6px; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>STUDIO VISUEL ASTRO-Q°ODE V4.0 — IMAM8MAHDI × AL-MIZAN</h1>
    <p>Horodatage : <code>{ts}</code> · Horloge Kernel <code>dt = {CLOCK_DT_KERNEL}</code> · Bride <code>MIZAN = {MIZAN}</code> · Ligne <code>{LIGNE_REF}</code> · RMS <code>{RMS}</code> · <code>qubit_physique_local = false</code></p>
    <div>
      <span class="pill">C = {CONSTANTE_MECQUOISE_C}</span>
      <span class="pill">M = {CONSTANTE_MEDINOISE_M}</span>
      <span class="pill">JAUGE_AIR = {JAUGE_AIR}</span>
      <span class="pill">PRODUIT = {PRODUIT_MEDINOIS}</span>
      <span class="pill">27 Formes (F0..F26)</span>
      <span class="pill">52 Rails (A-Z / a-z)</span>
      <span class="pill">15 Phases Harmoniques</span>
      <span class="pill">Sceaux SHA-256 : {audit_sceaux['nb_valides']}/{audit_sceaux['nb_verifies']} OK</span>
    </div>
  </div>

  <div class="grid">
    <div class="card" style="text-align:center;">
      <h2>Radar Fractal des 27 Formes (F0 + 13 ⊕ 13)</h2>
      {svg_radar}
      <p style="font-size:12px;color:#94a3b8;">Bleu : Octave 1 Lumière (F1..F13) · Violet : Octave 2 Duale Al-Mizan (F14..F26) · Or : Origine F0 Hélium</p>
    </div>

    <div class="card">
      <h2>Pont Temps Réel & Télémétrie (:5025, :5026, :5030)</h2>
      <table>
        <thead><tr><th>Port</th><th>Service Local Al-Mizan</th><th>État</th></tr></thead>
        <tbody>{lignes_ports}</tbody>
      </table>
      <h3 style="margin-top:16px;">Sphère Holographique (⊕ / Corde / ⊗) & Cryogénie</h3>
      <p>Température Capteur <code>:5026</code> : <b>{cryo['temp_mK']} mK</b> (Seuil Killswitch : {cryo['seuil_killswitch_mK']} mK)</p>
      <p>Identité Corde <code>exp(A ⊕ B) = exp(A) ⊗ exp(B)</code> : <b>Validée</b> (Tension = <code>{sphere['tension_membrane']}</code>)</p>
      <p>Born Bridé Mizan : <code>{sphere['born_bride_mizan']}</code></p>
      <p>Triade <code>Bit ⊗ ({LIGNE_REF}) / Qubit ⊕ ({MIZAN}) / i-Bit Ω (RMS={RMS}, 8 cycles Si-29)</code> : <b>{triade['statut']}</b></p>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>Axe d'Exécution Biomécanique (Omoplate -> Bras -> 5 Doigts)</h2>
      <table>
        <thead><tr><th>Segment Anatomique</th><th>Rôle Système</th><th>Symbole</th><th>Paradigme</th></tr></thead>
        <tbody>{lignes_doigts}</tbody>
      </table>
      <p style="margin-top:12px;font-size:12px;color:#94a3b8;">Cycles Temporels : dx (Soleil) = {CLOCK_DX_SOLEIL} · dy (Lune) = {CLOCK_DY_LUNE} · dz (Terre) = {CLOCK_DZ_TERRE}</p>
    </div>

    <div class="card">
      <h2>Compilateur Quantique OpenQASM 2.0 & Exécution DIE (:5030)</h2>
      <p>Mode Backend : <code>{qasm_exec['mode_execution_die']}</code> · Fidélité ZNE Zéro-Bruit : <b>{qasm_exec['analyse_zne_et_peau']['fidelite_zero_bruit_zne']}</b></p>
      <pre>{qasm_exec['openqasm_2_0'].strip()}</pre>
      <p>Probabilités Born protégées : <code>{qasm_exec['analyse_zne_et_peau']['born_protege_mizan']}</code></p>
    </div>
  </div>

  <div class="card" style="margin-bottom:24px;">
    <h2>Matrice Fondatrice de l'Unisson (4×4) — Valeur de l'Or (Au) et de l'Argent (Ag)</h2>
    <p>Équation : <code>{unisson['equation_unisson']}</code></p>
    <table>
      <thead><tr><th>Dimension de l'Unisson</th><th>Pôle Or (Au ⊕)</th><th>Pôle Argent (Ag ⊗)</th><th>Ratio Or/Ag</th><th>Accord Unisson Ω</th></tr></thead>
      <tbody>{lignes_unisson}</tbody>
    </table>
    <p style="margin-top:12px;">
      <b>Or (Au, Z={v_or['numero_atomique_z']})</b> : {v_or['masse_evaluee_grammes']} g = <code>{v_or['nb_unites_canoniques']} Mithqal</code> · φ⁻¹ = <code>{v_or['frequence_harmonique_mizan']}</code> · Énergie = <code>{v_or['energie_aq_joules_ou_kelvin']}</code> · Valeur = <b>{v_or['valeur_monetaire_estimee_eur']} EUR</b><br/>
      <b>Argent (Ag, Z={v_ag['numero_atomique_z']})</b> : {v_ag['masse_evaluee_grammes']} g = <code>{v_ag['nb_unites_canoniques']} Dirhams</code> · δ_S⁻¹ = <code>{v_ag['frequence_harmonique_mizan']}</code> · Signal = <code>{v_ag['energie_aq_joules_ou_kelvin']}</code> · Valeur = <b>{v_ag['valeur_monetaire_estimee_eur']} EUR</b>
    </p>
  </div>

  <div class="card">
    <h2>Table Complète des 27 Formes (Dépassement du Seuil 13 sous D = [{LIGNE_REF}, {MIZAN}])</h2>
    <table>
      <thead><tr><th>Index</th><th>Code</th><th>Forme Géométrique</th><th>Octave</th><th>Phase (rad)</th><th>Image D</th></tr></thead>
      <tbody>{lignes_formes}</tbody>
    </table>
  </div>
</body>
</html>
"""
        cible.write_text(html, encoding="utf-8")
        return cible
