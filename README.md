# Pràctica 1: Desmuntant la Mentida Visual

**Assignatura:** Modelització i Visualització de Dades (URV).

**Contigut:** Redisseny crític, modelització i programació de la interactivitat d'un *junk chart* real.


## Estructura

```
.
├── docs/
│   └── nova-practica-miv.pdf      # enunciat original de la pràctica
├── data/
│   └── pressupost_generalitat_2003_2024.csv   # sèrie reconstruïda 2003–2024
├── src/
│   ├── build_dataset.py           # reconstrucció de la sèrie (API + Idescat + IPC)
│   └── plot_design.py             # redisseny interactiu (Streamlit + Plotly)
├── report/
│   ├── main.tex                   # informe (font)
│   ├── main.pdf                   # informe (compilat)
│   └── img/                       # captures del gràfic original i del redisseny
├── requirements.txt
└── README.md
```

## Com reproduir-ho

```bash
pip install -r requirements.txt

# Regenera data/pressupost_generalitat_2003_2024.csv amb una crida en directe
# a l'API oberta de transparenciacatalunya.cat (cal connexió a internet)
python3 src/build_dataset.py

# Obre l'aplicació interactiva del redisseny al navegador
streamlit run src/plot_design.py
```

