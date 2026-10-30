# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""Génère les pages « Règlement des dettes et redistribution » (FR/EN/AR).

Contenu strictement honnête : les règles sont citées par verset et paraphrasées,
les calculs sont des identités arithmétiques sur des conventions déclarées.
Aucun fonds n'est détenu, perçu ou distribué. La parabole des sept épis n'est
pas un rendement. La complétude revendiquée est celle du protocole déclaré.

Usage :
    py -3 oeuvre_universelle/generer_page_reglement_dettes_redistribution.py
"""

from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from oeuvre_universelle.reglement_dettes_redistribution import resoudre, verifier
else:
    from .reglement_dettes_redistribution import resoudre, verifier

RACINE = Path(__file__).resolve().parent.parent
WEB_CLOUD = RACINE / "web_cloud"
RESULTATS = RACINE / "resultats" / "oeuvre_universelle"

LANGUES = ("fr", "en", "ar")
CHEMINS = {
    "fr": "/reglement-dettes-redistribution",
    "en": "/reglement-dettes-redistribution/en",
    "ar": "/reglement-dettes-redistribution/ar",
}
PAGES = {
    "fr": WEB_CLOUD / "reglement_dettes_redistribution.html",
    "en": WEB_CLOUD / "reglement_dettes_redistribution_en.html",
    "ar": WEB_CLOUD / "reglement_dettes_redistribution_ar.html",
}
DONNEES_JSON = WEB_CLOUD / "reglement_dettes_redistribution_resultats.json"
ARCHIVE_JSON = RESULTATS / "reglement_dettes_redistribution.json"

AUTEUR = "M. Ahmed EL BAHLOUL (IMAM8MAHDI)"
SITE = "https://www.al-mizan.world"
DATE_JOUR = date.today().isoformat()


def _ech(v: Any) -> str:
    return html.escape(str(v), quote=True)


def _carte(donnees: Dict[str, Any], eq_id: str) -> Any:
    for eq in donnees["equations"]:
        if eq["id"] == eq_id:
            return eq["detail"]
    raise KeyError(eq_id)


def _f(x: float, n: int = 6) -> str:
    return f"{x:,.{n}f}".replace(",", "\u202f")


def _c(x: float, n: int = 6) -> str:
    return f"{x:.{n}f}"


def _fig_num(x: float, n: int = 1, lang: str = "fr") -> str:
    texte = f"{x:.{n}f}"
    return texte.replace(".", ",") if lang == "fr" else texte


# ============================================================================
# FIGURE — cascade de règlement (EQ-03) + continuité (EQ-10), calculées
# ============================================================================

FIG_LABELS = {
    "fr": {
        "titre_gauche": "Règlement d’une dette de 1 000 €",
        "titre_droit": "Continuité : Wₙ/W₀ = 0,975ⁿ",
        "dette": "Dette", "verse": "Versé", "remise": "Remise", "reste": "Reste",
        "demi": "n½", "ans": "ans", "valeur": "Wₙ/W₀",
    },
    "en": {
        "titre_gauche": "Settling a debt of 1,000 €",
        "titre_droit": "Continuity: Wₙ/W₀ = 0.975ⁿ",
        "dette": "Debt", "verse": "Paid", "remise": "Forgiven", "reste": "Remaining",
        "demi": "n½", "ans": "years", "valeur": "Wₙ/W₀",
    },
    "ar": {
        "titre_gauche": "تسوية دين قدره 1000 €",
        "titre_droit": "الاستمرارية: Wₙ/W₀ = 0.975ⁿ",
        "dette": "الدين", "verse": "المدفوع", "remise": "الإبراء", "reste": "الباقي",
        "demi": "n½", "ans": "سنة", "valeur": "Wₙ/W₀",
    },
}


def _figure(donnees: Dict[str, Any], lang: str) -> str:
    dette = _carte(donnees, "EQ-03")
    cont = _carte(donnees, "EQ-10")
    lab = FIG_LABELS[lang]

    # Panneau gauche : cascade dette / versé / remise / reste.
    valeurs = [
        (dette["dette_eur"], lab["dette"]),
        (dette["verse_eur"], lab["verse"]),
        (dette["remise_effective_eur"], lab["remise"]),
        (dette["reste_eur"], lab["reste"]),
    ]
    maximum = max(v[0] for v in valeurs) or 1.0
    base_y, hauteur = 350.0, 240.0
    barres = []
    for i, (valeur, etiquette) in enumerate(valeurs):
        h = valeur / maximum * hauteur
        x = 70.0 + i * 105.0
        y = base_y - h
        barres.append(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='76' height='{h:.1f}' "
            "fill='#1f5f8b' opacity='0.82' rx='4'/>"
            f"<text x='{x + 38:.1f}' y='{y - 8:.1f}' text-anchor='middle' "
            f"font-family='Segoe UI,Arial' font-size='12' fill='#33475a'>"
            f"{_fig_num(valeur, 0, lang)} €</text>"
            f"<text x='{x + 38:.1f}' y='{base_y + 20:.1f}' text-anchor='middle' "
            f"font-family='Segoe UI,Arial' font-size='13' fill='#0f3d5c'>{_ech(etiquette)}</text>"
        )

    # Panneau droit : courbe de continuité W_n/W_0 = (1−τ)^n.
    x0, x1, y0, y1 = 620.0, 1090.0, 350.0, 70.0
    taux = cont["taux"]
    points = []
    for n in range(0, 81):
        facteur = (1.0 - taux) ** n
        x = x0 + n / 80.0 * (x1 - x0)
        y = y0 - facteur * (y0 - y1)
        points.append(f"{x:.1f},{y:.1f}")
    demi = cont["demi_vie_ans"]
    x_demi = x0 + demi / 80.0 * (x1 - x0)
    y_demi = y0 - 0.5 * (y0 - y1)
    ticks = []
    for n in (0, 20, 40, 60, 80):
        x = x0 + n / 80.0 * (x1 - x0)
        ticks.append(
            f"<line x1='{x:.1f}' y1='{y0}' x2='{x:.1f}' y2='{y0 + 5}' stroke='#5b6b7a'/>"
            f"<text x='{x:.1f}' y='{y0 + 20}' text-anchor='middle' "
            f"font-family='Segoe UI,Arial' font-size='12' fill='#5b6b7a'>{n}</text>"
        )
    for valeur, libelle in ((1.0, "1.0"), (0.5, "0.5"), (0.0, "0.0")):
        y = y0 - valeur * (y0 - y1)
        ticks.append(
            f"<line x1='{x0 - 5}' y1='{y:.1f}' x2='{x0}' y2='{y:.1f}' stroke='#5b6b7a'/>"
            f"<text x='{x0 - 10}' y='{y + 4:.1f}' text-anchor='end' "
            f"font-family='Segoe UI,Arial' font-size='12' fill='#5b6b7a'>{libelle}</text>"
        )
    return (
        "<svg viewBox='0 0 1120 420' role='img' "
        "aria-label='Cascade de règlement de dette et courbe de continuité'>"
        f"<text x='260' y='30' text-anchor='middle' font-family='Segoe UI,Arial' font-size='15' "
        f"font-weight='700' fill='#0f3d5c'>{_ech(lab['titre_gauche'])}</text>"
        + "".join(barres) +
        f"<text x='855' y='30' text-anchor='middle' font-family='Segoe UI,Arial' font-size='15' "
        f"font-weight='700' fill='#0f3d5c'>{_ech(lab['titre_droit'])}</text>"
        f"<line x1='{x0}' y1='{y0}' x2='{x1}' y2='{y0}' stroke='#5b6b7a' stroke-width='1.2'/>"
        f"<line x1='{x0}' y1='{y0}' x2='{x0}' y2='{y1}' stroke='#5b6b7a' stroke-width='1.2'/>"
        f"<polyline points='{' '.join(points)}' fill='none' stroke='#1f5f8b' stroke-width='2.4'/>"
        f"<line x1='{x_demi:.1f}' y1='{y0}' x2='{x_demi:.1f}' y2='{y_demi:.1f}' "
        "stroke='#b45309' stroke-width='1.6' stroke-dasharray='5 4'/>"
        f"<circle cx='{x_demi:.1f}' cy='{y_demi:.1f}' r='4' fill='#b45309'/>"
        f"<text x='{x_demi + 8:.1f}' y='{y_demi - 10:.1f}' font-family='Segoe UI,Arial' "
        f"font-size='12' fill='#8a4b06'>{lab['demi']} = {_fig_num(demi, 2, lang)} {_ech(lab['ans'])}</text>"
        + "".join(ticks) +
        "</svg>"
    )


# ============================================================================
# TEXTES DES CARTES (FR / EN / AR)
# ============================================================================

EQ_TEXT: Dict[str, Dict[str, tuple]] = {
    "EQ-01": {
        "fr": ("La zakat légale : seuil et taux",
               "La zakat est 1/40 (2,5 %) de la richesse au-dessus du nisab ; le nisab argent du dossier est de 595 g.",
               "Sous le seuil, la zakat est nulle : la règle protège les petits patrimoines. Les montants utilisent l'étalonnage du dossier, pas les cours réels."),
        "en": ("Legal zakat: threshold and rate",
               "Zakat is 1/40 (2.5%) of wealth above the nisab; the project's silver nisab is 595 g.",
               "Below the threshold zakat is zero: the rule protects small estates. Amounts use the project calibration, not live market prices."),
        "ar": ("الزكاة الشرعية: النصاب والمعدل",
               "الزكاة 1/40 (2.5%) من الثروة التي تبلغ النصاب، والنصاب الفضي في المشروع 595 غرامًا.",
               "دون النصاب تكون الزكاة صفرًا: القاعدة تحمي صغار المالكين. المبالغ تستخدم معايرة المشروع لا أسعار السوق اللحظية."),
    },
    "EQ-02": {
        "fr": ("Les huit catégories coraniques",
               "Le verset 9:60 énumère huit catégories : les pauvres, les nécessiteux, ceux qui ont la charge de la collecte, ceux dont les cœurs sont à rallier, l'affranchissement, les endettés, la cause de Dieu et le voyageur.",
               "Le Coran fixe les catégories, pas des parts égales. Le module retient 1/8 par catégorie comme convention de calcul déclarée ; la somme vaut 1."),
        "en": ("The eight Quranic categories",
               "Verse 9:60 lists eight categories: the poor, the needy, those employed to collect it, those whose hearts are to be reconciled, to free captives, debtors, in the cause of God, and the wayfarer.",
               "The Quran fixes the categories, not equal shares. The module uses one eighth per category as a declared calculation convention; the sum is one."),
        "ar": ("الفئات الثماني في الآية",
               "الآية 9:60 تعدّد ثماني فئات: الفقراء، والمساكين، والعاملين عليها، والمؤلفة قلوبهم، والرقاب، والغارمين، وفي سبيل الله، وابن السبيل.",
               "القرآن يحدد الفئات لا أنصبة متساوية. الوحدة تعتمد الثمن لكل فئة كاصطلاح حسابي معلن، والمجموع يساوي واحدًا."),
    },
    "EQ-03": {
        "fr": ("Report et remise",
               "Le verset 2:280 demande de reporter l'échéance du débiteur insolvable et déclare la remise meilleure. Formule : reste = dette − versé − remis, jamais négatif.",
               "La remise ne peut dépasser le reste dû ; une demande supérieure est plafonnée. Le module ne juge pas la bonne foi et ne contraint personne."),
        "en": ("Respite and forgiveness",
               "Verse 2:280 asks for respite for the insolvent debtor and calls forgiveness better. Formula: remainder = debt − paid − forgiven, never negative.",
               "Forgiveness cannot exceed the remaining debt; a larger request is capped. The module does not judge good faith and enforces nothing."),
        "ar": ("إنظار المعسر والإبراء",
               "الآية 2:280 تطلب إنظار المدين المعسر وتجعل الإبراء أفضل. الصيغة: الباقي = الدين − المدفوع − الإبراء، بلا سالب.",
               "الإبراء لا يتجاوز الباقي؛ وإذا طُلب أكثر يُقيَّد بالباقي. الوحدة لا تحكم على حسن النية ولا تُلزم أحدًا."),
    },
    "EQ-04": {
        "fr": ("Qard hasan contre riba",
               "Le prêt d'honneur restitue le capital sans surplus : R = C. Le prêt à intérêt compose : R = C(1+r)^n.",
               "Pour 10 000 à 5 % sur 10 ans, le surcoût est 6 288,95. Le moteur rejette tout taux de riba positif."),
        "en": ("Qard hasan versus riba",
               "The goodly loan returns the principal with no surplus: R = C. An interest loan compounds: R = C(1+r)^n.",
               "For 10,000 at 5% over 10 years, the extra is 6,288.95. The engine rejects any positive riba rate."),
        "ar": ("القرض الحسن مقابل الربا",
               "القرض الحسن يعيد رأس المال دون زيادة: R = C. القرض بفائدة يتراكم: R = C(1+r)^n.",
               "لعشرة آلاف يورو بفائدة 5% لعشر سنوات، الزيادة 6288.95 يورو. المحرك يرفض أي معدل ربا موجب."),
    },
    "EQ-05": {
        "fr": ("Capacité de remboursement",
               "Capacité = revenu − dépenses essentielles, jamais négative ; durée = arrondi supérieur de la dette sur la capacité.",
               "Si le revenu est inférieur aux dépenses, la capacité est nulle : le résultat est un report, pas une contrainte. La frontière des dépenses essentielles est une convention déclarée."),
        "en": ("Repayment capacity",
               "Capacity = income − essential expenses, never negative; duration = ceiling of debt over capacity.",
               "If income is below expenses, capacity is zero, so the result is a deferral, not coercion. The essential-expense line is a declared convention."),
        "ar": ("القدرة على السداد",
               "القدرة = الدخل − النفقات الأساسية، ولا تكون سالبة؛ والمدة = تقريب أعلى للدين على القدرة.",
               "إذا كان الدخل أقل من النفقات فالقدرة صفر، فتكون النتيجة إنظارًا لا إلزامًا. حدّ النفقات الأساسية اصطلاح معلن."),
    },
    "EQ-06": {
        "fr": ("Parts successorales fixes",
               "Cas déclaré : conjoint, père, mère, un fils, une fille, après dettes. Conjoint 1/8, père 1/6, mère 1/6, reste 13/24 partagé 2:1.",
               "La somme vaut exactement 1. Ce n'est pas un calculateur général : awl, radd et autres cas sont exclus."),
        "en": ("Fixed inheritance shares",
               "Declared case: spouse, father, mother, one son, one daughter, after debts. Spouse 1/8, father 1/6, mother 1/6, remainder 13/24 split 2:1.",
               "The sum is exactly one. This is not a general inheritance calculator: awl, radd and other cases are excluded."),
        "ar": ("الأنصبة الشرعية في الميراث",
               "حالة معلنة: زوج، وأب، وأم، وابن، وبنت، بعد الديون. الزوج 1/8، والأب 1/6، والأم 1/6، والباقي 13/24 للابن والبنت بنسبة 2:1.",
               "المجموع يساوي واحدًا بالضبط. الوحدة ليست حاسبة ميراث عامة: لا تعالج العول والرد ولا الحالات الأخرى."),
    },
    "EQ-07": {
        "fr": ("La zakat comme stabilisateur",
               "Sur une masse W, l'injection annuelle vaut 2,5 % de W et la masse tourne en 40 ans à flux constant.",
               "Modèle agrégé sans comportement des agents ni croissance ; ce n'est pas une prévision économique."),
        "en": ("Zakat as an automatic stabiliser",
               "At aggregate wealth W, the annual injection is 2.5% of W, and the stock turns over in 40 years at constant flow.",
               "An aggregate model without agent behaviour or growth; not an economic forecast."),
        "ar": ("الزكاة كمثبِّت تلقائي",
               "على مستوى الكتلة W، الحقن السنوي = 2.5% × W، ودوران الكتلة 40 سنة عند تدفق ثابت.",
               "نموذج مجمّع بلا سلوك أفراد ولا نمو؛ ليس تنبؤًا اقتصاديًا."),
    },
    "EQ-08": {
        "fr": ("Redistribution et inégalité",
               "Deux groupes égaux : Gini = (a−b)/(2(a+b)) ; un transfert t le réduit de t/(a+b).",
               "Exemple : 0,25, puis 0,125, puis 0 à l'égalisation complète. Modèle-jouet, pas une mesure de la distribution réelle."),
        "en": ("Redistribution and inequality",
               "Two equal groups: Gini = (a−b)/(2(a+b)); a transfer t lowers it by t/(a+b).",
               "Example: 0.25, then 0.125, then 0 at full equalisation. A toy model, not a measurement of real distribution."),
        "ar": ("إعادة التوزيع واللامساواة",
               "نموذج مجموعتين متساويتين: جيني = (a−b)/(2(a+b))، والتحويل t يخفضه بمقدار t/(a+b).",
               "مثال: 0.25 ثم 0.125 ثم 0 عند التسوية الكاملة. هذا نموذج لعبة وليس قياسًا للتوزيع الحقيقي."),
    },
    "EQ-09": {
        "fr": ("La parabole de l'abondance",
               "Verset 2:261 : un grain devient sept épis, chacun portant cent grains : 7 × 100 = 700.",
               "C'est une parabole révélée, pas un rendement financier ni une promesse de multiplication ; elle n'entre dans aucun calcul de solvabilité."),
        "en": ("The parable of abundance",
               "Verse 2:261: one grain becomes seven spikes, each with a hundred grains: 7 × 100 = 700.",
               "This is a revealed parable, not a financial return or a promise of multiplication; it enters no solvency calculation."),
        "ar": ("مثل الوفرة",
               "الآية 2:261: حبة تصير سبع سنابل، في كل سنبلة مئة حبة: 7 × 100 = 700.",
               "هذا مثل قرآني وليس عائدًا ماليًا ولا وعدًا بمضاعفة الأموال؛ لا يدخل في أي حساب جدوى."),
    },
    "EQ-10": {
        "fr": ("Continuité du flux",
               "Stock après n années : W_n = W_0(1−τ)^n ; demi-vie = ln(0,5)/ln(0,975) ≈ 27,38 ans.",
               "La continuité vient du flux, pas de l'accumulation. Le modèle est sans croissance et sans inflation."),
        "en": ("Continuity of the flow",
               "Stock after n years: W_n = W_0(1−τ)^n; half-life = ln(0.5)/ln(0.975) ≈ 27.38 years.",
               "Continuity comes from the flow, not from accumulation. The model has no growth and no inflation."),
        "ar": ("استمرارية التدفق",
               "المخزون بعد n سنة: W_n = W_0(1−τ)^n، ونصف العمر = ln(0.5)/ln(0.975) ≈ 27.38 سنة.",
               "الاستمرارية تأتي من التدفق لا من التراكم. النموذج بلا نمو ولا تضخم."),
    },
    "EQ-11": {
        "fr": ("Conservation du flux",
               "Zakat = somme des allocations + réserve ; la réserve est une fraction déclarée de la zakat.",
               "Identité comptable : aucune unité ne disparaît du circuit déclaré. Le taux de réserve est une convention de gouvernance."),
        "en": ("Conservation of the flow",
               "Zakat = sum of allocations + reserve; the reserve is a declared fraction of zakat.",
               "An accounting identity: no unit disappears from the declared circuit. The reserve rate is a governance convention."),
        "ar": ("حفظ التدفق",
               "الزكاة = مجموع الأنصبة + الاحتياطي؛ والاحتياطي نسبة معلنة من الزكاة.",
               "هوية محاسبية: لا تختفي أي وحدة من الدائرة المعلنة. نسبة الاحتياطي اصطلاح حوكمة."),
    },
    "EQ-12": {
        "fr": ("Indice de justice et de paix",
               "J = 1 − T, avec T = 0,40 riba + 0,20 partage + 0,20 zakat + 0,20 adossement.",
               "Scénario halal : J = 1 ; scénario usuraire : T = 0,68 et J = 0,32. Convention interne, pas une mesure de la paix sociale."),
        "en": ("Justice and peace index",
               "J = 1 − T, where T = 0.40 riba + 0.20 sharing + 0.20 zakat + 0.20 asset backing.",
               "Halal scenario: J = 1; usurious scenario: T = 0.68 and J = 0.32. An internal convention, not a measure of social peace."),
        "ar": ("مؤشر العدل والسلام",
               "J = 1 − T، حيث T = 0.40 ربا + 0.20 مشاركة + 0.20 زكاة + 0.20 أداء عيني.",
               "السيناريو الحلال: J = 1؛ السيناريو الربوي: T = 0.68 وJ = 0.32. المؤشر اصطلاح داخلي لا يقيس السلام الاجتماعي."),
    },
    "EQ-13": {
        "fr": ("Les quatre piliers et la complétude du protocole",
               "P1 identité et mandat, P2 intégrité et provenance, P3 confidentialité et maîtrise, P4 résilience et preuve ; chacun a un répondant dans le protocole de dette.",
               "K = 4/4 = 1 exprime la complétude du protocole déclaré, pas celle du monde."),
        "en": ("The four pillars and protocol completeness",
               "P1 identity and mandate, P2 integrity and provenance, P3 confidentiality and control, P4 resilience and proof; each has a counterpart in the debt protocol.",
               "K = 4/4 = 1 expresses the completeness of the declared protocol, not of the world."),
        "ar": ("الركائز الأربع واكتمال البروتوكول",
               "P1 الهوية والتفويض، P2 السلامة والمصدر، P3 السرية والتحكم، P4 الصمود والدليل؛ لكل ركيزة مقابل في بروتوكول الدين.",
               "K = 4/4 = 1 يعبّر عن اكتمال البروتوكول المعلن، لا عن اكتمال العالم."),
    },
}

T: Dict[str, Dict[str, Any]] = {
    "fr": {
        "lang": "fr", "dir": "ltr", "locale": "fr_FR",
        "titre": "Règlement des dettes et redistribution — justice, paix, abondance, continuité",
        "og_titre": "Règlement des dettes et redistribution : 13 équations posées et contrôlées",
        "description": "Treize équations pour le règlement des dettes, la zakat, le qard hasan, la succession et la redistribution, avec contrôles exacts et limites honnêtes.",
        "nav": ("Accueil", "L'Œuvre", "Observateur Triniter", "Portefeuille", "Développeurs"),
        "pied": "© 2026 {auteur} — AL-MIZAN.WORLD · Règles déclarées, calculs reproductibles · GPL-3.0 / AGPL-3.0",
        "h1": "Règlement des dettes et redistribution : les règles, posées puis calculées",
        "lead": "De la règle coranique au calcul : report de l'insolvable, remise, prêt sans intérêt, zakat, parts successorales, flux et indice de justice — avec les limites explicites.",
        "badge_calc": "13 équations",
        "badge_ctrl": "{ok}/{total} contrôles",
        "badge_hon": "0 transfert de fonds",
        "badge_src": "Corpus : versets cités",
        "warn_titre": "Périmètre honnête.",
        "warn_corps": "Ce module formalise des règles et calcule des exemples. Il ne perçoit aucune zakat, ne détient aucun fonds et ne contraint personne. Les scénarios agrégés sont des modèles déclarés ; la parabole des sept épis n'est pas un rendement. La « complétude complète » est bornée à la complétude du protocole déclaré.",
        "s_source": "Source normative",
        "p_source": "Coran 2:275-279, 2:280, 2:282, 2:245, 2:261, 9:60, 4:11-12, 5:8, 16:90, 49:10. Les versets sont cités par référence et paraphrasés ; aucune traduction n'est présentée comme officielle. Les constantes de zakat et de nisab sont celles du moteur du dossier.",
        "s_table": "Les treize équations",
        "p_table": "Chaque ligne donne la formule, le résultat calculé, le chemin d'explication (fonction du module → contrôle) et le statut.",
        "th_id": "ID", "th_formule": "Formule", "th_resultat": "Résultat",
        "th_chemin": "Chemin d'explication", "th_statut": "Statut",
        "s_detail": "Cartes d'explication",
        "p_detail": "Chaque carte pose la règle, donne le résultat et explique ce qu'elle dit — et ce qu'elle ne dit pas.",
        "s_figure": "Figure calculée",
        "fig_legende": "À gauche : règlement d'une dette de 1 000 € avec versement de 300 € et remise de 200 € (reste 500 €). À droite : continuité du stock sous zakat, Wₙ/W₀ = 0,975ⁿ, avec la demi-vie à 27,38 ans. Les deux panneaux sont recalculés depuis EQ-03 et EQ-10.",
        "s_resultats": "Résultats",
        "p_resultats": "Valeurs recalculées à chaque génération. Les contrôles échouent si une constante ou une formule dérive.",
        "s_ponts": "Ponts avec les quatre piliers",
        "p_ponts": "Lecture structurelle déclarée SPÉCIFIÉE : chaque pilier reçoit un répondant dans le protocole de dette, avec sa limite explicite.",
        "th_pilier": "Pilier", "th_question": "Question du dossier",
        "th_regle": "Règle de dette", "th_limite": "Limite",
        "ponts_lignes": (
            ("P1 — Identité et mandat", "Qui agit, à quel titre ?",
             "Parties identifiées, mandat écrit, signature (2:282).",
             "Le module ne vérifie pas l'identité réelle."),
            ("P2 — Intégrité et provenance", "Ce qui s'exécute est-il ce qui a été signé ?",
             "Écriture, témoins, empreinte SHA-256.",
             "L'empreinte prouve le contenu, pas les faits."),
            ("P3 — Confidentialité et maîtrise", "Qui peut lire, restaurer, effacer ?",
             "Registre accessible, aucune clé privée détenue.",
             "Aucune garde de fonds."),
            ("P4 — Résilience et preuve", "Que reste-t-il après l'attaque ?",
             "Journal d'audit, quittance, recours, réconciliation (49:10).",
             "Preuve documentaire, pas exécution forcée."),
        ),
        "s_repro": "Comment l'utiliser",
        "p_repro": "Les commandes s'exécutent depuis ASTRO-Q°ODE_SYSTEME/. Le JSON public est servi à l'adresse indiquée ci-dessous.",
        "s_limites": "Limites",
        "limites": (
            "<li>Aucune mesure : le module calcule des règles, il ne mesure ni la pauvreté, ni la paix, ni l'abondance.</li>"
            "<li>Aucun transfert : aucun fonds n'est détenu, perçu ou distribué.</li>"
            "<li>Nisab calibré : les seuils viennent de l'étalonnage du dossier, pas des cours réels.</li>"
            "<li>Succession partielle : un cas déclaré, sans awl, radd ni testament.</li>"
            "<li>Modèles agrégés : capacité, stabilisateur et Gini sont des modèles-jouets à hypothèses explicites.</li>"
            "<li>Parabole : le facteur 700 n'est pas un rendement.</li>"
            "<li>Indice : J = 1−T est une convention interne, pas une mesure de justice.</li>"
            "<li>Complétude : K = 1 ne vaut que pour le protocole déclaré.</li>"
            "<li>Aucune autorité : le module ne remplace ni un juge, ni un savant, ni une institution de zakat.</li>"
        ),
        "actions_json": "Résultats JSON",
        "actions_oeuvre": "L'Œuvre universelle",
        "note_langue": "Version française. Les versions anglaise et arabe reprennent les mêmes équations et les mêmes chiffres.",
        "statuts": {"OPÉRATIONNEL": "OPÉRATIONNEL", "SIMULÉ": "SIMULÉ", "SPÉCIFIÉ": "SPÉCIFIÉ"},
        "src_ligne": "Source : Coran, versets cités ; moteur d'économie islamique du dossier pour les constantes.",
        "resume_lignes": (
            ("Équations", "equations"), ("Contrôles", "controles"),
            ("Zakat (1 000 €)", "zakat"), ("Nisab argent", "nisab"),
            ("Qard vs riba (10 ans)", "qard"), ("Succession (Σ · fils · fille)", "succession"),
            ("Demi-vie zakat (ans)", "demi_vie"), ("Gini (0 → 50)", "gini"),
            ("Indice usuraire", "indice"), ("Complétude", "completude"),
        ),
    },
    "en": {
        "lang": "en", "dir": "ltr", "locale": "en_GB",
        "titre": "Debt settlement and redistribution — justice, peace, abundance, continuity",
        "og_titre": "Debt settlement and redistribution: 13 equations, posed and checked",
        "description": "Thirteen equations for debt settlement, zakat, qard hasan, inheritance and redistribution, with exact checks and honest limits.",
        "nav": ("Home", "The Work", "Triniter Observer", "Portfolio", "Developers"),
        "pied": "© 2026 {auteur} — AL-MIZAN.WORLD · Declared rules, reproducible calculations · GPL-3.0 / AGPL-3.0",
        "h1": "Debt settlement and redistribution: the rules, posed and then computed",
        "lead": "From the Quranic rule to the computation: respite for the insolvent, forgiveness, interest-free lending, zakat, inheritance shares, flow and a justice index — with explicit limits.",
        "badge_calc": "13 equations",
        "badge_ctrl": "{ok}/{total} checks",
        "badge_hon": "0 fund transfer",
        "badge_src": "Corpus: cited verses",
        "warn_titre": "Honest scope.",
        "warn_corps": "This module formalises rules and computes examples. It collects no zakat, holds no funds and coerces no one. Aggregate scenarios are declared models; the parable of the seven spikes is not a return. “Complete completeness” is bounded by the completeness of the declared protocol.",
        "s_source": "Normative source",
        "p_source": "Quran 2:275-279, 2:280, 2:282, 2:245, 2:261, 9:60, 4:11-12, 5:8, 16:90, 49:10. Verses are cited by reference and paraphrased; no translation is presented as official. Zakat and nisab constants come from the project engine.",
        "s_table": "The thirteen equations",
        "p_table": "Each row gives the formula, the computed result, the explanation path (module function → check) and the status.",
        "th_id": "ID", "th_formule": "Formula", "th_resultat": "Result",
        "th_chemin": "Explanation path", "th_statut": "Status",
        "s_detail": "Explanation cards",
        "p_detail": "Each card states the rule, gives the result and explains what it says — and what it does not say.",
        "s_figure": "Computed figure",
        "fig_legende": "Left: settling a 1,000 € debt with 300 € paid and 200 € forgiven (500 € remaining). Right: continuity of the stock under zakat, Wₙ/W₀ = 0.975ⁿ, with the half-life at 27.38 years. Both panels are recomputed from EQ-03 and EQ-10.",
        "s_resultats": "Results",
        "p_resultats": "Values are recomputed at each generation. Checks fail if a constant or a formula drifts.",
        "s_ponts": "Bridges to the four pillars",
        "p_ponts": "A structural reading declared SPECIFIED: each pillar receives a counterpart in the debt protocol, with its explicit limit.",
        "th_pilier": "Pillar", "th_question": "Project question",
        "th_regle": "Debt rule", "th_limite": "Limit",
        "ponts_lignes": (
            ("P1 — Identity and mandate", "Who acts, in what capacity?",
             "Identified parties, written mandate, signature (2:282).",
             "The module does not verify real identity."),
            ("P2 — Integrity and provenance", "Is what runs what was signed?",
             "Written record, witnesses, SHA-256 fingerprint.",
             "The fingerprint proves the content, not the facts."),
            ("P3 — Confidentiality and control", "Who can read, restore, erase?",
             "Accessible register, no private key held.",
             "No custody of funds."),
            ("P4 — Resilience and proof", "What remains after the attack?",
             "Audit log, receipt, recourse, reconciliation (49:10).",
             "Documentary proof, not enforcement."),
        ),
        "s_repro": "How to use it",
        "p_repro": "Commands run from ASTRO-Q°ODE_SYSTEME/. The public JSON is served at the address below.",
        "s_limites": "Limits",
        "limites": (
            "<li>No measurement: the module computes rules; it measures neither poverty, nor peace, nor abundance.</li>"
            "<li>No transfer: no funds are held, collected or distributed.</li>"
            "<li>Calibrated nisab: thresholds come from the project calibration, not live prices.</li>"
            "<li>Partial inheritance: one declared case, without awl, radd or wills.</li>"
            "<li>Aggregate models: capacity, stabiliser and Gini are toy models with explicit assumptions.</li>"
            "<li>Parable: the factor 700 is not a return.</li>"
            "<li>Index: J = 1−T is an internal convention, not a measure of justice.</li>"
            "<li>Completeness: K = 1 holds only for the declared protocol.</li>"
            "<li>No authority: the module replaces neither a judge, nor a scholar, nor a zakat institution.</li>"
        ),
        "actions_json": "JSON results",
        "actions_oeuvre": "The Universal Work",
        "note_langue": "English version. The French and Arabic versions carry the same equations and the same figures.",
        "statuts": {"OPÉRATIONNEL": "OPERATIONAL", "SIMULÉ": "SIMULATED", "SPÉCIFIÉ": "SPECIFIED"},
        "src_ligne": "Source: Quran, cited verses; the project's Islamic economy engine for the constants.",
        "resume_lignes": (
            ("Equations", "equations"), ("Checks", "controles"),
            ("Zakat (1,000 €)", "zakat"), ("Silver nisab", "nisab"),
            ("Qard vs riba (10 years)", "qard"), ("Inheritance (Σ · son · daughter)", "succession"),
            ("Zakat half-life (years)", "demi_vie"), ("Gini (0 → 50)", "gini"),
            ("Usurious index", "indice"), ("Completeness", "completude"),
        ),
    },
    "ar": {
        "lang": "ar", "dir": "rtl", "locale": "ar_SA",
        "titre": "تسوية الديون وإعادة التوزيع — العدل والسلام والوفرة والاستمرارية",
        "og_titre": "تسوية الديون وإعادة التوزيع: ثلاث عشرة معادلة موضوعة ومتحقَّق منها",
        "description": "ثلاث عشرة معادلة لتسوية الديون والزكاة والقرض الحسن والميراث وإعادة التوزيع، مع تحققات دقيقة وحدود صادقة.",
        "nav": ("الرئيسية", "العمل الكوني", "المراقب الثلاثي", "المحفظة", "المطورون"),
        "pied": "© 2026 {auteur} — AL-MIZAN.WORLD · قواعد معلنة وحسابات قابلة للتكرار · GPL-3.0 / AGPL-3.0",
        "h1": "تسوية الديون وإعادة التوزيع: القواعد موضوعة ثم محسوبة",
        "lead": "من القاعدة القرآنية إلى الحساب: إنظار المعسر، والإبراء، والقرض بلا فائدة، والزكاة، والأنصبة، والتدفق، ومؤشر العدل — مع حدود صريحة.",
        "badge_calc": "13 معادلة",
        "badge_ctrl": "{ok}/{total} تحققًا",
        "badge_hon": "لا تحويل أموال",
        "badge_src": "المصدر: آيات مشار إليها",
        "warn_titre": "نطاق صادق.",
        "warn_corps": "هذه الوحدة تصوغ قواعد وتحسب أمثلة. لا تجمع زكاة، ولا تحتفظ بأموال، ولا تُلزم أحدًا. السيناريوهات المجمّعة نماذج معلنة؛ ومثل السبعة سنابل ليس عائدًا. «الاكتمال الكامل» محدود باكتمال البروتوكول المعلن.",
        "s_source": "المصدر المعياري",
        "p_source": "البقرة 2:275-279، 2:280، 2:282، 2:245، 2:261؛ التوبة 9:60؛ النساء 4:11-12؛ المائدة 5:8؛ النحل 16:90؛ الحجرات 49:10. تُذكر الآيات بالإحالة والمعنى، ولا تُقدَّم أي ترجمة كرسمية. ثوابت الزكاة والنصاب من محرك المشروع.",
        "s_table": "المعادلات الثلاث عشرة",
        "p_table": "كل سطر يعطي الصيغة والنتيجة المحسوبة ومسار الشرح (دالة الوحدة ← التحقق) والحالة.",
        "th_id": "المعرف", "th_formule": "الصيغة", "th_resultat": "النتيجة",
        "th_chemin": "مسار الشرح", "th_statut": "الحالة",
        "s_detail": "بطاقات الشرح",
        "p_detail": "كل بطاقة تضع القاعدة وتعطي النتيجة وتشرح ما تقوله وما لا تقوله.",
        "s_figure": "رسم محسوب",
        "fig_legende": "يسارًا: تسوية دين قدره 1000 € بدفع 300 € وإبراء 200 € (الباقي 500 €). يمينًا: استمرارية المخزون تحت الزكاة، Wₙ/W₀ = 0.975ⁿ، ونصف العمر عند 27.38 سنة. يُعاد حساب اللوحتين من EQ-03 وEQ-10.",
        "s_resultats": "النتائج",
        "p_resultats": "تُعاد القيم في كل توليد. تفشل التحققات إذا انحرفت ثابتة أو صيغة.",
        "s_ponts": "جسور مع الركائز الأربع",
        "p_ponts": "قراءة بنيوية محددة: كل ركيزة لها مقابل في بروتوكول الدين، مع حدّها الصريح.",
        "th_pilier": "الركيزة", "th_question": "سؤال الملف",
        "th_regle": "قاعدة الدين", "th_limite": "الحد",
        "ponts_lignes": (
            ("P1 — الهوية والتفويض", "من يتصرف وبأي صفة؟",
             "أطراف معروفة، وتفويض مكتوب، وتوقيع (2:282).",
             "الوحدة لا تتحقق من الهوية الحقيقية."),
            ("P2 — السلامة والمصدر", "هل ما يُنفَّذ هو ما وُقِّع؟",
             "كتابة وشهود وبصمة SHA-256.",
             "البصمة تثبت المحتوى لا الوقائع."),
            ("P3 — السرية والتحكم", "من يقرأ ويستعيد ويمحو؟",
             "سجل متاح، ولا مفاتيح خاصة محتجزة.",
             "لا حفظ لأموال."),
            ("P4 — الصمود والدليل", "ماذا يبقى بعد الهجوم؟",
             "سجل تدقيق، وإيصال، وسبيل مراجعة، ومصالحة (49:10).",
             "دليل وثائقي لا تنفيذ قسري."),
        ),
        "s_repro": "كيفية الاستخدام",
        "p_repro": "تُنفَّذ الأوامر من ASTRO-Q°ODE_SYSTEME/. يُقدَّم JSON العام على العنوان أدناه.",
        "s_limites": "الحدود",
        "limites": (
            "<li>لا قياس: الوحدة تحسب قواعد ولا تقيس الفقر ولا السلام ولا الوفرة.</li>"
            "<li>لا تحويل: لا تُحتفظ بأموال ولا تُجمع ولا تُوزع.</li>"
            "<li>نصاب معاير: العتبات من معايرة المشروع لا من الأسعار اللحظية.</li>"
            "<li>ميراث جزئي: حالة معلنة واحدة، دون عول أو رد أو وصية.</li>"
            "<li>نماذج مجمّعة: القدرة والمثبِّت وجيني نماذج لعبة بفرضيات صريحة.</li>"
            "<li>مثل: العامل 700 ليس عائدًا.</li>"
            "<li>مؤشر: J = 1−T اصطلاح داخلي وليس قياسًا للعدل.</li>"
            "<li>اكتمال: K = 1 لا يصح إلا للبروتوكول المعلن.</li>"
            "<li>لا سلطة: الوحدة لا تحل محل قاضٍ ولا عالم ولا مؤسسة زكاة.</li>"
        ),
        "actions_json": "نتائج JSON",
        "actions_oeuvre": "العمل الكوني",
        "note_langue": "النسخة العربية. تحمل النسختان الفرنسية والإنجليزية نفس المعادلات ونفس الأرقام.",
        "statuts": {"OPÉRATIONNEL": "تشغيلي", "SIMULÉ": "محاكى", "SPÉCIFIÉ": "محدد"},
        "src_ligne": "المصدر: القرآن، الآيات المذكورة؛ ومحرك الاقتصاد الإسلامي في المشروع للثوابت.",
        "resume_lignes": (
            ("المعادلات", "equations"), ("التحققات", "controles"),
            ("الزكاة (1000 €)", "zakat"), ("نصاب الفضة", "nisab"),
            ("القرض مقابل الربا (10 سنوات)", "qard"), ("الميراث (Σ · ابن · بنت)", "succession"),
            ("نصف عمر الزكاة (سنة)", "demi_vie"), ("جيني (0 → 50)", "gini"),
            ("المؤشر الربوي", "indice"), ("الاكتمال", "completude"),
        ),
    },
}

CSS = """
:root{--encre:#10263a;--bleu:#1f5f8b;--pale:#f5f7fa;--or:#b45309;--gris:#5b6b7a;}
*{box-sizing:border-box}
body{margin:0;font-family:Georgia,'Times New Roman',serif;color:var(--encre);
     background:#fbfcfd;line-height:1.62;font-size:17px}
html[dir="rtl"] body{font-family:'Segoe UI',Tahoma,'Traditional Arabic',Arial,sans-serif}
header.site{background:#0f2438;color:#eef4f9;padding:14px 22px;display:flex;flex-wrap:wrap;
     gap:14px;align-items:center;justify-content:space-between;font-family:'Segoe UI',Arial,sans-serif}
header.site a{color:#dce9f4;text-decoration:none;margin-left:16px;font-size:14px}
header.site .marque{font-weight:700;letter-spacing:.06em;font-size:15px}
header.site nav .langues{margin-left:14px;padding-left:12px;border-left:1px solid #34506a}
header.site nav .langues a{margin-left:6px;padding:2px 7px;border:1px solid #34506a;border-radius:5px;font-size:12.5px}
header.site nav .langues a.on{background:#dce9f4;color:#0f2438;border-color:#dce9f4;font-weight:700}
html[dir="rtl"] header.site nav .langues{margin-left:0;padding-left:0;border-left:0;margin-right:14px;
     padding-right:12px;border-right:1px solid #34506a}
html[dir="rtl"] .formule,html[dir="rtl"] table,html[dir="rtl"] pre,html[dir="rtl"] code{direction:ltr;text-align:left}
main{max-width:1120px;margin:0 auto;padding:30px 22px 60px}
h1{font-size:32px;line-height:1.2;margin:10px 0 6px}
h2{font-size:23px;margin-top:44px;border-bottom:1px solid #d7e0e8;padding-bottom:6px}
h3{font-size:18px;margin:0 0 6px}
p.lead{font-size:19px;color:#33475a}
.badges{margin:14px 0 6px}
.badges span{display:inline-block;font-family:'Segoe UI',Arial,sans-serif;font-size:12.5px;
     margin:0 8px 8px 0;padding:4px 10px;border-radius:20px;border:1px solid #cfdbe6;
     background:#eef4f9;color:#1f5f8b}
.badges .or{background:#fdf3e7;border-color:#ecc79a;color:#8a4b06}
.avertissement{margin:18px 0;padding:14px 16px;border-left:4px solid var(--or);
     background:#fdf8f2;font-size:15.5px;color:#4a3a28}
html[dir="rtl"] .avertissement{border-left:0;border-right:4px solid var(--or)}
.tableau{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14.5px;margin:14px 0}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid #e2e9ef;vertical-align:top}
html[dir="rtl"] th,html[dir="rtl"] td{text-align:right}
th{font-family:'Segoe UI',Arial,sans-serif;font-size:12.5px;text-transform:uppercase;
   letter-spacing:.05em;color:#5b6b7a;background:#f5f7fa}
tbody tr:hover{background:#f8fbfd}
td.id{white-space:nowrap;font-weight:700;color:#0f3d5c}
.formule{display:block;font-family:Consolas,monospace;font-size:13.5px;color:#1f4e6b;background:#f4f8fb;
     padding:10px 12px;border-radius:6px;overflow-x:auto}
.chemin{font-family:Consolas,monospace;font-size:12px;color:#5b6b7a;white-space:nowrap}
.grille{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:18px}
.carte{border:1px solid #dde6ed;border-radius:10px;padding:16px 18px;background:#fff}
.carte .entete{display:flex;justify-content:space-between;align-items:center;
     font-family:'Segoe UI',Arial,sans-serif;font-size:12.5px;color:#5b6b7a;margin-bottom:8px}
.carte .pose{font-size:15px;color:#33475a;margin:0 0 10px}
.carte .res{font-size:15px;margin:10px 0 0;padding:8px 10px;background:#f4f8fb;border-radius:6px}
.carte .lecture{font-size:15px;color:#3c4f61;margin:10px 0 0}
.carte .voie{font-family:Consolas,monospace;font-size:12px;color:#5b6b7a;margin-top:10px}
.statut{display:inline-block;font-family:'Segoe UI',Arial,sans-serif;font-size:11.5px;
     padding:2px 9px;border-radius:20px;border:1px solid #cfdbe6;background:#eef4f9;color:#1f5f8b}
.statut.o{background:#eaf6ef;border-color:#bfe0cb;color:#1e6b3a}
.statut.s{background:#fdf3e7;border-color:#ecc79a;color:#8a4b06}
.statut.p{background:#f0eefc;border-color:#cfc6f2;color:#4b3a9a}
figure{margin:20px 0;padding:10px;border:1px solid #dde6ed;border-radius:10px;background:#fff}
figure svg{width:100%;height:auto;display:block}
figcaption{font-size:14px;color:#5b6b7a;margin-top:8px}
.encadre{margin:18px 0;padding:14px 16px;border-left:4px solid var(--bleu);background:#f4f8fb}
html[dir="rtl"] .encadre{border-left:0;border-right:4px solid var(--bleu)}
ul{margin:10px 0 0;padding-left:20px}
html[dir="rtl"] ul{padding-left:0;padding-right:20px}
li{margin:6px 0}
pre{background:#f6f8fa;border:1px solid #d7e0e8;border-radius:8px;padding:14px;overflow-x:auto;font-size:13.5px}
.actions{margin-top:26px;display:flex;flex-wrap:wrap;gap:10px}
.actions a{font-family:'Segoe UI',Arial,sans-serif;font-size:14px;text-decoration:none;
     padding:9px 16px;border-radius:8px;border:1px solid #1f5f8b;color:#1f5f8b}
.actions a.principal{background:#1f5f8b;color:#fff}
.note-langue{font-size:13.5px;color:#5b6b7a;margin-top:10px}
footer.site{background:#0f2438;color:#c9d9e6;padding:18px 22px;font-size:13.5px;
     font-family:'Segoe UI',Arial,sans-serif;text-align:center}
footer.site a{color:#dce9f4}
@media (max-width:900px){.grille{grid-template-columns:1fr}}
"""


def _nav(lang: str) -> str:
    t = T[lang]
    liens = (
        ("/", t["nav"][0]),
        ("/oeuvre-universelle", t["nav"][1]),
        ("/observateur-triniter", t["nav"][2]),
        ("/portefeuille", t["nav"][3]),
        ("/developpeurs", t["nav"][4]),
    )
    corps = "".join(f"<a href='{h}'>{_ech(libelle)}</a>" for h, libelle in liens)
    langues = "".join(
        f"<a class='langue{' on' if code == lang else ''}' href='{CHEMINS[code]}' "
        f"hreflang='{code}' lang='{code}'>{libelle}</a>"
        for code, libelle in (("fr", "FR"), ("en", "EN"), ("ar", "العربية"))
    )
    return (
        "<header class='site'><div class='marque'>AL-MIZAN.WORLD</div><nav>"
        f"{corps}<span class='langues'>{langues}</span></nav></header>"
    )


def _pied(lang: str) -> str:
    return f"<footer class='site'>{T[lang]['pied'].format(auteur=_ech(AUTEUR))}</footer>"


def _classe_statut(statut: str) -> str:
    return {"OPÉRATIONNEL": "o", "SIMULÉ": "s", "SPÉCIFIÉ": "p"}.get(statut, "")


def _table(donnees: Dict[str, Any], lang: str) -> str:
    t = T[lang]
    lignes = []
    for eq in donnees["equations"]:
        statut = t["statuts"][eq["statut"]]
        lignes.append(
            "<tr class='equation'>"
            f"<td class='id'><a href='#{eq['id'].lower()}'>{eq['id']}</a></td>"
            f"<td><span class='formule'>{_ech(eq['formule'])}</span></td>"
            f"<td>{_ech(eq['resultat'])}</td>"
            f"<td><span class='chemin'>{_ech(eq['chemin'])}</span></td>"
            f"<td><span class='statut {_classe_statut(eq['statut'])}'>{_ech(statut)}</span></td>"
            "</tr>"
        )
    return (
        "<div class='tableau'><table><thead><tr>"
        f"<th>{t['th_id']}</th><th>{t['th_formule']}</th><th>{t['th_resultat']}</th>"
        f"<th>{t['th_chemin']}</th><th>{t['th_statut']}</th>"
        "</tr></thead><tbody>" + "".join(lignes) + "</tbody></table></div>"
    )


def _cartes(donnees: Dict[str, Any], lang: str) -> str:
    blocs = []
    for eq in donnees["equations"]:
        titre, pose, lecture = EQ_TEXT[eq["id"]][lang]
        statut = T[lang]["statuts"][eq["statut"]]
        blocs.append(
            f"<article class='carte' id='{eq['id'].lower()}'>"
            f"<div class='entete'><span class='id'>{eq['id']}</span>"
            f"<span class='statut {_classe_statut(eq['statut'])}'>{_ech(statut)}</span></div>"
            f"<h3>{_ech(titre)}</h3>"
            f"<p class='pose'>{_ech(pose)}</p>"
            f"<div class='formule'>{_ech(eq['formule'])}</div>"
            f"<p class='res'><strong>{T[lang]['th_resultat']} :</strong> {_ech(eq['resultat'])}</p>"
            f"<p class='lecture'>{_ech(lecture)}</p>"
            f"<p class='voie'>{_ech(eq['chemin'])}</p>"
            "</article>"
        )
    return "<div class='grille'>" + "".join(blocs) + "</div>"


def _resultats(donnees: Dict[str, Any], lang: str) -> str:
    t = T[lang]
    zakat = _carte(donnees, "EQ-01")
    qard = _carte(donnees, "EQ-04")
    succession = _carte(donnees, "EQ-06")
    continuite = _carte(donnees, "EQ-10")
    inegalite = _carte(donnees, "EQ-08")
    justice = _carte(donnees, "EQ-12")
    valeurs = {
        "equations": str(donnees["resume"]["equations"]),
        "controles": f"{donnees['resume']['controles_ok']}/{donnees['resume']['controles_total']}",
        "zakat": _c(zakat["zakat_eur"]),
        "nisab": _c(zakat["nisab_argent_eur"]),
        "qard": _c(qard["surcout_riba_eur"]),
        "succession": f"{succession['somme_parts']} · {_c(succession['montants_eur']['fils'], 0)} · {_c(succession['montants_eur']['fille'], 0)}",
        "demi_vie": _c(continuite["demi_vie_ans"]),
        "gini": f"{_c(inegalite['gini_initial'])} → {_c(inegalite['scenarios'][0]['gini_apres'])} → {_c(inegalite['scenarios'][1]['gini_apres'])}",
        "indice": f"{_c(justice['scenarios']['usuraire']['tension_economique'])} / {_c(justice['scenarios']['usuraire']['indice_harmonie_economique'])}",
        "completude": f"4/4 · {_c(1.0)}",
    }
    lignes = "".join(
        f"<tr><td>{_ech(libelle)}</td><td>{_ech(valeurs[cle])}</td></tr>"
        for libelle, cle in t["resume_lignes"]
    )
    return (
        "<div class='tableau'><table><tbody>" + lignes + "</tbody></table></div>"
        f"<p class='note-langue'>{_ech(t['p_resultats'])}</p>"
        f"<p class='note-langue'>{_ech(t['src_ligne'])}</p>"
    )


def _ponts(lang: str) -> str:
    t = T[lang]
    lignes = []
    for pilier, question, regle, limite in t["ponts_lignes"]:
        lignes.append(
            "<tr>"
            f"<td><strong>{_ech(pilier)}</strong></td>"
            f"<td>{_ech(question)}</td>"
            f"<td>{_ech(regle)}</td>"
            f"<td>{_ech(limite)}</td>"
            "</tr>"
        )
    return (
        "<div class='tableau'><table><thead><tr>"
        f"<th>{t['th_pilier']}</th><th>{t['th_question']}</th>"
        f"<th>{t['th_regle']}</th><th>{t['th_limite']}</th>"
        "</tr></thead><tbody>" + "".join(lignes) + "</tbody></table></div>"
    )


def _corps(donnees: Dict[str, Any], svg: str, lang: str) -> str:
    t = T[lang]
    resume = donnees["resume"]
    valeurs = {"ok": resume["controles_ok"], "total": resume["controles_total"]}
    return f"""
<h1>{t['h1']}</h1>
<p class="lead">{t['lead']}</p>
<div class="badges">
  <span>{t['badge_calc']}</span>
  <span>{t['badge_ctrl'].format(**valeurs)}</span>
  <span class="or">{t['badge_hon']}</span>
  <span>{t['badge_src']}</span>
</div>

<div class="avertissement">
  <strong>{t['warn_titre']}</strong> {t['warn_corps']}
</div>

<h2 id="source">{t['s_source']}</h2>
<p>{t['p_source']}</p>

<h2 id="table">{t['s_table']}</h2>
<p>{t['p_table']}</p>
{_table(donnees, lang)}

<h2 id="detail">{t['s_detail']}</h2>
<p>{t['p_detail']}</p>
{_cartes(donnees, lang)}

<h2 id="figure">{t['s_figure']}</h2>
<figure>{svg}<figcaption>{t['fig_legende'].format(**valeurs)}</figcaption></figure>

<h2 id="resultats">{t['s_resultats']}</h2>
{_resultats(donnees, lang)}

<h2 id="ponts">{t['s_ponts']}</h2>
<p>{t['p_ponts']}</p>
{_ponts(lang)}

<h2 id="reproductibilite">{t['s_repro']}</h2>
<pre>py -3 oeuvre_universelle/reglement_dettes_redistribution.py
py -3 -m unittest tests.test_reglement_dettes_redistribution -v
py -3 oeuvre_universelle/generer_page_reglement_dettes_redistribution.py</pre>
<p>{t['p_repro']}</p>

<h2 id="limites">{t['s_limites']}</h2>
<ul>{t['limites']}</ul>

<div class="actions">
  <a class="principal" href="/reglement-dettes-redistribution.json">{t['actions_json']}</a>
  <a href="/oeuvre-universelle">{t['actions_oeuvre']}</a>
</div>
<p class="note-langue">{t['note_langue']}</p>
"""


def _html(donnees: Dict[str, Any], svg: str, lang: str) -> str:
    t = T[lang]
    alternates = "".join(
        f"<link rel='alternate' hreflang='{code}' href='{SITE}{CHEMINS[code]}'>\n"
        for code in LANGUES
    )
    return f"""<!DOCTYPE html>
<html lang="{t['lang']}" dir="{t['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t['titre']}</title>
<meta name="description" content="{_ech(t['description'])}">
<link rel="canonical" href="{SITE}{CHEMINS[lang]}">
{alternates}<link rel="alternate" hreflang="x-default" href="{SITE}/reglement-dettes-redistribution">
<meta property="og:title" content="{_ech(t['og_titre'])}">
<meta property="og:description" content="{_ech(t['description'])}">
<meta property="og:type" content="article">
<meta property="og:locale" content="{t['locale']}">
<style>{CSS}</style>
</head>
<body>
{_nav(lang)}
<main>
{_corps(donnees, svg, lang)}
</main>
{_pied(lang)}
</body>
</html>
"""


def generer() -> Dict[str, Any]:
    donnees = resoudre()
    if not verifier(donnees):
        echoues = [c["id"] for c in donnees["controles"] if not c["ok"]]
        raise RuntimeError(f"Contrôles numériques en échec : {echoues}")

    WEB_CLOUD.mkdir(parents=True, exist_ok=True)
    RESULTATS.mkdir(parents=True, exist_ok=True)
    for lang in LANGUES:
        PAGES[lang].write_text(
            _html(donnees, _figure(donnees, lang), lang),
            encoding="utf-8",
            newline="\n",
        )
    charge = json.dumps(donnees, ensure_ascii=False, indent=2, default=str)
    DONNEES_JSON.write_text(charge, encoding="utf-8", newline="\n")
    ARCHIVE_JSON.write_text(charge, encoding="utf-8", newline="\n")
    return {
        "pages": {
            lang: {"chemin": str(PAGES[lang]), "octets": PAGES[lang].stat().st_size}
            for lang in LANGUES
        },
        "json": str(DONNEES_JSON),
        "controles": f"{donnees['resume']['controles_ok']}/{donnees['resume']['controles_total']}",
        "equations": len(donnees["equations"]),
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(generer(), ensure_ascii=False, indent=2))
