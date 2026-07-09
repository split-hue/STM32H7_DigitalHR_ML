"""
Analiza uspešnosti po razredih (črkah) za vse modele:
  - Model A: EMNIST original  (rezultati_emnist_orig.csv)
  - Model B: EMNIST reduciran (rezultati_emnist_redu.csv)
  - Model C: Obrazec          (rezultati_obrazec.csv)
  - Model D: Bitmaps          (rezultati_bitmaps.csv)
  - Model E: Strokes          (rezultati_strokes.csv)
 
Izriše:
  - Individualni graf točnosti po razredih za vsak model
  - Primerjalni graf vseh 5 modelov na skupni osi
"""
 
 
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from sklearn.metrics import recall_score
 
 
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
    ("Model A", "EMNIST original",  "rezultati_emnist_orig.csv", "#4C72B0"),
    ("Model B", "EMNIST reduciran", "rezultati_emnist_redu.csv", "#DD8452"),
    ("Model C", "Obrazec",          "rezultati_obrazec.csv",     "#8172B2"),
    ("Model D", "Bitmaps",          "rezultati_bitmaps.csv",     "#55A868"),
    ("Model E", "Strokes",          "rezultati_strokes.csv",     "#C44E52"),
]
 
# ── 2. Nalaganje podatkov in izračun točnosti po razredih ────────────────────
 
dfs = {oznaka: parse_log(pot) for oznaka, _, pot, _ in MODELI}
 
all_labels = sorted(
    set().union(*[df["Real"].unique() for df in dfs.values()])
)
x = np.arange(len(all_labels))
 
acc_per_class = {}
for oznaka, _, pot, _ in MODELI:
    df = dfs[oznaka]
    acc_per_class[oznaka] = [
        recall_score(df["Real"], df["Pred"], labels=[l], average="macro", zero_division=0) * 100
        for l in all_labels
    ]
 
# ── 3. Individualni grafi ────────────────────────────────────────────────────
 
for oznaka, opis, _, barva in MODELI:
    acc = acc_per_class[oznaka]
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(x, acc, width=0.6, color=barva)
    ax.set_xticks(x)
    ax.set_xticklabels(all_labels)
    ax.set_xlabel("Črka")
    ax.set_ylabel("Točnost (%)")
    ax.set_title(f"Točnost po razredih — {oznaka} ({opis})")
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%g%%'))
    avg = sum(acc) / len(acc)
    ax.axhline(avg, color="red", linestyle="--", linewidth=1, label=f"Povprečje ({avg:.1f}%)")
    ax.legend()
    plt.tight_layout()
    fname = f"model_{oznaka[-1].lower()}_po_razredih"
    plt.savefig(f"{fname}.pdf")
    plt.savefig(f"{fname}.png", dpi=150)
    plt.show()
 
# ── 4. Primerjalni graf vseh 5 modelov ───────────────────────────────────────
 
n_modeli = len(MODELI)
width    = 0.15
offsets  = np.linspace(-(n_modeli - 1) / 2, (n_modeli - 1) / 2, n_modeli) * width
 
fig, ax = plt.subplots(figsize=(max(14, len(all_labels) * 0.6), 5))
for i, (oznaka, opis, _, barva) in enumerate(MODELI):
    ax.bar(x + offsets[i], acc_per_class[oznaka], width=width,
           color=barva, label=f"{oznaka} ({opis})")
 
ax.set_xticks(x)
ax.set_xticklabels(all_labels)
ax.set_xlabel("Črka")
ax.set_ylabel("Točnost (%)")
ax.set_title("Primerjava točnosti po razredih — vsi modeli")
ax.set_ylim(0, 110)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%g%%'))
ax.legend(loc="upper right", fontsize=8)
plt.tight_layout()
plt.savefig("primerjava_vsi_modeli_po_razredih.pdf")
plt.savefig("primerjava_vsi_modeli_po_razredih.png", dpi=150)
plt.show()
 
# ── 5. Toplotne karte razlik (vsak par z referenčnim modelom D) ──────────────
#  Δk = Točnost_X − Točnost_D  (za modele A, B, C, E)
 
ref_oznaka = "Model D"
ref_acc    = acc_per_class[ref_oznaka]
 
primerjave = [(oz, opis) for oz, opis, _, _ in MODELI if oz != ref_oznaka]
 
fig, axes = plt.subplots(len(primerjave), 1,
                         figsize=(12, 2.2 * len(primerjave)))
if len(primerjave) == 1:
    axes = [axes]
 
for ax, (oz, opis) in zip(axes, primerjave):
    delta     = [a - b for a, b in zip(acc_per_class[oz], ref_acc)]
    delta_arr = np.array(delta).reshape(1, -1)
    im = ax.imshow(delta_arr, aspect="auto", cmap="RdYlGn", vmin=-100, vmax=100)
    ax.set_xticks(np.arange(len(all_labels)))
    ax.set_xticklabels(all_labels)
    ax.set_yticks([])
    ax.set_title(
        f"$\\Delta_k$ = Točnost$_{{{oz[-1]}}}$ − Točnost$_D$   "
        f"({oz}: {opis}  vs  Model D: Bitmaps)"
    )
    for i, d in enumerate(delta):
        ax.text(i, 0, f"{d:+.0f}", ha="center", va="center",
                fontsize=7, color="black")
    plt.colorbar(im, ax=ax, orientation="vertical", label="Δ (%)")
 
plt.tight_layout()
plt.savefig("delta_po_razredih_vse.pdf")
plt.savefig("delta_po_razredih_vse.png", dpi=150)
plt.show()