# -*- coding: utf-8 -*-
"""
Analyseur Syntaxique (Parser) du Langage ASTRO-Q°ODE (V1.0 & V2.0)
==================================================================
Construit un `ProgrammeAstroQode` (AST) à partir de la liste des `Token` produite par `LexerAstroQode`.
Supporte intégralement :
- Les directives d'horloge `SET CLOCK_... = ...`
- Les blocs `MECQUOIS { ... }` et `MEDINOIS { ... }`
- Les blocs déclaratifs de spécification (`TYPES [...]`, `PROPRIÉTÉS [...]`, etc.)
- Les constantes `omega_*` et variables `alpha_*`
- Les littéraux `0 : HÉLIUM`, `-9 i`, `+5 I`, `[dx U dy U dz]`
- Les expressions monadiques `Monad(...)`, `>>=`, `lambda x { ... }`
- Les conteneurs Sandbox `( ... )` et d'isolation monadique absolue `(( ... ))`
- Le modificateur de force `??` et l'inversion culturelle `¿ { ... }`.
"""

from __future__ import annotations

from typing import List, Optional

from .ast_nodes import (
    AffectationLocaleMedinoise,
    BlocMecquois,
    BlocMedinois,
    DeclarationConstanteMecquoise,
    DeclarationSpecification,
    DirectiveHorloge,
    ExpressionAstro,
    ExpressionBinaire,
    ExpressionEnsemble,
    ExpressionForme,
    ExpressionFusionPP,
    ExpressionAppelAlmizan,
    ExpressionLambda,
    ExpressionMonad,
    ExpressionSandbox,
    ExpressionUnaire,
    InstructionAfficher,
    InstructionAstro,
    InstructionConditionnelleForcee,
    InstructionForceExpression,
    InstructionInversionCatch,
    InstructionIsolationMonadique,
    InstructionRetour,
    LitteralChaine,
    LitteralHeliumInerte,
    LitteralNombreUnite,
    ProgrammeAstroQode,
    ReferenceVariable,
)
from .lexer import LexerAstroQode
from .tokens import Token, TokenType


class ErreurSyntaxiqueAstroQode(Exception):
    """Levée lorsqu'une erreur de grammaire est détectée lors du parsing."""

    def __init__(self, message: str, token: Token) -> None:
        super().__init__(
            f"[Erreur Syntaxique L{token.ligne}:C{token.colonne} près de {token.valeur!r}] {message}"
        )
        self.token = token


