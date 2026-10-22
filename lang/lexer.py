# -*- coding: utf-8 -*-
"""
Analyseur Lexical (Lexer) du Langage ASTRO-Q°ODE (V1.0 & V2.0)
==============================================================
Transforme tout script `.aq` ou fichier de spécification (comme `astro_q°ode_specification.txt`)
en un flux de `Token` typés.
Supporte nativement :
- Les suffixes d'unités `i` (Kelvin) et `I` (Joules) après les nombres (`-9 i`, `+5 I`, `8766 i`).
- Les identifiants `omega_*` (Niveau 4 Mecquois) et `alpha_*` (Niveau 3 Médinois).
- L'opérateur de transcription monadique `>>=`, le modificateur de force `??`,
  l'inversion culturelle `¿`, l'isolation absolue `(( ... ))` et l'Origine `0 : HÉLIUM`.
- Les symboles Unicode (`∪`, `⊃`, `⊂`, `∖`, `∩`, `⊘`, `≡`, `≢`, `‰`, `×`, `÷`, `≠`)
  ainsi que leurs alias ASCII (`U`, `UNION`, `INCL`, `STRICT`, `DIFF`, `INTER`, `HDIV`).
"""

from __future__ import annotations

from typing import List, Optional

from .tokens import Token, TokenType


class ErreurLexicaleAstroQode(Exception):
    """Levée lorsqu'un caractère ou une séquence invalide est rencontré par le Lexer."""

    def __init__(self, message: str, ligne: int, colonne: int) -> None:
        super().__init__(f"[Erreur Lexicale L{ligne}:C{colonne}] {message}")
        self.ligne = ligne
        self.colonne = colonne


