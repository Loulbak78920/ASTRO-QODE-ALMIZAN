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


# Additional checks derived directly from the published two-pole dossier.
def decompose(qk, qj):
    return ((-3*qk + 2*qj)/13, (2*qk + 3*qj)/13)

def reconstruct(a, b):
    return (-3*a + 2*b, 2*a + 3*b)

for qk, qj in ((-2304, 1536), (0, 0), (13, -7), (-9, -11)):
    aa, bb = decompose(qk, qj)
    rr = 2*qk + 3*qj
    qk2, qj2 = reconstruct(aa, bb)
    assert close(qk2, qk) and close(qj2, qj)
    assert close(rr, 13*bb)
    assert close(qk*qk + qj*qj, 13*(aa*aa + bb*bb))

# For constant coefficients, verify both differential equations and residual.
def state(x):
    amp = 768*math.exp(-gamma*x)
    return amp*math.cos(omega*x), amp*math.sin(omega*x)

a_t, b_t = state(t)
a_p, b_p = state(t+h)
a_m, b_m = state(t-h)
assert close((a_p-a_m)/(2*h), -gamma*a_t-omega*b_t, tol=1e-8)
assert close((b_p-b_m)/(2*h), omega*a_t-gamma*b_t, tol=1e-8)
assert close(13*b_t, 9984*math.exp(-gamma*t)*math.sin(omega*t))

print("PASS: orthogonal basis, unique decomposition, equilibrium residual,")
print("      constant-coefficient harmonic solution and energy derivative.")
print("NOTE: these tests do not establish any universal physical law.")