class ParserAstroQode:
    """Analyseur syntaxique récursif descendant pour ASTRO-Q°ODE V1.0 & V2.0."""

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    @classmethod
    def depuis_source(cls, source: str) -> "ParserAstroQode":
        lexer = LexerAstroQode(source)
        return cls(lexer.tokeniser())

    def _courant(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def _suivant(self, decalage: int = 1) -> Token:
        cible = self.pos + decalage
        if cible >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[cible]

    def _est(self, *types: TokenType) -> bool:
        return self._courant().type in types

    def _avancer(self) -> Token:
        tok = self._courant()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _attendre(self, type_attendu: TokenType, message: str = "") -> Token:
        tok = self._courant()
        if tok.type != type_attendu:
            detail = message or f"Attendu {type_attendu.name}, obtenu {tok.type.name}"
            raise ErreurSyntaxiqueAstroQode(detail, tok)
        return self._avancer()

    def _consommer_points_virgules_optionnels(self) -> None:
        while self._est(TokenType.POINT_VIRGULE):
            self._avancer()

    # ==========================================================================
    # PARSING DU PROGRAMME RACINE
    # ==========================================================================

    def parser_programme(self) -> ProgrammeAstroQode:
        programme = ProgrammeAstroQode()

        while not self._est(TokenType.EOF):
            self._consommer_points_virgules_optionnels()
            if self._est(TokenType.EOF):
                break

            tok = self._courant()

            if tok.type == TokenType.SET:
                directive = self._parser_directive_horloge()
                programme.directives_horloge.append(directive)
                programme.toutes_instructions.append(directive)

            elif tok.type in (TokenType.SPEC_META, TokenType.SPEC_BLOC):
                decl_spec = DeclarationSpecification(contenu=self._avancer().valeur)
                programme.metadonnees_spec.append(decl_spec)
                programme.toutes_instructions.append(decl_spec)

            elif tok.type == TokenType.MECQUOIS:
                bloc_mec = self._parser_bloc_mecquois()
                programme.blocs_mecquois.append(bloc_mec)
                programme.toutes_instructions.append(bloc_mec)

            elif tok.type == TokenType.MEDINOIS:
                bloc_med = self._parser_bloc_medinois()
                programme.blocs_medinois.append(bloc_med)
                programme.toutes_instructions.append(bloc_med)

            else:
                # Permet aussi d'exécuter des instructions directes dans le REPL ou scripts courts
                instr = self._parser_instruction_generale()
                programme.toutes_instructions.append(instr)

            self._consommer_points_virgules_optionnels()

        return programme

    def _parser_directive_horloge(self) -> DirectiveHorloge:
        self._attendre(TokenType.SET)
        nom_tok = self._attendre(TokenType.IDENTIFIANT, "Nom de constante d'horloge attendu après SET.")
        self._attendre(TokenType.AFFECTATION, "Symbole '=' attendu dans la directive SET.")
        val_tok = self._attendre(TokenType.NOMBRE, "Valeur numérique d'horloge attendue.")
        return DirectiveHorloge(nom_horloge=nom_tok.valeur, valeur=float(val_tok.valeur))

    def _parser_bloc_mecquois(self) -> BlocMecquois:
        self._attendre(TokenType.MECQUOIS)
        self._attendre(TokenType.ACCOLADE_G, "Attendu '{' après MECQUOIS.")
        declarations: List[InstructionAstro] = []

        while not self._est(TokenType.ACCOLADE_D, TokenType.EOF):
            self._consommer_points_virgules_optionnels()
            if self._est(TokenType.ACCOLADE_D, TokenType.EOF):
                break

            if self._est(TokenType.SPEC_BLOC, TokenType.SPEC_META):
                declarations.append(DeclarationSpecification(contenu=self._avancer().valeur))
            elif self._est(TokenType.OMEGA_CONST, TokenType.IDENTIFIANT):
                nom_tok = self._avancer()
                self._attendre(TokenType.AFFECTATION, "Attendu '=' dans la déclaration MECQUOIS.")
                expr = self._parser_expression()
                declarations.append(DeclarationConstanteMecquoise(nom=nom_tok.valeur, expression=expr))
            elif self._est(TokenType.AFFICHER):
                declarations.append(self._parser_afficher())
            else:
                raise ErreurSyntaxiqueAstroQode(
                    "Dans un bloc MECQUOIS, seules les déclarations immuables (omega_*) sont autorisées.",
                    self._courant(),
                )
            self._consommer_points_virgules_optionnels()

        self._attendre(TokenType.ACCOLADE_D, "Attendu '}' pour fermer le bloc MECQUOIS.")
        return BlocMecquois(declarations=declarations)

    def _parser_bloc_medinois(self) -> BlocMedinois:
        self._attendre(TokenType.MEDINOIS)
        self._attendre(TokenType.ACCOLADE_G, "Attendu '{' après MEDINOIS.")
        instructions = self._parser_liste_instructions_bloc()
        self._attendre(TokenType.ACCOLADE_D, "Attendu '}' pour fermer le bloc MEDINOIS.")
        return BlocMedinois(instructions=instructions)

    def _parser_liste_instructions_bloc(self) -> List[InstructionAstro]:
        instructions: List[InstructionAstro] = []
        while not self._est(TokenType.ACCOLADE_D, TokenType.EOF):
            self._consommer_points_virgules_optionnels()
            if self._est(TokenType.ACCOLADE_D, TokenType.EOF):
                break
            instructions.append(self._parser_instruction_generale())
            self._consommer_points_virgules_optionnels()
        return instructions

    def _parser_instruction_generale(self) -> InstructionAstro:
        tok = self._courant()

        # 1. Métadonnées de spécification
        if tok.type in (TokenType.SPEC_BLOC, TokenType.SPEC_META):
            return DeclarationSpecification(contenu=self._avancer().valeur)

        # 2. Instruction return
        if tok.type == TokenType.RETURN:
            self._avancer()
            expr = self._parser_expression()
            return InstructionRetour(expression=expr)

        # 3. Instruction afficher(...)
        if tok.type == TokenType.AFFICHER:
            return self._parser_afficher()

        # 4. Bloc d'inversion culturelle autonome : ¿ { ... }
        if tok.type == TokenType.INVERSION_CATCH:
            self._avancer()
            self._attendre(TokenType.ACCOLADE_G, "Attendu '{' après '¿'.")
            corps = self._parser_liste_instructions_bloc()
            self._attendre(TokenType.ACCOLADE_D, "Attendu '}' pour refermer le bloc '¿'.")
            return InstructionInversionCatch(corps=corps)

        # 5. Affectation de constante omega_* ou variable alpha_* (ou identifiant)
        if tok.type in (TokenType.ALPHA_VAR, TokenType.OMEGA_CONST, TokenType.IDENTIFIANT) and self._suivant().type == TokenType.AFFECTATION:
            nom_tok = self._avancer()
            self._attendre(TokenType.AFFECTATION)
            expr = self._parser_expression()
            forcee = False
            if self._est(TokenType.FORCE_DOUBLE):
                self._avancer()
                forcee = True
            if nom_tok.type == TokenType.OMEGA_CONST:
                return DeclarationConstanteMecquoise(nom=nom_tok.valeur, expression=expr)
            return AffectationLocaleMedinoise(nom=nom_tok.valeur, expression=expr, forcee=forcee)

        # 6. Expression (conditionnelle forcée `(cond) ?? { ... }`, transcription forcée `(m >>= fn) ??`, ou isolation `(( m ))`)
        expr = self._parser_expression()

        # Est-ce suivi de `??` ?
        if self._est(TokenType.FORCE_DOUBLE):
            self._avancer()  # consomme '??'
            if self._est(TokenType.ACCOLADE_G):
                self._avancer()  # '{'
                bloc_alors = self._parser_liste_instructions_bloc()
                self._attendre(TokenType.ACCOLADE_D, "Attendu '}' après le bloc conditionnel '??'.")
                bloc_sinon: Optional[List[InstructionAstro]] = None
                if self._est(TokenType.INVERSION_CATCH):
                    self._avancer()  # '¿'
                    self._attendre(TokenType.ACCOLADE_G, "Attendu '{' après '¿'.")
                    bloc_sinon = self._parser_liste_instructions_bloc()
                    self._attendre(TokenType.ACCOLADE_D, "Attendu '}' après le bloc '¿'.")
                return InstructionConditionnelleForcee(
                    condition=expr,
                    bloc_alors=bloc_alors,
                    bloc_sinon_catch=bloc_sinon,
                )
            return InstructionForceExpression(expression=expr)

        # Si c'est une Sandbox de niveau >= 2 `(( expr ))` utilisée en instruction d'isolation
        if isinstance(expr, ExpressionSandbox) and expr.niveau >= 2:
            return InstructionIsolationMonadique(expression=expr.interne)

        return InstructionForceExpression(expression=expr)

    def _parser_afficher(self) -> InstructionAfficher:
        self._attendre(TokenType.AFFICHER)
        if self._est(TokenType.PAREN_G):
            self._avancer()
            expr = self._parser_expression()
            self._attendre(TokenType.PAREN_D, "Attendu ')' après afficher(...).")
            return InstructionAfficher(expression=expr)
        expr = self._parser_expression()
        return InstructionAfficher(expression=expr)

    # ==========================================================================
    # HIÉRARCHIE DES EXPRESSIONS (PRÉCÉDENCE DES OPÉRATEURS)
    # ==========================================================================

    def _parser_expression(self) -> ExpressionAstro:
        return self._parser_bind_monadique()

    def _parser_bind_monadique(self) -> ExpressionAstro:
        gauche = self._parser_logique_ou()
        while self._est(TokenType.BIND_MONADE):
            op = self._avancer().valeur
            droite = self._parser_logique_ou()
            gauche = ExpressionBinaire(gauche=gauche, operateur=op, droite=droite)
        return gauche

    def _parser_logique_ou(self) -> ExpressionAstro:
        gauche = self._parser_logique_et()
        while self._est(TokenType.OU_LOGIQUE, TokenType.XOR_LOGIQUE):
            op = self._avancer().valeur
            droite = self._parser_logique_et()
            gauche = ExpressionBinaire(gauche=gauche, operateur=op, droite=droite)
        return gauche

    def _parser_logique_et(self) -> ExpressionAstro:
        gauche = self._parser_relationnel_et_ensembliste()
        while self._est(TokenType.ET_LOGIQUE, TokenType.NAND_LOGIQUE):
            op = self._avancer().valeur
            droite = self._parser_relationnel_et_ensembliste()
            gauche = ExpressionBinaire(gauche=gauche, operateur=op, droite=droite)
        return gauche

    def _parser_relationnel_et_ensembliste(self) -> ExpressionAstro:
        gauche = self._parser_ensembliste_combinatoire()
        types_rel = (
            TokenType.INCLUSION_LARGE,
            TokenType.INCLUSION_STRICTE,
            TokenType.CONGRUENCE,
            TokenType.NON_CONGRUENCE,
            TokenType.EGAL_LOGIQUE,
            TokenType.DIFF_LOGIQUE,
            TokenType.SUPERIEUR,
            TokenType.INFERIEUR,
        )
        while self._est(*types_rel):
            op = self._avancer().valeur
            droite = self._parser_ensembliste_combinatoire()
            gauche = ExpressionBinaire(gauche=gauche, operateur=op, droite=droite)
        return gauche

    def _parser_ensembliste_combinatoire(self) -> ExpressionAstro:
        gauche = self._parser_additif()
        types_ens = (
            TokenType.UNION,
            TokenType.DIFFERENCE_ENS,
            TokenType.INTERSECTION,
            TokenType.DIV_HARMONIQUE,
            TokenType.POUR_MILLE,
            TokenType.OPLUS_KRONECKER,
            TokenType.OTIMES_KRONECKER,
        )
        while self._est(*types_ens):
            op_tok = self._avancer()
            if op_tok.type == TokenType.UNION:
                op = "∪"
            elif op_tok.type == TokenType.OPLUS_KRONECKER:
                op = "⊕"
            elif op_tok.type == TokenType.OTIMES_KRONECKER:
                op = "⊗"
            else:
                op = op_tok.valeur
            droite = self._parser_additif()
            gauche = ExpressionBinaire(gauche=gauche, operateur=op, droite=droite)
        return gauche

    def _parser_additif(self) -> ExpressionAstro:
        gauche = self._parser_multiplicatif()
        while self._est(TokenType.PLUS, TokenType.MOINS):
            op = self._avancer().valeur
            droite = self._parser_multiplicatif()
            gauche = ExpressionBinaire(gauche=gauche, operateur=op, droite=droite)
        return gauche

    def _parser_multiplicatif(self) -> ExpressionAstro:
        gauche = self._parser_unaire()
        while self._est(TokenType.FOIS, TokenType.DIV, TokenType.MODULO):
            op = self._avancer().valeur
            droite = self._parser_unaire()
            gauche = ExpressionBinaire(gauche=gauche, operateur=op, droite=droite)
        return gauche

    def _parser_unaire(self) -> ExpressionAstro:
        if self._est(TokenType.NON_LOGIQUE, TokenType.MOINS, TokenType.PLUS):
            op = self._avancer().valeur
            return ExpressionUnaire(operateur=op, operande=self._parser_unaire())
        return self._parser_primaire()

    def _parser_primaire(self) -> ExpressionAstro:
        tok = self._courant()

        # 1. Nombre, unité 'i' / 'I', ou '0 : HÉLIUM'
        if tok.type == TokenType.NOMBRE:
            nb_tok = self._avancer()
            # Vérifie la forme spéciale `0 : HÉLIUM`
            if nb_tok.valeur in ("0", "+0", "-0") and self._est(TokenType.DEUX_POINTS):
                self._avancer()  # ':'
                if self._est(TokenType.HELIUM, TokenType.IDENTIFIANT):
                    self._avancer()
                return LitteralHeliumInerte()

            est_entier = "." not in nb_tok.valeur
            val = float(nb_tok.valeur)
            unite: Optional[str] = None
            if self._est(TokenType.UNITE_KELVIN):
                self._avancer()
                unite = "i"
            elif self._est(TokenType.UNITE_JOULES):
                self._avancer()
                unite = "I"
            return LitteralNombreUnite(valeur=val, est_entier=est_entier, unite=unite)

        # 2. Mot-clé direct HÉLIUM
        if tok.type == TokenType.HELIUM:
            self._avancer()
            return LitteralHeliumInerte()

        # 3. Constructeur Monad(expr)
        if tok.type == TokenType.MONAD:
            self._avancer()
            self._attendre(TokenType.PAREN_G, "Attendu '(' après Monad.")
            interne = self._parser_expression()
            self._attendre(TokenType.PAREN_D, "Attendu ')' pour fermer Monad(...).")
            return ExpressionMonad(interne=interne)

        # 4. Constructeur Forme(0..13)
        if tok.type == TokenType.FORME:
            self._avancer()
            self._attendre(TokenType.PAREN_G, "Attendu '(' après Forme.")
            idx_expr = self._parser_expression()
            self._attendre(TokenType.PAREN_D, "Attendu ')' après Forme(...).")
            return ExpressionForme(index_expr=idx_expr)

        # 5. Constructeur fusion_pp(nb_noyaux)
        if tok.type == TokenType.FUSION:
            self._avancer()
            self._attendre(TokenType.PAREN_G, "Attendu '(' après fusion_pp.")
            nb_expr = self._parser_expression()
            self._attendre(TokenType.PAREN_D, "Attendu ')' après fusion_pp(...).")
            return ExpressionFusionPP(nb_noyaux_expr=nb_expr)

        # 5b. Primitives Al-Mizan V3.0, V4.0 & V5.0 (Unisson Or/Argent)
        if tok.type in (
            TokenType.CLAMP_MIZAN,
            TokenType.SPHERE_HOLO,
            TokenType.TRIADE_IBIT,
            TokenType.CYCLE_15,
            TokenType.TIR_SCPI,
            TokenType.CAPTEUR_CRYO,
            TokenType.EXEC_QASM,
            TokenType.SCELLER_SHA256,
            TokenType.MATRICE_UNISSON,
            TokenType.VALEUR_OR,
            TokenType.VALEUR_ARGENT,
        ):
            nom_prim = self._avancer().valeur
            self._attendre(TokenType.PAREN_G, f"Attendu '(' après {nom_prim}.")
            arg_expr = self._parser_expression()
            self._attendre(TokenType.PAREN_D, f"Attendu ')' après {nom_prim}(...).")
            return ExpressionAppelAlmizan(nom_primitive=nom_prim, argument=arg_expr)

        # 6. Expression lambda : `lambda param { ... }`
        if tok.type == TokenType.LAMBDA:
            self._avancer()
            param_tok = self._avancer()
            self._attendre(TokenType.ACCOLADE_G, "Attendu '{' après le paramètre du lambda.")
            corps = self._parser_liste_instructions_bloc()
            self._attendre(TokenType.ACCOLADE_D, "Attendu '}' pour fermer le corps du lambda.")
            return ExpressionLambda(parametre=param_tok.valeur, corps=corps)

        # 7. Ensemble / Contexte `[dx U dy U dz]` ou `[a, b, c]`
        if tok.type == TokenType.CROCHET_G:
            self._avancer()
            elements: List[ExpressionAstro] = []
            if not self._est(TokenType.CROCHET_D):
                # On parse les éléments séparés par ',' ou 'U' / '∪'
                elements.append(self._parser_additif())
                while self._est(TokenType.VIRGULE, TokenType.UNION):
                    self._avancer()
                    elements.append(self._parser_additif())
            self._attendre(TokenType.CROCHET_D, "Attendu ']' pour fermer l'ensemble.")
            return ExpressionEnsemble(elements=elements)

        # 8. Conteneur Sandbox `( expr )` ou Isolation Monadique `(( expr ))`
        if tok.type == TokenType.PAREN_G:
            self._avancer()
            interne = self._parser_expression()
            self._attendre(TokenType.PAREN_D, "Attendu ')' pour fermer la parenthèse.")
            if isinstance(interne, ExpressionSandbox):
                return ExpressionSandbox(interne=interne.interne, niveau=interne.niveau + 1)
            return ExpressionSandbox(interne=interne, niveau=1)

        # 9. Guillemets français d'inversion culturelle `« expr »`
        if tok.type == TokenType.GUILLEMET_FR_G:
            self._avancer()
            interne = self._parser_expression()
            self._attendre(TokenType.GUILLEMET_FR_D, "Attendu '»' pour fermer le conteneur français.")
            return ExpressionSandbox(interne=interne, niveau=2)

        # 10. Chaîne de caractères
        if tok.type == TokenType.CHAINE:
            return LitteralChaine(valeur=self._avancer().valeur)

        # 11. Références aux variables et constantes (omega_*, alpha_*, dx, dy, dz, dt, F0..F26)
        if tok.type in (TokenType.OMEGA_CONST, TokenType.ALPHA_VAR, TokenType.IDENTIFIANT):
            ident = self._avancer().valeur
            # Support des raccourcis F0 .. F26 pour les 27 Formes (14 de base + 13 Duales Al-Mizan)
            if len(ident) in (2, 3) and ident.startswith("F") and ident[1:].isdigit():
                idx = int(ident[1:])
                if 0 <= idx <= 26:
                    return ExpressionForme(
                        index_expr=LitteralNombreUnite(valeur=float(idx), est_entier=True)
                    )
            return ReferenceVariable(nom=ident)

        raise ErreurSyntaxiqueAstroQode(f"Expression inattendue : {tok.valeur!r}", tok)
