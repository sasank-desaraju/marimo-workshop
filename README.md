# Marimo at UF: reactive notebooks from the laptop to HiPerGator

Materials for a two-part live workshop on [marimo](https://marimo.io)
notebooks, run with UF Research Computing.

- **When:** Thursday, October 22, 2026, 10:40 AM to noon ET
- **Where:** Zoom
- **Presenters:** Sasank Desaraju and Piyush Chaudhari.

marimo is a reactive Python notebook: each notebook is a plain `.py` file,
cells re-run when the values they depend on change, and the same file can be
edited as a notebook, run as a script, served as an app, or tested with
pytest. The first part of the workshop introduces marimo on your own machine,
including its SQL cells. The second part shows how to use the same notebooks
for scientific work on HiPerGator (HPG), UF's supercomputer: getting marimo
running through Open OnDemand, running notebooks as scripts and Slurm jobs,
and watching results come in while a job runs.

## Part 1: Marimo 101, local use, and SQL (Piyush Chaudhari)

Reactivity, notebooks as Python files, UI elements, layout, interactive
charts, and SQL cells (`mo.sql`) against a synthetic OMOP CDM database in
DuckDB. The same lesson is given as a Quarto slide deck, a marimo notebook,
and a Jupyter notebook.

- Materials: https://github.com/pc-piyush/F26_Marimo (in `PC/`)
- Slides: https://pc-piyush.github.io/F26_Marimo/PC/

## Part 2: Marimo on HiPerGator for scientific work (Sasank Desaraju)

Running marimo on HPG through Open OnDemand (the Marimo app, Jupyter, and an
OOD Desktop with a VS Code tunnel), then a small MNIST-1D pipeline: preprocess
in a notebook and from the CLI, test the dataset with pytest, train as a Slurm
job, and watch results come in with auto-refresh. A standalone CPU fallback
notebook runs on any laptop.

- Materials, setup, and commands: [`hpg/README.md`](hpg/README.md)

## Repository layout

```
hpg/             Part 2: HiPerGator notebooks, scripts, and setup (see hpg/README.md)
README.md        this overview
CITATION.cff     citation metadata for the whole workshop
LICENSE          MIT
```

Part 1 materials are in Piyush Chaudhari's repo,
https://github.com/pc-piyush/F26_Marimo (in `PC/`), for now.

## How to cite

If you use these materials, please cite them using the metadata in
[`CITATION.cff`](CITATION.cff). On GitHub, the "Cite this repository" button
on the repo page is built from that file. Sasank Desaraju and Piyush
Chaudhari contributed equally.

## License

Code is MIT licensed (see `LICENSE`).
