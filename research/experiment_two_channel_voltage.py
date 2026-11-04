#!/usr/bin/env python3
"""AL-MIZAN two-channel voltage experiment. Standard library only.

CSV columns: t_s,qk_v,qj_v; optional sigma_qk_v,sigma_qj_v.
Calibration CSV must be independent of validation CSV.
A(t), B(t) are volts. gamma [1/s], omega [rad/s].
Assumption: constant gamma and omega, not derived from AL-MIZAN algebra.
"""
import argparse
import csv
import json
import math
import sys

def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 3:
        raise ValueError("At least three rows required in each CSV")
    out = []
    for row in rows:
        t, qk, qj = (float(row[k]) for k in ("t_s", "qk_v", "qj_v"))
        sk = float(row.get("sigma_qk_v") or 0)
        sj = float(row.get("sigma_qj_v") or 0)
        if not all(math.isfinite(x) for x in (t, qk, qj, sk, sj)) or min(sk, sj) < 0:
            raise ValueError("Non-finite or negative-uncertainty data")
        a = (-3*qk + 2*qj)/13
        b = (2*qk + 3*qj)/13
        out.append(dict(t=t, a=a, b=b, r=13*b, sr=math.hypot(2*sk, 3*sj)))
    if any(y["t"] <= x["t"] for x, y in zip(out, out[1:])):
        raise ValueError("Times must be strictly increasing")
    return out

def fit(cal):
    # Explicit least-squares estimation of log amplitude and unwrapped phase.
    t0 = cal[0]["t"]
    ts = [x["t"]-t0 for x in cal]
    zs = [complex(x["a"], x["b"]) for x in cal]
    if any(abs(z) == 0 for z in zs):
        raise ValueError("Zero amplitude: phase undefined")
    phases = [math.atan2(z.imag, z.real) for z in zs]
    for i in range(1, len(phases)):
        delta = phases[i]-phases[i-1]
        while delta > math.pi:
            phases[i] -= 2*math.pi
            delta -= 2*math.pi
        while delta < -math.pi:
            phases[i] += 2*math.pi
            delta += 2*math.pi
    def line(ys):
        mt = sum(ts)/len(ts)
        my = sum(ys)/len(ys)
        den = sum((t-mt)**2 for t in ts)
        if den == 0:
            raise ValueError("Degenerate time range")
        slope = sum((t-mt)*(y-my) for t,y in zip(ts,ys))/den
        return my-slope*mt, slope
    loga0, neg_gamma = line([math.log(abs(z)) for z in zs])
    phi0, omega = line(phases)
    return dict(t0=t0, amp0=math.exp(loga0), phi0=phi0,
                gamma=-neg_gamma, omega=omega)

def predict(model, t):
    dt=t-model["t0"]
    amp=model["amp0"]*math.exp(-model["gamma"]*dt)
    phase=model["phi0"]+model["omega"]*dt
    return amp*math.cos(phase), amp*math.sin(phase)

def evaluate(cal, val):
    if val[0]["t"] <= cal[-1]["t"]:
        raise ValueError("Validation must be strictly later than calibration")
    m=fit(cal)
    residuals=[]
    baseline=[]
    z0=complex(cal[-1]["a"], cal[-1]["b"])
    for row in val:
        ap,bp=predict(m,row["t"])
        residuals.append(math.hypot(row["a"]-ap,row["b"]-bp))
        baseline.append(abs(complex(row["a"],row["b"])-z0))
    rmse=math.sqrt(sum(x*x for x in residuals)/len(residuals))
    base=math.sqrt(sum(x*x for x in baseline)/len(baseline))
    return dict(status="ANALYSIS_ONLY_NOT_PHYSICAL_VALIDATION",
                n_calibration=len(cal), n_validation=len(val),
                gamma_per_s=m["gamma"], omega_rad_per_s=m["omega"],
                rmse_vector_v=rmse, baseline_persistence_rmse_v=base,
                beats_persistence=rmse<base,
                limitation="Two voltages do not establish a universal law; uncertainty calibration, instrument provenance and independent physical parameter derivation remain necessary.")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--calibration", required=True)
    p.add_argument("--validation", required=True)
    args=p.parse_args()
    try:
        print(json.dumps(evaluate(read(args.calibration),read(args.validation)),indent=2))
    except (ValueError,KeyError,OverflowError,FileNotFoundError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":
    sys.exit(main())
