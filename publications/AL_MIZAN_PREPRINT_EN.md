
> **Manuscript DOI (author-confirmed publication / publication confirmée par l'auteur):** https://doi.org/10.5281/zenodo.23918713 . The DOI's record metadata have not been independently inspected here; this DOI is distinct from the older project DOI 10.5281/zenodo.23554838.

# Al-Mizan: An Orthogonal Two-Pole Decomposition and Conditional Harmonic Dynamics

**Author (project originator):** Ahmed EL BAHLOUL  
**Version:** 2026-11-03 — open preprint draft  
**Repository:** https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN  
**Related project DOI:** https://doi.org/10.5281/zenodo.23554838 (not necessarily a DOI for this manuscript)

## Abstract

We describe a two-dimensional orthogonal coordinate system and a damped harmonic differential equation postulated for its coordinates. We derive the explicit solution, equilibrium residual and energy identity. We distinguish these elementary but exact mathematical consequences from untested physical interpretations, including possible contraction and phase dynamics. The framework is presented for reproducible critique, not as an established universal law of nature.

## 1. Definitions and algebraic decomposition

Let `q=(Q_K,Q_J)^T` and `v=(-3,2)^T`, `w=(2,3)^T`. Then `v·w=0` and `v·v=w·w=13`. Thus `q=A v+B w`, uniquely, where

```text
A=(-3 Q_K+2 Q_J)/13,
B=( 2 Q_K+3 Q_J)/13.
```

The balance residual is `R=2 Q_K+3 Q_J=13B`. Hence `R=0` iff `B=0`.

For the stipulated initial vector `q(0)=(-2304,1536)^T`, we obtain `A(0)=768`, `B(0)=0`.

## 2. Conditional dynamics

Assume `gamma(t)` and `omega(t)` are real integrable functions and the coordinate pair satisfies

```text
A'=-gamma A-omega B,
B'= omega A-gamma B.
```

Set `Z=A+iB`. Then `Z'=(-gamma+i omega)Z`. Define `Gamma(t)=integral_0^t gamma(s)ds` and `Phi(t)=integral_0^t omega(s)ds`. The unique solution with `Z(0)=768` is

```text
Z(t)=768 exp(-Gamma(t)+i Phi(t)).
```

Consequently, `R(t)=9984 exp(-Gamma(t)) sin(Phi(t))`. At nonzero amplitude, `R(t)=0` exactly when `Phi(t)` is an integer multiple of pi.

Let `E(t)=|Z(t)|^2`. Differentiating yields `E'=-2 gamma E` almost everywhere. For the real vector `q=A v+B w`, `||q||²=13E`. The outer product `M=q q^T` is symmetric positive semidefinite and has rank one for `q != 0`; `det(M)=0`, `tr(M)=13E`.

## 3. What is not established

The differential equation is an assumption, not a derivation from fundamental physics. Indeed, any nonvanishing differentiable complex trajectory `Z=a exp(i phi)` can be written in this form by defining `gamma=-a'/a`, `omega=phi'`. Thus the equation alone cannot predict physical phenomena unless these functions are specified independently of the observations.

The initial ratio `-3:2` is stipulated; it is not proven to be a universal physical ratio. The value 13 arises from `3²+2²`, not automatically from a physical 13-phase cycle. The parameter `F0=0.122` has not been independently derived from physical principles. A separate 4×4 contraction operator requires a demonstrated mapping to this two-dimensional model before physical equivalence can be claimed.

No gravitational, cosmological or quantum interpretation is validated by the calculations in this paper. In particular, no prediction for the Sun–Earth–Moon system follows without explicit, dimensionally consistent physical observables and independently estimated parameters.

## 4. Reproducibility and open questions

The standard-library verification program is available at [research/verify_al_mizan.py](../research/verify_al_mizan.py). It checks the orthogonal basis, the initial decomposition and a constant-coefficient example.

A predictive physical hypothesis would require: (i) defined observables with units, (ii) independently specified dynamics, (iii) preregistered quantitative predictions and uncertainties, (iv) out-of-sample tests, and (v) comparison against established physical models. Counterexamples and negative results are welcome.

## 5. Authorship, licensing and references

Project originator and claimed author: **Ahmed EL BAHLOUL**. Publication history and exact versions can be traced through repository commits. This does not, by itself, establish novelty of every mathematical identity or legal priority over all related work.

Reuse is governed by the repository's [LICENSE](../LICENSE). See the [full mathematical dossier](2026-11-03_AL_MIZAN_THEOREME_HARMONIQUE_ET_LIMITES_PHYSIQUES.md), [international invitation](2026-11-03_INTERNATIONAL_OPEN_RESEARCH_INVITATION_AL_MIZAN.md) and [citation metadata](../CITATION.cff).

**Publication status:** Public GitHub preprint draft. Not peer reviewed; not submitted to or accepted by arXiv, HAL or Zenodo as this manuscript.
