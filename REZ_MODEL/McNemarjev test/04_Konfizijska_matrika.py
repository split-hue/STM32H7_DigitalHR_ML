"""
Konfuzijske matrike za vse modele:
  - Model A: EMNIST original  (rezultati_emnist_orig.csv)
  - Model B: EMNIST reduciran (rezultati_emnist_redu.csv)
  - Model C: Obrazec          (rezultati_obrazec.csv)
  - Model D: Bitmaps          (rezultati_bitmaps.csv)
  - Model E: Strokes          (rezultati_strokes.csv)
 
Normalizacija po vrsticah (delež napovedi v %).
"""
 
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix
 
 
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
 
 
MODELI = [
    ("A", "EMNIST original",  "rezultati_emnist_orig.csv"),
    ("B", "EMNIST reduciran", "rezultati_emnist_redu.csv"),
    ("C", "Obrazec",          "rezultati_obrazec.csv"),
    ("D", "Bitmaps",          "rezultati_bitmaps.csv"),
    ("E", "Strokes",          "rezultati_strokes.csv"),
]
 
# ── 2. Konfuzijska matrika ───────────────────────────────────────────────────
 
def plot_confusion_matrix(df: pd.DataFrame, title: str, filename: str) -> None:
    labels  = sorted(df["Real"].unique())
    cm      = confusion_matrix(df["Real"], df["Pred"], labels=labels)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100
 
    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=100)
 
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Napovedani razred", fontsize=11)
    ax.set_ylabel("Dejanski razred", fontsize=11)
    ax.set_title(title, fontsize=13)
 
    for i in range(len(labels)):
        for j in range(len(labels)):
            val   = cm_norm[i, j]
            color = "white" if val > 60 else "black"
            ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                    fontsize=7, color=color)
 
    plt.colorbar(im, ax=ax, label="Delež napovedi (%)")
    plt.tight_layout()
    plt.savefig(f"{filename}.pdf")
    plt.savefig(f"{filename}.png", dpi=150)
    plt.show()
 
 
for oznaka, opis, pot in MODELI:
    df = parse_log(pot)
    plot_confusion_matrix(
        df,
        title    = f"Konfuzijska matrika — Model {oznaka} ({opis})",
        filename = f"konfuzija_{oznaka}",
    )