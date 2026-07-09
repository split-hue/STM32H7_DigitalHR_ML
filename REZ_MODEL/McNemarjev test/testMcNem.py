"""
McNemarjev test za primerjavo dveh modelov:
  - Model A: strokes (rezultati_strokes.csv)
  - Model B: bitmaps (rezultati_bitmaps.csv)
 
McNemarjev test meri, ali se modela statistično značilno razlikujeta
v napakah — torej ali eden naredi napake tam, kjer drugi ne.
"""
 
import pandas as pd
from scipy.stats import chi2 as chi2_dist
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
 
 
strokes = parse_log("rezultati_strokes.csv")
bitmaps = parse_log("rezultati_bitmaps.csv")
 
assert len(strokes) == len(bitmaps), (
    f"Različno število vzorcev: strokes={len(strokes)}, bitmaps={len(bitmaps)}"
)
 
# ── 2. Pravilnost napovedi ───────────────────────────────────────────────────
 
correct_s = (strokes["Real"] == strokes["Pred"]).astype(int)
correct_b = (bitmaps["Real"] == bitmaps["Pred"]).astype(int)

# ── 3. Globalne klasifikacijske metrike ──────────────────────────────────────

def print_metrics(name: str, df: pd.DataFrame, correct: pd.Series) -> None:
    y_true = df["Real"]
    y_pred = df["Pred"]
    labels = sorted(y_true.unique())

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


print_metrics("Bitmaps (Model C)", bitmaps, correct_b)
print_metrics("Strokes (Model D)", strokes, correct_s)

# ── 4. Kontingenčna tabela McNemarjevega testa ───────────────────────────────
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
 
# ── 5. Izračun McNemarjevega testa ───────────────────────────────────────────
 
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
 
# ── 6. Zaključek ─────────────────────────────────────────────────────────────
 
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
 
# ── 7. Pregled točnosti ──────────────────────────────────────────────────────
 
acc_s = correct_s.mean() * 100
acc_b = correct_b.mean() * 100
print()
print("Povzetek točnosti:")
print(f"  Strokes : {correct_s.sum():3d} / {len(strokes)} = {acc_s:.2f}%")
print(f"  Bitmaps : {correct_b.sum():3d} / {len(bitmaps)} = {acc_b:.2f}%")




#################################################################################
#################### Analiza uspeŠnosti po razredih ##############################
#################################################################################

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from sklearn.metrics import recall_score

# ── Točnost po razredih ──────────────────────────────────────────────────────

labels = sorted(set(bitmaps["Real"].unique()) | set(strokes["Real"].unique()))

acc_per_class_b = [
    recall_score(bitmaps["Real"], bitmaps["Pred"], labels=[l], average="macro", zero_division=0) * 100
    for l in labels
]
acc_per_class_s = [
    recall_score(strokes["Real"], strokes["Pred"], labels=[l], average="macro", zero_division=0) * 100
    for l in labels
]

delta = [s - b for s, b in zip(acc_per_class_s, acc_per_class_b)]

x = np.arange(len(labels))
width = 0.4

# ── Graf 1: Točnost po razredih - Model C (Bitmaps) ─────────────────────────

fig, ax = plt.subplots(figsize=(12, 4))
ax.bar(x, acc_per_class_b, width=0.6, color="#4C72B0")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_xlabel("Črka")
ax.set_ylabel("Točnost (%)")
ax.set_title("Točnost po razredih - Model C (slikovni vhod)")
ax.set_ylim(0, 105)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%g%%'))
ax.axhline(sum(acc_per_class_b) / len(acc_per_class_b), color="red",
           linestyle="--", linewidth=1, label="Povprečje")
ax.legend()
plt.tight_layout()
plt.savefig("model_c_po_razredih.pdf")
plt.savefig("model_c_po_razredih.png", dpi=150)
plt.show()

# ── Graf 2: Točnost po razredih - Model D (Strokes) ─────────────────────────

fig, ax = plt.subplots(figsize=(12, 4))
ax.bar(x, acc_per_class_s, width=0.6, color="#55A868")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_xlabel("Črka")
ax.set_ylabel("Točnost (%)")
ax.set_title("Točnost po razredih - Model D (vektorski vhod)")
ax.set_ylim(0, 105)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%g%%'))
ax.axhline(sum(acc_per_class_s) / len(acc_per_class_s), color="red",
           linestyle="--", linewidth=1, label="Povprečje")
ax.legend()
plt.tight_layout()
plt.savefig("model_d_po_razredih.pdf")
plt.savefig("model_d_po_razredih.png", dpi=150)
plt.show()

# ── Graf 3: Razlika Δk = D - C (toplotna karta) ─────────────────────────────

fig, ax = plt.subplots(figsize=(12, 2))
delta_arr = np.array(delta).reshape(1, -1)
im = ax.imshow(delta_arr, aspect="auto", cmap="RdYlGn", vmin=-100, vmax=100)
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_yticks([])
ax.set_title("Razlika točnosti po razredih: $\\Delta_k$ = Točnost$_D$ − Točnost$_C$ (%)")
for i, (d, l) in enumerate(zip(delta, labels)):
    ax.text(i, 0, f"{d:+.0f}", ha="center", va="center", fontsize=8,
            color="black")
plt.colorbar(im, ax=ax, orientation="vertical", label="Δ (%)")
plt.tight_layout()
plt.savefig("delta_po_razredih.pdf")
plt.savefig("delta_po_razredih.png", dpi=150)
plt.show()


#################################################################################
####################### KONFUZIJSKA MATRIKA #####################################
#################################################################################


from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import numpy as np

# ── Konfuzijski matriki ──────────────────────────────────────────────────────

def plot_confusion_matrix(df: pd.DataFrame, title: str, filename: str) -> None:
    labels = sorted(df["Real"].unique())
    cm = confusion_matrix(df["Real"], df["Pred"], labels=labels)
    
    # Normalizacija po vrsticah (delež, ne absolutno število)
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

    # Vrednosti v celicah — samo neničelne, da ni gneče
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = cm_norm[i, j]
            if True: #if val > 0:
                color = "white" if val > 60 else "black"
                ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                        fontsize=7, color=color)

    plt.colorbar(im, ax=ax, label="Delež napovedi (%)")
    plt.tight_layout()
    plt.savefig(f"{filename}.pdf")
    plt.savefig(f"{filename}.png", dpi=150)
    plt.show()


plot_confusion_matrix(bitmaps, "Konfuzijska matrika — Model C (slikovni vhod)", "konfuzija_C")
plot_confusion_matrix(strokes, "Konfuzijska matrika — Model D (vektorski vhod)", "konfuzija_D")