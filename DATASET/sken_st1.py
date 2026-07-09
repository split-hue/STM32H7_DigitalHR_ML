# -*- coding: utf-8 -*-
"""
Izrezovalnik celic iz skeniranih obrazcev za zbiranje slovenskih črk.
Različica v5 – 28x28 izvoz v podmape IN hkrati v eno skupno mapo.
 
Zahteve: pip install opencv-python pillow numpy
"""
 
import sys
import io
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
 
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
 

 

VRSTNI_RED_MAP = [
    "M", "Ž", "A", "K", "Š", "D", "E", "T",
    "Č", "L", "B", "P", "V", "R", "O", "U",
    "G", "S", "I", "N", "J", "H", "Z", "F",
    "C", "Ž", "C", "A", "T", "Š", "B", "L",
    "I", "R", "O", "K", "E", "P", "N", "D",
    "S", "H", "U", "Z", "G", "J", "V", "F",
    "M", "Č", "S", "Ž", "K", "A", "Č", "N",
]
 
VHODNA_MAPA = "skenirani_obrazci_jpg_st1"
IZHODNA_MAPA = "izvozene_crke"   
SKUPNA_MAPA = "obrazec-vse"   
FORMATI = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
 

MIN_SIRINA = 40
MIN_VISINA = 20  
 

OBREZI_ROB = 0.1

PRESKOK_GLAVE = 0.25
 
# ── FUNK
 
def predobdelaj_sliko(slika_gray: np.ndarray) -> np.ndarray:
    visina, sirina = slika_gray.shape
    if max(visina, sirina) > 3000:
        faktor = 3000 / max(visina, sirina)
        slika_gray = cv2.resize(
            slika_gray,
            (int(sirina * faktor), int(visina * faktor)),
            interpolation=cv2.INTER_AREA
        )
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    slika_gray = clahe.apply(slika_gray)
    slika_gray = cv2.GaussianBlur(slika_gray, (3, 3), 0)
    return slika_gray
 
 
def zaznej_mrejo_s_hough(slika_gray: np.ndarray):
    visina, sirina = slika_gray.shape
 
    bin_slika = cv2.adaptiveThreshold(
        slika_gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=25, C=12
    )
 
    dolzina_horiz = max(sirina // 8, 60)
    jedro_horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (dolzina_horiz, 1))
    horiz = cv2.morphologyEx(bin_slika, cv2.MORPH_OPEN, jedro_horiz, iterations=1)
    horiz = cv2.dilate(horiz, np.ones((3, 1), np.uint8), iterations=2)
 
    dolzina_vert = max(visina // 8, 60)
    jedro_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (1, dolzina_vert))
    vert = cv2.morphologyEx(bin_slika, cv2.MORPH_OPEN, jedro_vert, iterations=1)
    vert = cv2.dilate(vert, np.ones((1, 3), np.uint8), iterations=2)
 
    projekcija_h = np.sum(horiz, axis=1).astype(np.float32)
    horiz_y = _najdi_pike_projekcije(projekcija_h)
 
    projekcija_v = np.sum(vert, axis=0).astype(np.float32)
    vert_x = _najdi_pike_projekcije(projekcija_v)
 
    return horiz_y, vert_x, horiz, vert
 
 
