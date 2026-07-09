# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
 
"""
Globalne klasifikacijske metrike za vse modele:
  - Model A: EMNIST original  (rezultati_emnist_orig.csv)
  - Model B: EMNIST reduciran (rezultati_emnist_redu.csv)
  - Model C: Obrazec          (rezultati_obrazec.csv)
  - Model D: Bitmaps          (rezultati_bitmaps.csv)
  - Model E: Strokes          (rezultati_strokes.csv)
"""
 
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report
 
 
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
 
 
MODELI = {
    "Model A (EMNIST original)":  "rezultati_emnist_orig.csv",
    "Model B (EMNIST reduciran)":  "rezultati_emnist_redu.csv",
    "Model C (Obrazec)":           "rezultati_obrazec.csv",
    "Model D (Bitmaps)":           "rezultati_bitmaps.csv",
    "Model E (Strokes)":           "rezultati_strokes.csv",
}
 
# ── 2. Globalne klasifikacijske metrike ──────────────────────────────────────
 
def print_metrics(name: str, df: pd.DataFrame) -> None:
    y_true  = df["Real"]
    y_pred  = df["Pred"]
    labels  = sorted(y_true.unique())
    correct = (y_true == y_pred)
 
    acc    = correct.mean() * 100
    prec   = precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0) * 100
    recall = recall_score(   y_true, y_pred, labels=labels, average="macro", zero_division=0) * 100
    f1     = f1_score(       y_true, y_pred, labels=labels, average="macro", zero_division=0) * 100
 
    print("=" * 60)
    print(f"Globalne klasifikacijske metrike — {name}")
    print("=" * 60)
    print(f"  Globalna točnost          : {correct.sum():3d} / {len(correct)} = {acc:.2f}%")
    print(f"  Makro natančnost          : {prec:.2f}%")
    print(f"  Makro priklic             : {recall:.2f}%")
    print(f"  Makro F1                  : {f1:.2f}%")
    print()
    print("  Metrike po razredih (črke):")
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0, digits=4))
 
 
for ime, pot in MODELI.items():
    df = parse_log(pot)
    print_metrics(ime, df)