# -*- coding: utf-8 -*-
"""
Noyau du Langage ASTRO-Q°ODE (V1.0 & V2.0)
==========================================
Contient la chaîne de compilation et d'exécution complète :
- `tokens.py`          : Types de lexèmes (Tokens) et mots-clés ontologiques.
- `lexer.py`           : Analyseur lexical (supportant la syntaxe V1.0, V2.0, Unicode et ASCII).
- `ast_nodes.py`       : Nœuds de l'Arbre Syntaxique Abstrait (AST).
- `parser.py`          : Analyseur syntaxique récursif descendant.
- `runtime_values.py`  : Valeurs typées d'exécution (Kelvin `i`, Joules `I`, `0 : HÉLIUM`, `Monad`, `Forme`).
- `vm_biomecanique.py` : Machine Virtuelle Biomécanique (Omoplate α/β/γ, Bras `dt`, 5 Doigts).
- `interpreter.py`     : Interpréteur complet ASTRO-Q°ODE V1.0 & V2.0.
- `transpiler.py`      : Transpilateur ASTRO-Q°ODE (.aq) -> Python (.py).
"""

from .tokens import Token, TokenType
from .lexer import LexerAstroQode, ErreurLexicaleAstroQode
from .ast_nodes import ProgrammeAstroQode
from .parser import ParserAstroQode, ErreurSyntaxiqueAstroQode
from .runtime_values import (
    ValeurAstro,
    SignalKelvin,
    EnergieJoules,
    EtatHeliumInerte,
    EnsembleContexte,
)
from .vm_biomecanique import MachineVirtuelleBiomecanique
from .interpreter import InterpreteurAstroQode, ResultatExecutionAstroQode
from .transpiler import TranspilateurPythonAstroQode
from .compilateur_qasm_isa import CompilateurQasmIsaAstroQode, ResultatCompilationQasmIsa

__all__ = [
    "Token",
    "TokenType",
    "LexerAstroQode",
    "ErreurLexicaleAstroQode",
    "ProgrammeAstroQode",
    "ParserAstroQode",
    "ErreurSyntaxiqueAstroQode",
    "ValeurAstro",
    "SignalKelvin",
    "EnergieJoules",
    "EtatHeliumInerte",
    "EnsembleContexte",
    "MachineVirtuelleBiomecanique",
    "InterpreteurAstroQode",
    "ResultatExecutionAstroQode",
    "TranspilateurPythonAstroQode",
    "CompilateurQasmIsaAstroQode",
    "ResultatCompilationQasmIsa",
]