class LexerAstroQode:
    """Analyseur lexical complet pour ASTRO-Q°ODE V1.0 et V2.0."""

    MOTS_CLES_BLOCS_SPEC = {
        "TYPES",
        "PROPRIÉTÉS",
        "PROPRIETES",
        "OPERATEURS_NIVEAU_3",
        "OPERATEURS_NIVEAU_4",
    }

    MOTS_CLES_META_SPEC = {
        "MODIFICATEUR_FORCE",
        "CONTENEUR_SANDBOX",
        "INVERSION_CULTURELLE",
    }

    MOTS_CLES = {
        "SET": TokenType.SET,
        "MECQUOIS": TokenType.MECQUOIS,
        "MEDINOIS": TokenType.MEDINOIS,
        "Monad": TokenType.MONAD,
        "MONAD": TokenType.MONAD,
        "lambda": TokenType.LAMBDA,
        "LAMBDA": TokenType.LAMBDA,
        "return": TokenType.RETURN,
        "RETURN": TokenType.RETURN,
        "HÉLIUM": TokenType.HELIUM,
        "HELIUM": TokenType.HELIUM,
        "Forme": TokenType.FORME,
        "FORME": TokenType.FORME,
        "afficher": TokenType.AFFICHER,
        "print": TokenType.AFFICHER,
        "fusion_pp": TokenType.FUSION,
        "clamp_mizan": TokenType.CLAMP_MIZAN,
        "sphere_holographique": TokenType.SPHERE_HOLO,
        "triade_ibit": TokenType.TRIADE_IBIT,
        "cycle_15_phases": TokenType.CYCLE_15,
        "tir_scpi_5025": TokenType.TIR_SCPI,
        "capteur_cryo_5026": TokenType.CAPTEUR_CRYO,
        "executer_qasm_5030": TokenType.EXEC_QASM,
        "sceller_sha256": TokenType.SCELLER_SHA256,
        "matrice_unisson": TokenType.MATRICE_UNISSON,
        "valeur_or": TokenType.VALEUR_OR,
        "valeur_argent": TokenType.VALEUR_ARGENT,
        # Alias d'opérateurs en toutes lettres ou ASCII
        "AND": TokenType.ET_LOGIQUE,
        "OR": TokenType.OU_LOGIQUE,
        "NOT": TokenType.NON_LOGIQUE,
        "NAND": TokenType.NAND_LOGIQUE,
        "XOR": TokenType.XOR_LOGIQUE,
        "U": TokenType.UNION,
        "UNION": TokenType.UNION,
        "INCL": TokenType.INCLUSION_LARGE,
        "STRICT": TokenType.INCLUSION_STRICTE,
        "DIFF": TokenType.DIFFERENCE_ENS,
        "INTER": TokenType.INTERSECTION,
        "HDIV": TokenType.DIV_HARMONIQUE,
        "CONGR": TokenType.CONGRUENCE,
        "NCONGR": TokenType.NON_CONGRUENCE,
        "PERMILLE": TokenType.POUR_MILLE,
        "OPLUS": TokenType.OPLUS_KRONECKER,
        "OTIMES": TokenType.OTIMES_KRONECKER,
    }

    SYMBOLES_SIMPLES_UNICODE = {
        "⊕": TokenType.OPLUS_KRONECKER,
        "⊗": TokenType.OTIMES_KRONECKER,
        "∪": TokenType.UNION,
        "∖": TokenType.DIFFERENCE_ENS,
        "∩": TokenType.INTERSECTION,
        "⊘": TokenType.DIV_HARMONIQUE,
        "≡": TokenType.CONGRUENCE,
        "≢": TokenType.NON_CONGRUENCE,
        "⊃": TokenType.INCLUSION_LARGE,
        "⊂": TokenType.INCLUSION_STRICTE,
        "‰": TokenType.POUR_MILLE,
        "×": TokenType.FOIS,
        "÷": TokenType.DIV,
        "≠": TokenType.DIFF_LOGIQUE,
        "¿": TokenType.INVERSION_CATCH,
        "¡": TokenType.INVERSION_EXCLAM,
        "°": TokenType.DEGRE_QODE,
        "«": TokenType.GUILLEMET_FR_G,
        "»": TokenType.GUILLEMET_FR_D,
        "{": TokenType.ACCOLADE_G,
        "}": TokenType.ACCOLADE_D,
        "[": TokenType.CROCHET_G,
        "]": TokenType.CROCHET_D,
        ":": TokenType.DEUX_POINTS,
        ";": TokenType.POINT_VIRGULE,
        ",": TokenType.VIRGULE,
        "*": TokenType.FOIS,
        "/": TokenType.DIV,
        "%": TokenType.MODULO,
    }

    def __init__(self, source: str) -> None:
        self.source = source
        self.longueur = len(source)
        self.pos = 0
        self.ligne = 1
        self.colonne = 1
        self.tokens: List[Token] = []

    def _courant(self) -> Optional[str]:
        if self.pos >= self.longueur:
            return None
        return self.source[self.pos]

    def _suivant(self, decalage: int = 1) -> Optional[str]:
        cible = self.pos + decalage
        if cible >= self.longueur:
            return None
        return self.source[cible]

    def _avancer(self, pas: int = 1) -> str:
        extrait = ""
        for _ in range(pas):
            if self.pos < self.longueur:
                ch = self.source[self.pos]
                extrait += ch
                self.pos += 1
                if ch == "\n":
                    self.ligne += 1
                    self.colonne = 1
                else:
                    self.colonne += 1
        return extrait

    def _sauter_espaces_et_commentaires(self) -> None:
        while self.pos < self.longueur:
            ch = self._courant()
            if ch in (" ", "\t", "\r", "\n"):
                self._avancer()
            elif ch == "#":
                while self.pos < self.longueur and self._courant() != "\n":
                    self._avancer()
            else:
                break

    def _peut_etre_signe_unaire_numerique(self) -> bool:
        """
        Détermine si un '+' ou '-' suivi d'un chiffre est le signe d'un littéral numérique
        (ex: `= +5 I`, `alpha_c = -3 i`, `∪ +2 i`, `Monad(+1 I)`) ou un opérateur binaire.
        """
        if not self.tokens:
            return True
        dernier = self.tokens[-1].type
        types_precedant_expression = {
            TokenType.AFFECTATION,
            TokenType.PAREN_G,
            TokenType.DOUBLE_PAREN_G,
            TokenType.ACCOLADE_G,
            TokenType.CROCHET_G,
            TokenType.VIRGULE,
            TokenType.DEUX_POINTS,
            TokenType.RETURN,
            TokenType.UNION,
            TokenType.DIFFERENCE_ENS,
            TokenType.INTERSECTION,
            TokenType.DIV_HARMONIQUE,
            TokenType.CONGRUENCE,
            TokenType.NON_CONGRUENCE,
            TokenType.INCLUSION_LARGE,
            TokenType.INCLUSION_STRICTE,
            TokenType.PLUS,
            TokenType.MOINS,
            TokenType.FOIS,
            TokenType.DIV,
            TokenType.ET_LOGIQUE,
            TokenType.OU_LOGIQUE,
            TokenType.EGAL_LOGIQUE,
            TokenType.DIFF_LOGIQUE,
            TokenType.SUPERIEUR,
            TokenType.INFERIEUR,
            TokenType.BIND_MONADE,
            TokenType.OPLUS_KRONECKER,
            TokenType.OTIMES_KRONECKER,
        }
        return dernier in types_precedant_expression

    def _lire_nombre(self, ligne_debut: int, col_debut: int) -> Token:
        debut = self.pos
        if self._courant() in ("+", "-"):
            self._avancer()
        while self._courant() is not None and self._courant().isdigit():
            self._avancer()
        if self._courant() == "." and self._suivant() is not None and self._suivant().isdigit():
            self._avancer()  # '.'
            while self._courant() is not None and self._courant().isdigit():
                self._avancer()
        return Token(TokenType.NOMBRE, self.source[debut:self.pos], ligne_debut, col_debut)

    def _lire_chaine(self, ligne_debut: int, col_debut: int) -> Token:
        guillemet = self._avancer()
        tampon: List[str] = []
        while self.pos < self.longueur and self._courant() != guillemet:
            ch = self._courant()
            if ch == "\\" and self._suivant() is not None:
                self._avancer()
                tampon.append(self._avancer())
            else:
                tampon.append(self._avancer())
        if self._courant() == guillemet:
            self._avancer()
        else:
            raise ErreurLexicaleAstroQode("Chaîne de caractères non refermée.", ligne_debut, col_debut)
        return Token(TokenType.CHAINE, "".join(tampon), ligne_debut, col_debut)

    def _ignorer_bloc_crochets_specification(self) -> str:
        """Consomme un bloc descriptif `[ ... ]` dans `MECQUOIS` ou `MEDINOIS` (ex: TYPES [...])."""
        while self.pos < self.longueur and self._courant() in (" ", "\t", "\r", "\n"):
            self._avancer()
        if self._courant() != "[":
            return ""
        debut = self.pos
        profondeur = 0
        while self.pos < self.longueur:
            ch = self._courant()
            if ch == "[":
                profondeur += 1
            elif ch == "]":
                profondeur -= 1
                if profondeur == 0:
                    self._avancer()
                    break
            self._avancer()
        return self.source[debut:self.pos]

    def _ignorer_fin_ligne_meta_spec(self) -> str:
        debut = self.pos
        while self.pos < self.longueur and self._courant() != "\n":
            self._avancer()
        return self.source[debut:self.pos].strip()

    def _lire_identifiant_ou_mot_cle(self, ligne_debut: int, col_debut: int) -> Token:
        debut = self.pos
        while self.pos < self.longueur:
            ch = self._courant()
            if ch is not None and (ch.isalnum() or ch in ("_", "É", "È", "Ê", "À", "é", "è", "ê", "à")):
                self._avancer()
            else:
                break
        mot = self.source[debut:self.pos]

        # 1. Blocs déclaratifs de spécification : TYPES [...], PROPRIÉTÉS [...], OPERATEURS_NIVEAU_3/4 [...]
        if mot in self.MOTS_CLES_BLOCS_SPEC:
            contenu = self._ignorer_bloc_crochets_specification()
            return Token(TokenType.SPEC_BLOC, f"{mot} {contenu}".strip(), ligne_debut, col_debut)

        # 2. Métadonnées de spécification : MODIFICATEUR_FORCE : "??"
        if mot in self.MOTS_CLES_META_SPEC:
            reste = self._ignorer_fin_ligne_meta_spec()
            return Token(TokenType.SPEC_META, f"{mot} {reste}".strip(), ligne_debut, col_debut)

        # 3. Unités 'i' (Kelvin) et 'I' (Joules) immédiatement après un NOMBRE
        if mot == "i" and self.tokens and self.tokens[-1].type == TokenType.NOMBRE:
            return Token(TokenType.UNITE_KELVIN, "i", ligne_debut, col_debut)
        if mot == "I" and self.tokens and self.tokens[-1].type == TokenType.NOMBRE:
            return Token(TokenType.UNITE_JOULES, "I", ligne_debut, col_debut)

        # 4. Constantes globales Mecquoises (omega_*) et variables locales Médinoises (alpha_*)
        if mot.startswith("omega_"):
            return Token(TokenType.OMEGA_CONST, mot, ligne_debut, col_debut)
        if mot.startswith("alpha_"):
            return Token(TokenType.ALPHA_VAR, mot, ligne_debut, col_debut)

        # 5. Mots-clés du langage
        if mot in self.MOTS_CLES:
            return Token(self.MOTS_CLES[mot], mot, ligne_debut, col_debut)

        return Token(TokenType.IDENTIFIANT, mot, ligne_debut, col_debut)

    def tokeniser(self) -> List[Token]:
        """Exécute l'analyse lexicale complète et retourne la liste des `Token`."""
        self.tokens.clear()

        while self.pos < self.longueur:
            self._sauter_espaces_et_commentaires()
            if self.pos >= self.longueur:
                break

            ch = self._courant()
            suiv = self._suivant(1)
            suiv2 = self._suivant(2)
            l0, c0 = self.ligne, self.colonne

            # Opérateur 3 caractères : >>=
            if ch == ">" and suiv == ">" and suiv2 == "=":
                self._avancer(3)
                self.tokens.append(Token(TokenType.BIND_MONADE, ">>=", l0, c0))
                continue

            # Opérateurs et délimiteurs 2 caractères
            if ch == "?" and suiv == "?":
                self._avancer(2)
                self.tokens.append(Token(TokenType.FORCE_DOUBLE, "??", l0, c0))
                continue
            if ch == "!" and suiv == "!":
                self._avancer(2)
                self.tokens.append(Token(TokenType.EXCLAM_DOUBLE, "!!", l0, c0))
                continue
            if ch == "!" and suiv == "=":
                self._avancer(2)
                self.tokens.append(Token(TokenType.DIFF_LOGIQUE, "!=", l0, c0))
                continue
            if ch == "=" and suiv == "=":
                self._avancer(2)
                self.tokens.append(Token(TokenType.EGAL_LOGIQUE, "==", l0, c0))
                continue
            if ch == "&" and suiv == "&":
                self._avancer(2)
                self.tokens.append(Token(TokenType.ET_LOGIQUE, "&&", l0, c0))
                continue
            if ch == "|" and suiv == "|":
                self._avancer(2)
                self.tokens.append(Token(TokenType.OU_LOGIQUE, "||", l0, c0))
                continue
            if ch == "(" and suiv == "(":
                # Vérifie si c'est une isolation absolue `(( expr ))` et non `((a ⊃ b) ?? ...)`
                # Astuce : si après `((` on ne trouve pas d'opérateur conditionnel avant `))`,
                # le parser gère aussi bien DOUBLE_PAREN_G que deux PAREN_G imbriquées.
                # On émet PAREN_G unitaire et le Parser détecte les doubles parenthèses `(( ... ))`
                # sans aucune ambiguïté avec `(( cond ) >>= ...)`.
                self._avancer(1)
                self.tokens.append(Token(TokenType.PAREN_G, "(", l0, c0))
                continue

            # Nombres signés (+5, -3) ou non signés (8766, 0)
            if ch.isdigit() or (
                ch in ("+", "-")
                and suiv is not None
                and suiv.isdigit()
                and self._peut_etre_signe_unaire_numerique()
            ):
                self.tokens.append(self._lire_nombre(l0, c0))
                continue

            # Chaînes de caractères
            if ch in ('"', "'"):
                self.tokens.append(self._lire_chaine(l0, c0))
                continue

            # Parenthèses simples
            if ch == "(":
                self._avancer()
                self.tokens.append(Token(TokenType.PAREN_G, "(", l0, c0))
                continue
            if ch == ")":
                self._avancer()
                self.tokens.append(Token(TokenType.PAREN_D, ")", l0, c0))
                continue

            # Opérateurs simples ASCII
            if ch == "+":
                self._avancer()
                self.tokens.append(Token(TokenType.PLUS, "+", l0, c0))
                continue
            if ch == "-":
                self._avancer()
                self.tokens.append(Token(TokenType.MOINS, "-", l0, c0))
                continue
            if ch == "=":
                self._avancer()
                self.tokens.append(Token(TokenType.AFFECTATION, "=", l0, c0))
                continue
            if ch == ">":
                self._avancer()
                self.tokens.append(Token(TokenType.SUPERIEUR, ">", l0, c0))
                continue
            if ch == "<":
                self._avancer()
                self.tokens.append(Token(TokenType.INFERIEUR, "<", l0, c0))
                continue
            if ch == "!":
                self._avancer()
                self.tokens.append(Token(TokenType.NON_LOGIQUE, "!", l0, c0))
                continue

            # Symboles Unicode et ponctuation simple
            if ch in self.SYMBOLES_SIMPLES_UNICODE:
                sym = self._avancer()
                self.tokens.append(Token(self.SYMBOLES_SIMPLES_UNICODE[sym], sym, l0, c0))
                continue

            # Identifiants et mots-clés
            if ch.isalpha() or ch == "_":
                self.tokens.append(self._lire_identifiant_ou_mot_cle(l0, c0))
                continue

            raise ErreurLexicaleAstroQode(f"Caractère non reconnu : {ch!r}", l0, c0)

        self.tokens.append(Token(TokenType.EOF, "", self.ligne, self.colonne))
        return self.tokens
