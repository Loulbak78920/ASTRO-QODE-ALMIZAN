#!/usr/bin/env python3
"""Reproduce elementary Al-Mizan algebra; no external dependencies.

This is a mathematical consistency check, NOT validation of a physical law.
"""
import math

def close(a, b, tol=1e-10):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)

v = (-3.0, 2.0)
w = (2.0, 3.0)
assert close(sum(a*b for a,b in zip(v,w)), 0)
assert close(sum(a*a for a in v), 13)
assert close(sum(a*a for a in w), 13)

qk, qj = -2304.0, 1536.0
a = (-3*qk + 2*qj)/13
b = (2*qk + 3*qj)/13
assert close(a, 768)
assert close(b, 0)
assert close(a*v[0]+b*w[0], qk)
assert close(a*v[1]+b*w[1], qj)
assert close(2*qk+3*qj, 13*b)

# Constant-coefficient example only; gamma and omega are assumed inputs.
gamma, omega, t = 0.1, 0.7, 2.0
A = 768*math.exp(-gamma*t)*math.cos(omega*t)
B = 768*math.exp(-gamma*t)*math.sin(omega*t)
R = 13*B
E = A*A+B*B
assert close(R, 9984*math.exp(-gamma*t)*math.sin(omega*t))
assert close(E, 768**2*math.exp(-2*gamma*t))
assert close(13*E, 13*(A*A+B*B))

# Finite-difference check of E' = -2 gamma E.
h = 1e-5
energy = lambda x: 768**2*math.exp(-2*gamma*x)
derivative = (energy(t+h)-energy(t-h))/(2*h)
assert close(derivative, -2*gamma*energy(t), tol=1e-8)

print("PASS: orthogonal basis, unique decomposition, equilibrium residual,")
print("      constant-coefficient harmonic solution and energy derivative.")
print("NOTE: these tests do not establish any universal physical law.")
