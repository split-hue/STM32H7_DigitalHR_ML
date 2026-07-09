# Analiza modelov za prepoznavo rokopisnih slovenskih velikih tiskanih črk na vgrajenem sistemu

> Projekt je del **Diplomske naloge** in obravnava razvoj in primerjavo modelov za prepoznavo rokopisnih slovenskih velikih tiskanih črk na vgrajenem sistemu STM32H750B-DK.

Za zbiranje učnih podatkov je bila razvita namenska aplikacija, ki beleži tako slike posameznih črk kot podatke o potezah črk. Poleg tega je bil zbran ločen nabor podatkov z ročno napisanimi črkami na papirju, ki so bile nato optično prebrane. Na podlagi obeh naborov podatkov je bilo naučenih več modelov z različnimi vhodi. Modeli so bili posebej nameščeni na vezje STM32H750B-DK in ovrednoteni pod enakimi pogoji.
Rezultati kažejo, da modeli, ki temeljijo na podatkih o potezah, dosegajo višjo natančnost v primerjavi z modeli, ki za vhod uporabljajo slike črk.


> ***Ostalo gradivo je shranjeno v mapah z imenom: JUPY (Jupyter notebooks za učenje modelov), MODEL (vsi končni izvoženi modeli), DATASET (primeri podatkov v podatkovnih zbirkah), REZ_MODEL (rezultati posameznih modelov)***