def _najdi_pike_projekcije(projekcija: np.ndarray) -> list:
    maks = projekcija.max()
    if maks == 0:
        return []
 
    normalizirana = projekcija / maks
    maske = normalizirana > 0.25
 
    pike = []
    v_grupi = False
    zacetek = 0
 
    for i, vrednost in enumerate(maske):
        if vrednost and not v_grupi:
            v_grupi = True
            zacetek = i
        elif not vrednost and v_grupi:
            v_grupi = False
            pike.append((zacetek + i) // 2)
 
    if v_grupi:
        pike.append((zacetek + len(maske)) // 2)
 
    return pike
 
 
def filtriraj_in_popravi_mrejo(horiz_y: list, vert_x: list,
                                slika_visina: int, slika_sirina: int):
    horiz_y = [y for y in horiz_y if 0.02 * slika_visina < y < 0.98 * slika_visina]
    vert_x = [x for x in vert_x if 0.02 * slika_sirina < x < 0.98 * slika_sirina]
 
    horiz_y = _odstrani_podvojene(sorted(horiz_y), min_razdalja=15)
    vert_x = _odstrani_podvojene(sorted(vert_x), min_razdalja=15)
 
    return horiz_y, vert_x
 
 
def _odstrani_podvojene(pike: list, min_razdalja: int = 15) -> list:
    if not pike:
        return []
    filtrirane = [pike[0]]
    for pika in pike[1:]:
        if pika - filtrirane[-1] >= min_razdalja:
            filtrirane.append(pika)
    return filtrirane
 
 
def sestavi_rokopisne_celice(horiz_y: list, vert_x: list,
                              slika_visina: int, slika_sirina: int) -> list:
    if len(horiz_y) < 2 or len(vert_x) < 2:
        return []
 
    razmiki = [horiz_y[i+1] - horiz_y[i] for i in range(len(horiz_y)-1)]
 
    if not razmiki:
        return []
 
    mediana_razmika = float(np.median(razmiki))
    prag = mediana_razmika * 0.7
 
    print(f"    Mediana razmika: {mediana_razmika:.0f}px, prag: {prag:.0f}px")
    
    celice = []
    for i, razmik in enumerate(razmiki):
        if razmik >= prag:
            y1 = horiz_y[i]
            y2 = horiz_y[i + 1]
 
            for j in range(len(vert_x) - 1):
                x1 = vert_x[j]
                x2 = vert_x[j + 1]
                w = x2 - x1
                h = y2 - y1
 
                if w >= MIN_SIRINA and h >= MIN_VISINA:
                    celice.append((x1, y1, w, h))
 
    return celice
 
 
def najdi_celice_mreze(slika_gray: np.ndarray) -> list:
    orig_visina, orig_sirina = slika_gray.shape
 
    odmik_y_orig = int(orig_visina * PRESKOK_GLAVE)
    slika_brez_glave = slika_gray[odmik_y_orig:, :]
    print(f"    Preskok glave: zgornjih {int(PRESKOK_GLAVE*100)}% slike ({odmik_y_orig}px)")
 
    slika_obdelana = predobdelaj_sliko(slika_brez_glave)
    visina, sirina = slika_obdelana.shape
 
    horiz_y, vert_x, horiz_mapa, vert_mapa = zaznej_mrejo_s_hough(slika_obdelana)
 
    print(f"    Zaznane horizontalne črte: {len(horiz_y)}")
    print(f"    Zaznane vertikalne črte: {len(vert_x)}")
 
    horiz_y, vert_x = filtriraj_in_popravi_mrejo(horiz_y, vert_x, visina, sirina)
 
    print(f"    Po filtriranju - H: {len(horiz_y)}, V: {len(vert_x)}")
 
    rokopisne = sestavi_rokopisne_celice(horiz_y, vert_x, visina, sirina)
 
    print(f"    Zaznanih rokopisnih celic: {len(rokopisne)}")
 
    razmerje_visina = orig_visina - odmik_y_orig
    faktor_x = orig_sirina / sirina
    faktor_y = razmerje_visina / visina
 
    rokopisne = [
        (int(x * faktor_x),
         int(y * faktor_y) + odmik_y_orig,
         int(w * faktor_x),
         int(h * faktor_y))
        for x, y, w, h in rokopisne
    ]
 
    return rokopisne
 
 
def shrani_debug_sliko(slika_gray: np.ndarray, celice: list, pot: Path):
    debug = cv2.cvtColor(slika_gray, cv2.COLOR_GRAY2BGR)
 
    for i, (x, y, w, h) in enumerate(celice):
        barva = (0, 200, 0)
        cv2.rectangle(debug, (x, y), (x + w, y + h), barva, 2)
        cv2.putText(
            debug, str(i + 1), (x + 5, y + 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, barva, 2
        )
 
    debug_pot = pot.parent / f"DEBUG_{pot.name}"
    cv2.imwrite(str(debug_pot), debug)
    print(f"    Debug slika shranjena: {debug_pot.name}")
 

def _ustvari_unikatno_pot(osnovna_pot: Path) -> Path:
    """Pomožna funkcija za dodajanje _2, _3, če datoteka že obstaja."""
    if not osnovna_pot.exists():
        return osnovna_pot
    
    stevec = 2
    nova_pot = osnovna_pot.parent / f"{osnovna_pot.stem}_{stevec}{osnovna_pot.suffix}"
    while nova_pot.exists():
        stevec += 1
        nova_pot = osnovna_pot.parent / f"{osnovna_pot.stem}_{stevec}{osnovna_pot.suffix}"
    return nova_pot


def izrezi_in_shrani(slika_pil: Image.Image, celice: list,
                     izhodna_mapa: Path, skupna_mapa: Path, ime_datoteke: str,
                     slika_gray: np.ndarray = None):
    shranjeno = 0
 
    for i, (x, y, w, h) in enumerate(celice):
        if i >= len(VRSTNI_RED_MAP):
            print(f"  WARN: Celica {i+1} presega število map – preskočena.")
            break
 
        rob_x = int(w * OBREZI_ROB)
        rob_y = int(h * OBREZI_ROB)
 
        x1 = max(0, x + rob_x)
        y1 = max(0, y + rob_y)
        x2 = min(slika_pil.width, x + w - rob_x)
        y2 = min(slika_pil.height, y + h - rob_y)
 
        if x2 <= x1 or y2 <= y1:
            continue
 
        # 1. Izrez originalne celice
        izrez = slika_pil.crop((x1, y1, x2, y2))
 
        # 2. Pretvorba v sivinsko sliko (Grayscale)
        izrez = izrez.convert("L")
        
        # 3. Sprememba velikosti na točno 28x28 pikslov
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.LANCZOS
            
        izrez = izrez.resize((28, 28), resample_filter)
 
        ime_mape = VRSTNI_RED_MAP[i]
        osnova = Path(ime_datoteke).stem
        bazno_ime = f"{ime_mape}_{osnova}_celica{i+1:02d}.png"

   
        ciljna_mapa_pod = izhodna_mapa / ime_mape
        ciljna_mapa_pod.mkdir(parents=True, exist_ok=True)
        pot_izhoda_pod = _ustvari_unikatno_pot(ciljna_mapa_pod / bazno_ime)
        izrez.save(pot_izhoda_pod, "PNG", optimize=False)

    
        pot_izhoda_skupaj = _ustvari_unikatno_pot(skupna_mapa / bazno_ime)
        izrez.save(pot_izhoda_skupaj, "PNG", optimize=False)
 
        shranjeno += 1
 
    print(f"  ✓ Shranjeno {shranjeno} celic (28x28) v podmape in v '{skupna_mapa.name}'.")
    return shranjeno
 
 
def obdelaj_mapo(vhodna: Path, izhodna: Path, skupna: Path, debug: bool = True):
    slike = [p for p in vhodna.iterdir() if p.suffix.lower() in FORMATI]
 
    if not slike:
        print("  Napaka: V vhodni mapi ni podprtih slik.")
        return
 
    print(f"\nNajdeno slik: {len(slike)}\n")
 
    skupaj_shranjeno = 0
 
    for pot in sorted(slike):
        print(f"\n{'─'*50}")
        print(f"Obdelujem: {pot.name}")
 
        slika_cv = cv2.imread(str(pot), cv2.IMREAD_GRAYSCALE)
        if slika_cv is None:
            print("  Napaka pri branju → preskočeno.")
            continue
 
        slika_pil = Image.open(pot).convert("RGB")
        print(f"  Resolucija: {slika_cv.shape[1]}×{slika_cv.shape[0]} px")
 
        celice = najdi_celice_mreze(slika_cv)
        print(f"  → Zaznanih rokopisnih celic: {len(celice)}")
 
        if len(celice) == 0:
            print("  ⚠ Mreža ni bila zaznana – preskočeno.")
            continue
 
        if len(celice) != len(VRSTNI_RED_MAP):
            print(f"  ⚠ Pričakovano {len(VRSTNI_RED_MAP)} celic, zaznano {len(celice)}")
 
        if debug:
            shrani_debug_sliko(slika_cv, celice, izhodna / pot.name)
 
        n = izrezi_in_shrani(slika_pil, celice, izhodna, skupna, pot.name, slika_gray=slika_cv)
        skupaj_shranjeno += n
 
    print(f"\n{'═'*50}")
    print(f"  Skupaj obdelanih celic: {skupaj_shranjeno}")
    print("  Končano!")
 
 
# ── MAIN ─────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    print("═" * 50)
    print("  Izrezovalnik mreže iz skeniranih obrazcev v5")
    print("═" * 50)
 
    if VHODNA_MAPA:
        vhod = Path(VHODNA_MAPA)
    else:
        vhod = Path(input("\nPot do VHODNE mape:\n> ").strip())
 
    if not vhod.exists():
        print(f"  Napaka: Vhodna mapa ne obstaja: {vhod}")
        sys.exit(1)
 
    if IZHODNA_MAPA:
        izhod = Path(IZHODNA_MAPA)
    else:
        izhod = Path(input("\nPot do IZHODNE mape (podmape):\n> ").strip())

    if SKUPNA_MAPA:
        skupna = Path(SKUPNA_MAPA)
    else:
        skupna = Path(input("\nPot do SKUPNE mape:\n> ").strip())
 
    izhod.mkdir(parents=True, exist_ok=True)
    skupna.mkdir(parents=True, exist_ok=True)
 
    print(f"\nVhod:          {vhod.resolve()}")
    print(f"Izhod (mape):  {izhod.resolve()}")
    print(f"Izhod (vse):   {skupna.resolve()}")
 
    debug_vhod = input("\nShrani debug slike z označenimi celicami? (d/n) [d]: ").strip().lower()
    debug = debug_vhod != "n"
 
    obdelaj_mapo(vhod, izhod, skupna, debug=debug)