"""
Skupne pomožne funkcije — uvozi jih v katerikoli skript:
 
    from utils import parse_log, load_both
"""
 
import pandas as pd
 
 
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
 
 
def load_both(
    path_bitmaps: str = "rezultati_bitmaps.csv",
    path_strokes: str = "rezultati_strokes.csv",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Naloži obe datoteki in preveri, da imata enako število vzorcev."""
    bitmaps = parse_log(path_bitmaps)
    strokes = parse_log(path_strokes)
    assert len(bitmaps) == len(strokes), (
        f"Različno število vzorcev: bitmaps={len(bitmaps)}, strokes={len(strokes)}"
    )
    return bitmaps, strokes
 