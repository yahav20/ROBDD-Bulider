# pysmt_parse.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from pysmt.shortcuts import Symbol, And, Or, Not, Xor, Implies, Iff
from pysmt.typing import BOOL
from pysmt.shortcuts import serialize

# ==========================================
# PART 1: PARSER LOGIC 
# ==========================================

def tokenize(s: str) -> List[str]:
    # Remove all whitespace from the input string
    s = s.replace(" ", "")
    tokens = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch.isalpha() or ch == "_":
            j = i + 1
            # Read full variable names (alphanumeric + underscore)
            while j < len(s) and (s[j].isalnum() or s[j] == "_"):
                j += 1
            tokens.append(s[i:j])
            i = j
        elif ch in "()!&|^":
            # Single-character operators and parentheses
            tokens.append(ch)
            i += 1
        elif s.startswith("<->", i):
            # Bi-implication operator
            tokens.append("<->")
            i += 3
        elif s.startswith("->", i):
            # Implication operator
            tokens.append("->")
            i += 2
        else:
            # Handle unexpected characters
            raise ValueError(f"Unexpected character at {i}: {s[i:i+10]}")
    # Return the list of tokens
    return tokens


# Pratt parser precedence (low -> high)
PRECEDENCE = {
    "<->": 1,
    "->": 2,
    "|": 3,
    "^": 4,
    "&": 5,
}


def parse_pysmt(formula: str):
    # Tokenize the input formula string
    toks = tokenize(formula)
    # Start parsing the expression with minimum precedence 0
    node, idx = _parse_expr(toks, 0, min_prec=0)
    # Check for any unparsed trailing tokens
    if idx != len(toks):
        raise ValueError(f"Trailing tokens: {toks[idx:]}")
    return node


def _parse_expr(toks: List[str], i: int, min_prec: int):
    if i >= len(toks):
        raise ValueError("Unexpected end of input")

    tok = toks[i]

    # prefix
    if tok == "!":
        # Handle NOT operator (highest precedence)
        rhs, j = _parse_expr(toks, i + 1, min_prec=PRECEDENCE["&"] + 1)
        lhs = Not(rhs)
        i = j
    elif tok == "(":
        # Handle parentheses for grouping
        lhs, j = _parse_expr(toks, i + 1, min_prec=0)
        if j >= len(toks) or toks[j] != ")":
            raise ValueError("Missing ')'")
        i = j + 1
    else:
        # Assume it's a variable symbol
        lhs = Symbol(tok, BOOL)
        i += 1

    # infix loop
    while i < len(toks):
        op = toks[i]
        # Stop if closing parenthesis or another prefix operator
        if op == ")" or op == "!":
            break
        if op not in PRECEDENCE:
            break

        prec = PRECEDENCE[op]
        # Stop if current operator has lower precedence than min_prec
        if prec < min_prec:
            break

        # right-assoc for -> and <-> (common)
        next_min_prec = prec + (0 if op in ("->", "<->") else 1)
        rhs, j = _parse_expr(toks, i + 1, next_min_prec)

        # Apply the corresponding PySMT operator
        if op == "&":
            lhs = And(lhs, rhs)
        elif op == "|":
            lhs = Or(lhs, rhs)
        elif op == "^":
            lhs = Xor(lhs, rhs)
        elif op == "->":
            lhs = Implies(lhs, rhs)
        elif op == "<->":
            lhs = Iff(lhs, rhs)
        else:
            raise ValueError(f"Unknown op: {op}")

        i = j

    return lhs, i

if __name__ == "__main__":
    # Example usage:
    formula = "a & (b | !c) -> d <-> e ^ f"
    parsed = parse_pysmt(formula)
    print(parsed.serialize())