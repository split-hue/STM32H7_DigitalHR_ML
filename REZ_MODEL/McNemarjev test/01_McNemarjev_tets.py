"""
McNemarjev test za primerjavo dveh modelov:
  - Model C: bitmaps (rezultati_bitmaps.csv)
  - Model D: strokes (rezultati_strokes.csv)
 
McNemarjev test meri, ali se modela statistično značilno razlikujeta
v napakah — torej ali eden naredi napake tam, kjer drugi ne.
"""
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


 
import pandas as pd
from scipy.stats import chi2 as chi2_dist
 
 
# ── 1. Branje in razčlenitev PuTTY log datotek ──────────────────────────────
 
def parse_log(path: str) -> pd.DataFrame:
    """Izvleče vrstice s podatki (6 polj, ločenih s ';') iz PuTTY loga."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    data_lines = [
        l.strip() for l in lines
        if l.strip().count(";") == 5 and not l.strip().startswith("ID")
    ]
    rows = [l.split(";") for l in data_lines]
    df = pd.DataFrame(rows, columns=["ID", "Real", "Pred", "Conf", "Cycles", "us"])
    df["Real"] = df["Real"].str.strip()
    df["Pred"] = df["Pred"].str.strip()
    return df
 
 
strokes = parse_log("rezultati_strokes.csv")
bitmaps = parse_log("rezultati_bitmaps.csv")
 
assert len(strokes) == len(bitmaps), (
    f"Različno število vzorcev: strokes={len(strokes)}, bitmaps={len(bitmaps)}"
)
 
# ── 2. Pravilnost napovedi ───────────────────────────────────────────────────
 
correct_s = (strokes["Real"] == strokes["Pred"]).astype(int)
correct_b = (bitmaps["Real"] == bitmaps["Pred"]).astype(int)
 
# ── 3. Kontingenčna tabela ───────────────────────────────────────────────────
#
#           Bitmaps
#           Pravilno  Napačno
# Strokes  Pravilno   a         b
#          Napačno    c         d
 
a = int(((correct_s == 1) & (correct_b == 1)).sum())
b = int(((correct_s == 1) & (correct_b == 0)).sum())
c = int(((correct_s == 0) & (correct_b == 1)).sum())
d = int(((correct_s == 0) & (correct_b == 0)).sum())
 
print("=" * 60)
print("Kontingenčna tabela (McNemarjev test)")
print("=" * 60)
print(f"{'':25s} Bitmaps ✓   Bitmaps ✗")
print(f"{'Strokes ✓':25s}  {a:5d}       {b:5d}")
print(f"{'Strokes ✗':25s}  {c:5d}       {d:5d}")
print()
 
# ── 4. Izračun McNemarjevega testa ───────────────────────────────────────────
 
chi2_stat_yates = (abs(b - c) - 1) ** 2 / (b + c) if (b + c) > 0 else 0.0
chi2_stat       = (b - c) ** 2 / (b + c)           if (b + c) > 0 else 0.0
 
p_yates = 1 - chi2_dist.cdf(chi2_stat_yates, df=1)
p_value  = 1 - chi2_dist.cdf(chi2_stat,       df=1)
 
print("=" * 60)
print("Rezultati McNemarjevega testa")
print("=" * 60)
print(f"  b (Strokes ✓, Bitmaps ✗) = {b}")
print(f"  c (Strokes ✗, Bitmaps ✓) = {c}")
print()
print(f"  χ² (brez korekcije)       = {chi2_stat:.4f}")
print(f"  p-vrednost                = {p_value:.9f}")
print()
print(f"  χ² (Yatesova korekcija)   = {chi2_stat_yates:.4f}")
print(f"  p-vrednost (Yates)        = {p_yates:.9f}")
 
# ── 5. Zaključek ─────────────────────────────────────────────────────────────
 
alpha = 0.05
print()
print("=" * 60)
print(f"Stopnja značilnosti α = {alpha}")
if p_yates < alpha:
    print(">> Razlika med modeloma je statistično ZNAČILNA (zavrnemo H₀).")
    print("   Modela se statistično razlikujeta v svojih napakah.")
else:
    print(">> Razlika med modeloma NI statistično značilna (ne zavrnemo H₀).")
    print("   Ni dovolj dokazov, da bi se modela razlikovala.")
print("=" * 60)
 
# ── 6. Pregled točnosti ──────────────────────────────────────────────────────
 
acc_s = correct_s.mean() * 100
acc_b = correct_b.mean() * 100
print()
print("Povzetek točnosti:")
print(f"  Strokes : {correct_s.sum():3d} / {len(strokes)} = {acc_s:.2f}%")
print(f"  Bitmaps : {correct_b.sum():3d} / {len(bitmaps)} = {acc_b:.2f}%")