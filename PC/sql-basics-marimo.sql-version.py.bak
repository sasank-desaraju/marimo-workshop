# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo[sql]>=0.23.16",
#     "duckdb",
#     "pandas",
#     "numpy",
#     "altair",
# ]
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Marimo 101: SQL on OMOP")


@app.cell(hide_code=True)
def _():
    import sys
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd
    import altair as alt
    import duckdb
    return Path, alt, duckdb, mo, np, pd, sys


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Marimo 101
    ### A reactive walkthrough of SQL queries, as a native marimo notebook

    This is one of three versions of the same lesson, all built on the same OMOP data and the same queries:

    | Version | File | How it runs |
    |---|---|---|
    | **Quarto deck** | `sql-basics.qmd` | reveal.js slides; marimo cells run as *islands* in the browser |
    | **Jupyter notebook** | `sql-basics-jupyter.ipynb` | an IPython kernel, with ipywidgets callbacks; you re-run cells by hand |
    | **marimo notebook** *(this one)* | `sql-basics-marimo.py` | a reactive Python file you can open locally, on molab, or in the browser (WASM) |

    Look for the 🟢 **Native only** notes. They mark features that the slides can't show or that Jupyter needs extra code to match.
    """)
    return


@app.cell(hide_code=True)
def _(mo, sys):
    _mode = mo.app_meta().mode
    _wasm = sys.platform == "emscripten"
    if _wasm:
        _where, _kind = (
            "**in your browser via Pyodide (WebAssembly)**: a molab WASM preview, marimo.app, "
            "`marimo export html-wasm`, or a Quarto island. No server is involved.",
            "info",
        )
    elif _mode == "edit":
        _where, _kind = (
            "**in the native marimo editor on a real Python kernel**, either `marimo edit` "
            "on your machine or a molab session. Every cell is editable.",
            "success",
        )
    elif _mode == "run":
        _where, _kind = (
            "**as a marimo app** (`marimo run`, or molab's app view). The code is hidden but "
            "the app is still reactive.",
            "success",
        )
    else:
        _where, _kind = (
            f"**as a plain Python script** (mode = `{_mode}`). Every cell runs once, top to bottom.",
            "warn",
        )
    mo.callout(
        mo.md(
            f"**Where is this running?** {_where}\n\n"
            f"`marimo {mo.__version__}` · `Python {sys.version.split()[0]}` · "
            f"`platform = {sys.platform}` · `mode = {_mode}`"
        ),
        kind=_kind,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    _order = [("FROM", "#002657"), ("JOIN … ON", "#6A2A60"), ("WHERE", "#C63A0E"),
              ("GROUP BY", "#22884C"), ("HAVING", "#7A5C00"), ("SELECT", "#0021A5"),
              ("ORDER BY", "#D32737"), ("LIMIT", "#5F6168")]
    _chips = "".join(
        f'<div style="background:{c};color:#fff;font:600 13px \'JetBrains Mono\',ui-monospace,monospace;'
        f'padding:4px 8px;border-radius:4px;margin:3px 0">{i}&nbsp;&nbsp;{k}</div>'
        for i, (k, c) in enumerate(_order, 1)
    )
    mo.sidebar([
        mo.md("### Marimo 101"),
        mo.md("**SQL evaluation order**"),
        mo.Html(_chips),
        mo.md("<small>🟢 `mo.sidebar` is native-only. In the Quarto deck, the slide layout takes its place.</small>"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Learning SQL with OMOP

    Every OMOP extract uses **the same tables and column names**, so a query written here can run against any OMOP dataset at any institution.

    - Clinical facts live in *event tables*
    - Their meaning lives in **`concept`**, the vocabulary table

    Most of the queries we'll see **(1)** filter an event table, **(2)** join to `person`, and **(3)** join to `concept` to get readable names.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.mermaid(
        """
    erDiagram
        PERSON ||--o{ VISIT_OCCURRENCE : has
        PERSON ||--o{ CONDITION_OCCURRENCE : has
        PERSON ||--o{ DRUG_EXPOSURE : has
        PERSON ||--o{ MEASUREMENT : has
        VISIT_OCCURRENCE ||--o{ CONDITION_OCCURRENCE : "recorded during"
        CONCEPT ||--o{ CONDITION_OCCURRENCE : "condition_concept_id"
        CONCEPT ||--o{ DRUG_EXPOSURE : "drug_concept_id"
        CONCEPT ||--o{ MEASUREMENT : "measurement_concept_id"
        PERSON {
            int person_id PK
            int gender_concept_id FK
            int year_of_birth
        }
        CONDITION_OCCURRENCE {
            int person_id FK
            int condition_concept_id FK
            date condition_start_date
        }
        CONCEPT {
            int concept_id PK
            string concept_name
            string domain_id
        }
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The dataset

    - A synthetic OMOP CDM subset in **DuckDB**. If `omop.duckdb` sits next to this file, the notebook opens it; otherwise (on molab or in WASM) the next cell rebuilds the same seeded tables in memory
    - Concept IDs are real standard concepts (SNOMED, RxNorm, LOINC)
    - People, dates and values are simulated

    🟢 **Native only:** `con` is a global DuckDB connection, so marimo lists its tables and columns in the **Data sources** panel (left sidebar). Click a table to generate a SQL cell for it.
    """)
    return


@app.cell
def _(Path, duckdb, mo, np, pd):
    # ---------------------------------------------------------------
    # Synthetic OMOP CDM v5.4 subset stored in omop.duckdb.
    # Concept IDs are real standard OMOP concepts; people, dates and
    # values are simulated. Rebuild with: uv run build_omop_db.py
    # ---------------------------------------------------------------
    DB_PATH = (mo.notebook_dir() or Path.cwd()) / "omop.duckdb"
    if DB_PATH.exists():
        con = duckdb.connect(str(DB_PATH), read_only=True)
    else:
        # On molab / in WASM omop.duckdb isn't available, so rebuild the
        # same seeded tables in memory. Keep in sync with build_omop_db.py.
        _rng = np.random.default_rng(42)
        _N = 1200
        _t0 = pd.Timestamp("2016-01-01")
        _span = (pd.Timestamp("2024-12-31") - _t0).days

        _concept = pd.DataFrame(
            [
                (8507, "MALE", "Gender", "Gender"),
                (8532, "FEMALE", "Gender", "Gender"),
                (8527, "White", "Race", "Race"),
                (8516, "Black or African American", "Race", "Race"),
                (8515, "Asian", "Race", "Race"),
                (38003563, "Hispanic or Latino", "Ethnicity", "Ethnicity"),
                (38003564, "Not Hispanic or Latino", "Ethnicity", "Ethnicity"),
                (9201, "Inpatient Visit", "Visit", "Visit"),
                (9202, "Outpatient Visit", "Visit", "Visit"),
                (9203, "Emergency Room Visit", "Visit", "Visit"),
                (201826, "Type 2 diabetes mellitus", "Condition", "SNOMED"),
                (320128, "Essential hypertension", "Condition", "SNOMED"),
                (317576, "Coronary arteriosclerosis", "Condition", "SNOMED"),
                (255573, "Chronic obstructive lung disease", "Condition", "SNOMED"),
                (46271022, "Chronic kidney disease", "Condition", "SNOMED"),
                (433736, "Obesity", "Condition", "SNOMED"),
                (4329847, "Myocardial infarction", "Condition", "SNOMED"),
                (440383, "Depressive disorder", "Condition", "SNOMED"),
                (197320, "Acute renal failure syndrome", "Condition", "SNOMED"),
                (1503297, "metformin", "Drug", "RxNorm"),
                (1308216, "lisinopril", "Drug", "RxNorm"),
                (1545958, "atorvastatin", "Drug", "RxNorm"),
                (1112807, "aspirin", "Drug", "RxNorm"),
                (1307046, "metoprolol", "Drug", "RxNorm"),
                (1332418, "amlodipine", "Drug", "RxNorm"),
                (3004410, "Hemoglobin A1c/Hemoglobin.total in Blood", "Measurement", "LOINC"),
                (3016723, "Creatinine [Mass/volume] in Serum or Plasma", "Measurement", "LOINC"),
                (3004249, "Systolic blood pressure", "Measurement", "LOINC"),
            ],
            columns=["concept_id", "concept_name", "domain_id", "vocabulary_id"],
        )

        # person -------------------------------------------------------------
        _person = pd.DataFrame({
            "person_id": np.arange(1, _N + 1),
            "gender_concept_id": _rng.choice([8507, 8532], _N, p=[.48, .52]),
            "year_of_birth": _rng.integers(1935, 2006, _N),
            "month_of_birth": _rng.integers(1, 13, _N),
            "race_concept_id": _rng.choice([8527, 8516, 8515, 0], _N, p=[.6, .2, .08, .12]),
            "ethnicity_concept_id": _rng.choice([38003563, 38003564], _N, p=[.25, .75]),
        })
        _age = dict(zip(_person.person_id, 2024 - _person.year_of_birth))

        # visit_occurrence ---------------------------------------------------
        _nv = (_rng.poisson(4, _N) + 1).astype(np.intp)  # np.repeat needs intp (int32 in WASM)
        _vp = np.repeat(_person.person_id.values, _nv)
        _V = len(_vp)
        _vtype = _rng.choice([9201, 9202, 9203], _V, p=[.12, .75, .13])
        _vstart = _t0 + pd.to_timedelta(_rng.integers(0, _span, _V), unit="D")
        _los = np.where(_vtype == 9201, _rng.integers(1, 11, _V), 0)
        _visit = pd.DataFrame({
            "visit_occurrence_id": np.arange(1, _V + 1),
            "person_id": _vp,
            "visit_concept_id": _vtype,
            "visit_start_date": _vstart,
            "visit_end_date": _vstart + pd.to_timedelta(_los, unit="D"),
        })
        _by_person = {p: g for p, g in _visit.groupby("person_id")}

        # condition_occurrence ------------------------------------------------
        _base = {201826: .16, 320128: .28, 317576: .09, 255573: .07, 46271022: .06,
                 433736: .15, 4329847: .03, 440383: .12, 197320: .04}
        _crow = []
        for _pid, _g in _by_person.items():
            _scale = 0.35 + _age[_pid] / 55
            for _cid, _p in _base.items():
                if _rng.random() < min(_p * _scale, .85):
                    _v = _g.iloc[_rng.integers(0, len(_g))]
                    _crow.append((_pid, _cid, _v.visit_start_date, _v.visit_occurrence_id))
        _cond = pd.DataFrame(_crow, columns=["person_id", "condition_concept_id",
                                             "condition_start_date", "visit_occurrence_id"])
        _cond.insert(0, "condition_occurrence_id", np.arange(1, len(_cond) + 1))
        _has = _cond.groupby("person_id").condition_concept_id.apply(set).to_dict()

        # drug_exposure -------------------------------------------------------
        _drow = []
        for _pid, _g in _by_person.items():
            _cs = _has.get(_pid, set())
            if 201826 in _cs and _rng.random() < .72:
                _d0 = _cond[(_cond.person_id == _pid) & (_cond.condition_concept_id == 201826)].condition_start_date.iloc[0]
                _drow.append((_pid, 1503297, _d0 + pd.Timedelta(days=int(_rng.integers(0, 240)))))
            if 320128 in _cs:
                for _dc in (1308216, 1332418):
                    if _rng.random() < .45:
                        _drow.append((_pid, _dc, _g.visit_start_date.iloc[_rng.integers(0, len(_g))]))
            if _cs & {317576, 4329847}:
                for _dc in (1545958, 1112807, 1307046):
                    if _rng.random() < .6:
                        _drow.append((_pid, _dc, _g.visit_start_date.iloc[_rng.integers(0, len(_g))]))
        _drug = pd.DataFrame(_drow, columns=["person_id", "drug_concept_id", "drug_exposure_start_date"])
        _drug["days_supply"] = _rng.choice([30, 90], len(_drug))
        _drug["drug_exposure_end_date"] = _drug.drug_exposure_start_date + pd.to_timedelta(_drug.days_supply, unit="D")
        _drug.insert(0, "drug_exposure_id", np.arange(1, len(_drug) + 1))

        # measurement ---------------------------------------------------------
        _mrow = []
        for _v in _visit.itertuples():
            _cs = _has.get(_v.person_id, set())
            if _rng.random() < .35:
                _a1c = _rng.normal(7.9, 1.3) if 201826 in _cs else _rng.normal(5.4, .35)
                _mrow.append((_v.person_id, 3004410, _v.visit_start_date, round(max(_a1c, 4.0), 1), "%"))
            if _rng.random() < .6:
                _cr = _rng.lognormal(0, .2) * (1.9 if 197320 in _cs and _rng.random() < .5 else 1.0)
                _cr *= 1.35 if 46271022 in _cs else 1.0
                _mrow.append((_v.person_id, 3016723, _v.visit_start_date, round(_cr, 2), "mg/dL"))
            if _rng.random() < .8:
                _sbp = _rng.normal(141 if 320128 in _cs else 122, 13)
                _mrow.append((_v.person_id, 3004249, _v.visit_start_date, round(_sbp), "mmHg"))
        _meas = pd.DataFrame(_mrow, columns=["person_id", "measurement_concept_id",
                                             "measurement_date", "value_as_number", "unit_source_value"])
        _meas.insert(0, "measurement_id", np.arange(1, len(_meas) + 1))

        # load into DuckDB with proper DATE columns ---------------------------
        con = duckdb.connect()
        for _name, _df in {"person": _person, "visit_occurrence": _visit,
                           "condition_occurrence": _cond, "drug_exposure": _drug,
                           "measurement": _meas, "concept": _concept}.items():
            con.register("_tmp", _df)
            _cols = ", ".join(
                f"CAST({c} AS DATE) AS {c}" if c.endswith("_date") else c for c in _df.columns
            )
            con.execute(f"CREATE TABLE {_name} AS SELECT {_cols} FROM _tmp")
            con.unregister("_tmp")


    def run(q):
        """Run SQL against the OMOP connection and return a pandas DataFrame."""
        return con.execute(q).df()


    def show_sql(q):
        return mo.md(f"```sql\n{q.strip()}\n```")


    CLAUSE = {"select": "#0021A5", "from": "#002657", "where": "#C63A0E",
              "join": "#6A2A60", "group": "#22884C", "having": "#7A5C00",
              "order": "#D32737", "window": "#343741",
              "ink": "#1A1A1A", "muted": "#5F6168"}


    def styled(chart, w=520, h=300):
        return (chart.properties(width=w, height=h)
                .configure(font="Georgia")
                .configure_view(stroke=None)
                .configure_axis(labelColor=CLAUSE["ink"], titleColor=CLAUSE["muted"],
                                gridColor="#E6E7E6", domainColor="#C7C9C8",
                                labelFontSize=13, titleFontSize=13)
                .configure_legend(labelFontSize=13, titleFontSize=13))
    return CLAUSE, DB_PATH, con, run, show_sql, styled


@app.cell(hide_code=True)
def _(CLAUSE, DB_PATH, alt, mo, run, styled):
    _counts = run("""
        SELECT 'person' AS table_name, COUNT(*) AS n_rows FROM person
        UNION ALL SELECT 'visit_occurrence', COUNT(*) FROM visit_occurrence
        UNION ALL SELECT 'condition_occurrence', COUNT(*) FROM condition_occurrence
        UNION ALL SELECT 'drug_exposure', COUNT(*) FROM drug_exposure
        UNION ALL SELECT 'measurement', COUNT(*) FROM measurement
        UNION ALL SELECT 'concept', COUNT(*) FROM concept
    """)
    _bars = alt.Chart(_counts).mark_bar(color=CLAUSE["from"], cornerRadiusEnd=3).encode(
        x=alt.X("n_rows:Q", title="rows"),
        y=alt.Y("table_name:N", sort="-x", title=None),
        tooltip=["table_name", alt.Tooltip("n_rows:Q", format=",")],
    )
    _labels = _bars.mark_text(align="left", dx=4, color=CLAUSE["ink"]).encode(
        text=alt.Text("n_rows:Q", format=","))
    mo.vstack([
        mo.md(f"<small>Source: `{DB_PATH.name}`</small>" if DB_PATH.exists()
              else "<small>Source: rebuilt in memory (seed 42)</small>"),
        styled(_bars + _labels, w=520, h=220),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SQL query syntax

    You write clauses in one order. The database evaluates them in another, which explains most beginner errors.
    The sidebar keeps the evaluation order in view while you scroll.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.Html("""
    <svg viewBox="0 0 1180 430" width="100%" role="img" aria-label="Written clause order versus logical evaluation order">
      <style>
        .lab { font: 700 20px 'JetBrains Mono', monospace; fill: #fff; }
        .hd  { font: 700 22px Georgia, serif; fill: #1A1A1A; }
        .note{ font: 17px Georgia, serif; fill: #5F6168; }
        .ln  { stroke: #9A9C9B; stroke-width: 2; fill: none; }
      </style>
      <text class="hd" x="40" y="30">How you write it</text>
      <text class="hd" x="640" y="30">How the database runs it</text>
      <g>
        <rect x="40"  y="50"  width="260" height="40" rx="5" fill="#0021A5"/><text class="lab" x="56" y="77">SELECT</text>
        <rect x="40"  y="97"  width="260" height="40" rx="5" fill="#002657"/><text class="lab" x="56" y="124">FROM</text>
        <rect x="40"  y="144" width="260" height="40" rx="5" fill="#6A2A60"/><text class="lab" x="56" y="171">JOIN … ON</text>
        <rect x="40"  y="191" width="260" height="40" rx="5" fill="#C63A0E"/><text class="lab" x="56" y="218">WHERE</text>
        <rect x="40"  y="238" width="260" height="40" rx="5" fill="#22884C"/><text class="lab" x="56" y="265">GROUP BY</text>
        <rect x="40"  y="285" width="260" height="40" rx="5" fill="#7A5C00"/><text class="lab" x="56" y="312">HAVING</text>
        <rect x="40"  y="332" width="260" height="40" rx="5" fill="#D32737"/><text class="lab" x="56" y="359">ORDER BY</text>
        <rect x="40"  y="379" width="260" height="40" rx="5" fill="#5F6168"/><text class="lab" x="56" y="406">LIMIT</text>
      </g>
      <g>
        <rect x="640" y="50"  width="260" height="40" rx="5" fill="#002657"/><text class="lab" x="656" y="77">1  FROM</text>
        <rect x="640" y="97"  width="260" height="40" rx="5" fill="#6A2A60"/><text class="lab" x="656" y="124">2  JOIN … ON</text>
        <rect x="640" y="144" width="260" height="40" rx="5" fill="#C63A0E"/><text class="lab" x="656" y="171">3  WHERE</text>
        <rect x="640" y="191" width="260" height="40" rx="5" fill="#22884C"/><text class="lab" x="656" y="218">4  GROUP BY</text>
        <rect x="640" y="238" width="260" height="40" rx="5" fill="#7A5C00"/><text class="lab" x="656" y="265">5  HAVING</text>
        <rect x="640" y="285" width="260" height="40" rx="5" fill="#0021A5"/><text class="lab" x="656" y="312">6  SELECT</text>
        <rect x="640" y="332" width="260" height="40" rx="5" fill="#D32737"/><text class="lab" x="656" y="359">7  ORDER BY</text>
        <rect x="640" y="379" width="260" height="40" rx="5" fill="#5F6168"/><text class="lab" x="656" y="406">8  LIMIT</text>
      </g>
      <path class="ln" d="M300,70 C470,70 470,305 640,305"/>
      <path class="ln" d="M300,117 C470,117 470,70 640,70"/>
      <path class="ln" d="M300,164 C470,164 470,117 640,117"/>
      <path class="ln" d="M300,211 C470,211 470,164 640,164"/>
      <path class="ln" d="M300,258 C470,258 470,211 640,211"/>
      <path class="ln" d="M300,305 C470,305 470,258 640,258"/>
      <path class="ln" d="M300,352 L640,352"/>
      <path class="ln" d="M300,399 L640,399"/>
      <text class="note" x="920" y="310">Aliases are born here,</text>
      <text class="note" x="920" y="332">so WHERE can’t see them</text>
    </svg>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SELECT and FROM

    - `FROM` names the table
    - `SELECT` picks the columns you want back
    - `LIMIT` keeps the preview small while you explore
    - Avoid `SELECT *` in real extracts since OMOP tables are wide, and naming columns documents intent

    🟢 **Native only:** the next cell is a real **SQL cell**. In the deck it is a read-only ` ```{sql .marimo} ` block; in Jupyter it is a Python string passed to `con.execute()`.
    Here you can edit it, choose its engine from the dropdown, and its result is stored in the Python variable **`person_preview`**.
    """)
    return


@app.cell
def _(con, mo):
    person_preview = mo.sql(
        f"""
        SELECT person_id,
               gender_concept_id,
               year_of_birth,
               race_concept_id
        FROM person
        LIMIT 6
        """,
        engine=con
    )
    return (person_preview,)


@app.cell(hide_code=True)
def _(mo, person_preview):
    mo.md(f"""
    The SQL cell above returned a **{len(person_preview)}-row** `{type(person_preview).__module__.split('.')[0]}` DataFrame.
    Change its `LIMIT` and this sentence reruns by itself. SQL cells and Python cells share one reactive graph.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## WHERE filters rows

    Move the controls. The SQL cell interpolates their values with `{...}`, like an f-string, and reruns on its own.

    - `BETWEEN` is inclusive on both ends
    - Filtering on `gender_concept_id`, not a text label, is the OMOP way
    """)
    return


@app.cell
def _(mo):
    yob = mo.ui.range_slider(1935, 2005, value=[1950, 1975], step=1,
                             label="Year of birth", show_value=True, full_width=True)
    sex_pick = mo.ui.dropdown({"Anyone": 0, "Female (8532)": 8532, "Male (8507)": 8507},
                              value="Anyone", label="Sex")
    mo.hstack([yob, sex_pick], widths=[3, 1], gap=2, align="end")
    return sex_pick, yob


@app.cell
def _(con, mo, sex_pick, yob):
    where_df = mo.sql(
        f"""
        SELECT person_id, gender_concept_id, year_of_birth
        FROM person
        WHERE year_of_birth BETWEEN {yob.value[0]} AND {yob.value[1]}
          AND ({sex_pick.value} = 0 OR gender_concept_id = {sex_pick.value})
        """,
        engine=con
    )
    return (where_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    🟢 **Native only: SQL over a Python DataFrame.** The next SQL cell has no engine. It queries **`where_df`**, the *result of the previous SQL cell*, as if it were a table.
    You can chain steps like CTEs and still inspect each one.
    """)
    return


@app.cell
def _(mo, where_df):
    _df = mo.sql(
        f"""
        SELECT (year_of_birth // 10) * 10 AS birth_decade,
               COUNT(*)                   AS people
        FROM where_df
        GROUP BY 1
        ORDER BY 1
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ORDER BY and LIMIT

    Without `ORDER BY`, row order is not guaranteed, so `LIMIT` alone returns an arbitrary sample.
    """)
    return


@app.cell
def _(mo):
    sort_col = mo.ui.dropdown(["year_of_birth", "person_id", "month_of_birth"],
                              value="year_of_birth", label="Sort by")
    sort_dir = mo.ui.radio(["ASC", "DESC"], value="DESC", label="Direction", inline=True)
    top_n = mo.ui.number(1, 25, value=8, label="LIMIT")
    mo.hstack([sort_col, sort_dir, top_n], justify="start", gap=2)
    return sort_col, sort_dir, top_n


@app.cell
def _(mo, run, show_sql, sort_col, sort_dir, top_n):
    order_sql = f"""
    SELECT person_id, year_of_birth, month_of_birth
    FROM person
    ORDER BY {sort_col.value} {sort_dir.value}
    LIMIT {top_n.value}
    """
    mo.hstack([show_sql(order_sql), mo.ui.table(run(order_sql), page_size=8, selection=None)],
              widths=[1, 1], gap=2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## JOIN turns IDs into meaning

    - Event tables store integers
    - `concept` holds the names
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.Html("""
    <svg viewBox="0 0 520 250" width="100%" style="max-width:520px" role="img" aria-label="Joining condition_occurrence to concept on concept_id">
      <style>
        .t { font: 15px 'JetBrains Mono', monospace; fill: #1A1A1A; }
        .th { font: 700 15px 'JetBrains Mono', monospace; fill: #fff; }
      </style>
      <rect x="0" y="10" width="220" height="30" fill="#002657"/><text class="th" x="10" y="31">condition_occurrence</text>
      <rect x="0" y="40" width="220" height="150" fill="#fff" stroke="#C7C9C8"/>
      <text class="t" x="10" y="68">person_id  12</text>
      <text class="t" x="10" y="98">condition_</text>
      <text class="t" x="10" y="116">concept_id</text>
      <rect x="120" y="96" width="92" height="26" rx="4" fill="#F3E9F1" stroke="#6A2A60"/>
      <text class="t" x="128" y="115">201826</text>
      <text class="t" x="10" y="158">start 2019-03-04</text>
      <rect x="300" y="10" width="220" height="30" fill="#002657"/><text class="th" x="310" y="31">concept</text>
      <rect x="300" y="40" width="220" height="150" fill="#fff" stroke="#C7C9C8"/>
      <rect x="306" y="52" width="92" height="26" rx="4" fill="#F3E9F1" stroke="#6A2A60"/>
      <text class="t" x="314" y="71">201826</text>
      <text class="t" x="310" y="108">Type 2 diabetes</text>
      <text class="t" x="310" y="128">mellitus</text>
      <text class="t" x="310" y="164">SNOMED · Condition</text>
      <path d="M212,109 C260,109 250,65 306,65" stroke="#6A2A60" stroke-width="3" fill="none"/>
      <text class="t" x="0" y="232" style="fill:#6A2A60">ON co.condition_concept_id = c.concept_id</text>
    </svg>
    """)
    return


@app.cell
def _(con, mo):
    _df = mo.sql(
        f"""
        SELECT c.concept_name AS condition,
               COUNT(*)       AS n_records
        FROM condition_occurrence AS co
        JOIN concept AS c
          ON co.condition_concept_id = c.concept_id
        GROUP BY c.concept_name
        ORDER BY n_records DESC
        LIMIT 5
        """,
        engine=con
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    🟢 **Native only: tables are inputs as well as outputs.** The deck sets `selection=None` on every table because a slide has no room for a drill-down.
    Here, **click a condition** and the next cell joins `condition_occurrence` → `drug_exposure` → `concept` for those patients.
    """)
    return


@app.cell
def _(mo, run):
    _cond_counts = run("""
    SELECT c.concept_id,
           c.concept_name               AS condition,
           COUNT(DISTINCT co.person_id) AS patients,
           COUNT(*)                     AS n_records
    FROM condition_occurrence AS co
    JOIN concept AS c
      ON co.condition_concept_id = c.concept_id
    GROUP BY 1, 2
    ORDER BY patients DESC
    """)
    cond_table = mo.ui.table(_cond_counts, selection="single", initial_selection=[0],
                             page_size=9, label="Click a condition")
    cond_table
    return (cond_table,)


@app.cell
def _(CLAUSE, alt, cond_table, mo, run, show_sql, styled):
    mo.stop(len(cond_table.value) == 0, mo.md("*Select a condition above.*"))
    _cid = int(cond_table.value["concept_id"].iloc[0])
    _name = cond_table.value["condition"].iloc[0]
    drill_sql = f"""
    SELECT d.concept_name               AS drug,
           COUNT(DISTINCT de.person_id) AS patients
    FROM condition_occurrence AS co
    JOIN drug_exposure AS de ON co.person_id = de.person_id
    JOIN concept       AS d  ON de.drug_concept_id = d.concept_id
    WHERE co.condition_concept_id = {_cid}
    GROUP BY 1
    ORDER BY 2 DESC
    """
    _dr = run(drill_sql)
    _chart = alt.Chart(_dr).mark_bar(color=CLAUSE["join"], cornerRadiusEnd=3).encode(
        x=alt.X("patients:Q"), y=alt.Y("drug:N", sort="-x", title=None),
        tooltip=["drug", "patients"])
    mo.vstack([
        mo.md(f"#### Drugs recorded for patients with **{_name}**"),
        mo.hstack([show_sql(drill_sql),
                   styled(_chart, w=320, h=max(24 * len(_dr), 60)) if len(_dr) else mo.md("_No drug exposures._")],
                  widths=[1, 1], gap=2),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## INNER, LEFT and ANTI JOINS
    """)
    return


@app.cell
def _(mo):
    join_kind = mo.ui.radio(["INNER JOIN", "LEFT JOIN", "Anti join (LEFT + IS NULL)"],
                            value="INNER JOIN", label="Join type", inline=True)
    join_kind
    return (join_kind,)


@app.cell(hide_code=True)
def _(join_kind, mo):
    # Toy example: 5 people, 4 condition rows. Highlight what survives the join.
    _people = [1, 2, 3, 4, 5]
    _conds = [(1, "HTN"), (1, "T2DM"), (3, "CKD"), (4, "HTN")]
    if join_kind.value == "INNER JOIN":
        _rows = [(p, c) for p, c in _conds]
    elif join_kind.value == "LEFT JOIN":
        _rows = [(p, c) for p in _people for q, c in _conds if q == p] + \
                [(p, "NULL") for p in _people if p not in {q for q, _ in _conds}]
        _rows.sort()
    else:
        _rows = [(p, "NULL") for p in _people if p not in {q for q, _ in _conds}]
    _kept = {p for p, _ in _rows}
    _svg = ['<svg viewBox="0 0 560 250" width="100%" style="max-width:560px" role="img" aria-label="Toy join result">',
            '<style>.t{font:16px "JetBrains Mono",monospace}.h{font:700 15px Georgia,serif;fill:#5F6168}</style>',
            '<text class="h" x="0" y="16">person</text><text class="h" x="130" y="16">condition</text>',
            '<text class="h" x="340" y="16">result</text>']
    for _i, _p in enumerate(_people):
        _on = _p in _kept
        _svg.append(f'<rect x="0" y="{26+_i*40}" width="90" height="32" rx="4" fill="{"#F3E9F1" if _on else "#fff"}" stroke="{"#6A2A60" if _on else "#C7C9C8"}"/>')
        _svg.append(f'<text class="t" x="12" y="{48+_i*40}" fill="{"#1A1A1A" if _on else "#9A9C9B"}">id {_p}</text>')
    for _i, (_p, _c) in enumerate(_conds):
        _on = join_kind.value != "Anti join (LEFT + IS NULL)"
        _svg.append(f'<rect x="130" y="{26+_i*40}" width="150" height="32" rx="4" fill="#fff" stroke="{"#6A2A60" if _on else "#C7C9C8"}"/>')
        _svg.append(f'<text class="t" x="140" y="{48+_i*40}" fill="{"#1A1A1A" if _on else "#9A9C9B"}">{_p} · {_c}</text>')
    for _i, (_p, _c) in enumerate(_rows[:6]):
        _svg.append(f'<rect x="340" y="{26+_i*37}" width="210" height="30" rx="4" fill="#d17ac4"/>')
        _svg.append(f'<text class="t" x="352" y="{47+_i*37}" fill="#fff">{_p} · {_c}</text>')
    _svg.append("</svg>")
    join_toy = mo.Html("".join(_svg))
    return (join_toy,)


@app.cell
def _(join_kind, join_toy, mo, run, show_sql):
    _base_sql = """
    SELECT COUNT(DISTINCT p.person_id) AS people,
           COUNT(*)                    AS result_rows
    FROM person AS p
    {kind} condition_occurrence AS co
      ON p.person_id = co.person_id"""
    if join_kind.value == "INNER JOIN":
        join_sql = _base_sql.format(kind="INNER JOIN")
    elif join_kind.value == "LEFT JOIN":
        join_sql = _base_sql.format(kind="LEFT JOIN")
    else:
        join_sql = _base_sql.format(kind="LEFT JOIN") + "\n    WHERE co.person_id IS NULL"
    _r = run(join_sql)
    mo.hstack([
        join_toy,
        mo.vstack([
            show_sql(join_sql),
            mo.hstack([
                mo.stat(f"{int(_r.people[0]):,}", label="distinct people"),
                mo.stat(f"{int(_r.result_rows[0]):,}", label="rows returned"),
            ], justify="start", gap=2),
            mo.md("An inner join silently drops people with no events. The anti join finds exactly those people."),
        ]),
    ], widths=[1, 1], gap=2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## GROUP BY does aggregation

    - `COUNT(*)` counts records
    - `COUNT(DISTINCT person_id)` counts patients

    In EHR data these differ a lot. 🟢 `mo.ui.tabs` keeps the chart, SQL and raw result together without crowding the page.
    """)
    return


@app.cell
def _(mo):
    domain_pick = mo.ui.radio(
        {"Conditions": ("condition_occurrence", "condition_concept_id"),
         "Drugs": ("drug_exposure", "drug_concept_id"),
         "Visits": ("visit_occurrence", "visit_concept_id")},
        value="Conditions", label="Event table", inline=True)
    count_what = mo.ui.radio(["COUNT(*)", "COUNT(DISTINCT e.person_id)"],
                             value="COUNT(DISTINCT e.person_id)", label="Count", inline=True)
    mo.hstack([domain_pick, count_what], justify="start", gap=3)
    return count_what, domain_pick


@app.cell
def _(CLAUSE, alt, count_what, domain_pick, mo, run, show_sql, styled):
    _tbl, _col = domain_pick.value
    group_sql = f"""
    SELECT c.concept_name, {count_what.value} AS n
    FROM {_tbl} AS e
    JOIN concept AS c ON e.{_col} = c.concept_id
    GROUP BY c.concept_name
    ORDER BY n DESC
    """
    _g = run(group_sql)
    _chart = alt.Chart(_g).mark_bar(color=CLAUSE["group"], cornerRadiusEnd=3).encode(
        x=alt.X("n:Q", title="patients" if "DISTINCT" in count_what.value else "records"),
        y=alt.Y("concept_name:N", sort="-x", title=None),
        tooltip=["concept_name", alt.Tooltip("n:Q", format=",")],
    )
    mo.ui.tabs({
        "Chart": styled(_chart, w=520, h=min(28 * len(_g), 260)),
        "SQL": show_sql(group_sql),
        "Result": mo.ui.table(_g, selection=None),
    })
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## HAVING filters

    - `WHERE` runs before grouping, on rows
    - `HAVING` runs after grouping, on aggregates

    Use this pattern for *high utilisers*, *patients with ≥ 2 diagnosis codes* and similar phenotype rules.
    """)
    return


@app.cell
def _(mo):
    min_visits = mo.ui.slider(1, 15, value=8, label="Minimum visits", show_value=True, full_width=True)
    min_visits
    return (min_visits,)


@app.cell
def _(CLAUSE, alt, min_visits, mo, np, run, show_sql, styled):
    having_sql = f"""
    SELECT person_id, COUNT(*) AS n_visits
    FROM visit_occurrence
    GROUP BY person_id
    HAVING COUNT(*) >= {min_visits.value}
    """
    _h = run(having_sql)
    _dist = run("SELECT person_id, COUNT(*) AS n_visits FROM visit_occurrence GROUP BY person_id")
    _dist["kept"] = np.where(_dist.n_visits >= min_visits.value, "kept by HAVING", "dropped")
    _hist = alt.Chart(_dist).mark_bar().encode(
        x=alt.X("n_visits:O", title="visits per person"),
        y=alt.Y("count():Q", title="people"),
        color=alt.Color("kept:N", scale=alt.Scale(domain=["kept by HAVING", "dropped"],
                                                   range=[CLAUSE["having"], "#DCDDDC"]),
                        legend=alt.Legend(orient="top", title=None)),
    )
    mo.hstack([
        mo.vstack([show_sql(having_sql), mo.stat(f"{len(_h):,}", label="people kept")]),
        styled(_hist, w=380, h=200),
    ], widths=[1, 1], gap=2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Dates: visits over time

    **DuckDB** `date_trunc('year', d)` · **SQL Server** `DATEFROMPARTS(YEAR(d),1,1)` or `DATETRUNC(year, d)`
    """)
    return


@app.cell
def _(mo):
    visit_types = mo.ui.multiselect(
        {"Inpatient": 9201, "Outpatient": 9202, "Emergency": 9203},
        value=["Inpatient", "Emergency"], label="Visit types")
    grain = mo.ui.radio(["year", "quarter"], value="year", label="Grain", inline=True)
    mo.hstack([visit_types, grain], justify="start", gap=3)
    return grain, visit_types


@app.cell
def _(CLAUSE, alt, grain, mo, run, show_sql, styled, visit_types):
    mo.stop(not visit_types.value, mo.md("*Pick at least one visit type.*"))
    _ids = ", ".join(str(v) for v in visit_types.value)
    dates_sql = f"""
    SELECT date_trunc('{grain.value}', v.visit_start_date) AS period,
           c.concept_name AS visit_type,
           COUNT(*) AS n_visits
    FROM visit_occurrence AS v
    JOIN concept AS c ON v.visit_concept_id = c.concept_id
    WHERE v.visit_concept_id IN ({_ids})
    GROUP BY 1, 2
    ORDER BY 1
    """
    _d = run(dates_sql)
    _line = alt.Chart(_d).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("period:T", title=None),
        y=alt.Y("n_visits:Q", title="visits"),
        color=alt.Color("visit_type:N", title=None, legend=alt.Legend(orient="top"),
                        scale=alt.Scale(range=[CLAUSE["order"], CLAUSE["select"], CLAUSE["where"]])),
        tooltip=["period:T", "visit_type", "n_visits"],
    )
    mo.vstack([styled(_line, w=640, h=220), mo.accordion({"Show the SQL": show_sql(dates_sql)})])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Measurements and CASE WHEN

    `CASE WHEN` creates a derived column row by row, which is how most lab-based phenotype flags are built.
    Changing the lab **rebuilds the slider** with a new range and default. One UI element can depend on another, and the reactive graph keeps them in order.
    """)
    return


@app.cell
def _(mo):
    lab_pick = mo.ui.dropdown(
        {"HbA1c (%)": (3004410, 4.0, 13.0, 6.5),
         "Creatinine (mg/dL)": (3016723, 0.3, 4.0, 1.3),
         "Systolic BP (mmHg)": (3004249, 80.0, 190.0, 140.0)},
        value="HbA1c (%)", label="Lab")
    return (lab_pick,)


@app.cell
def _(lab_pick, mo):
    _cid, _lo, _hi, _default = lab_pick.value
    cutoff = mo.ui.slider(_lo, _hi, value=_default, step=0.1 if _hi < 20 else 1,
                          label="Abnormal if ≥", show_value=True, full_width=True)
    mo.hstack([lab_pick, cutoff], widths=[1, 2], gap=2, align="end")
    return (cutoff,)


@app.cell
def _(CLAUSE, alt, cutoff, lab_pick, mo, pd, run, show_sql, styled):
    _cid = lab_pick.value[0]
    lab_sql = f"""
    SELECT value_as_number,
           CASE WHEN value_as_number >= {cutoff.value}
                THEN 'abnormal' ELSE 'normal' END AS flag
    FROM measurement
    WHERE measurement_concept_id = {_cid}
      AND value_as_number IS NOT NULL
    """
    _m = run(lab_sql)
    _pct = (_m.flag == "abnormal").mean() * 100 if len(_m) else 0
    _h = alt.Chart(_m).mark_bar().encode(
        x=alt.X("value_as_number:Q", bin=alt.Bin(maxbins=40), title=None),
        y=alt.Y("count():Q", title="results"),
        color=alt.Color("flag:N", scale=alt.Scale(domain=["abnormal", "normal"],
                                                   range=[CLAUSE["order"], "#B3BCE3"]),
                        legend=alt.Legend(orient="top", title=None)),
    )
    _rule = alt.Chart(pd.DataFrame({"x": [cutoff.value]})).mark_rule(
        color=CLAUSE["ink"], strokeDash=[5, 4], strokeWidth=2).encode(x="x:Q")
    mo.hstack([
        mo.vstack([show_sql(lab_sql),
                   mo.stat(f"{_pct:.1f}%", label=f"of {len(_m):,} results flagged abnormal")]),
        styled(_h + _rule, w=380, h=200),
    ], widths=[1, 1], gap=2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Click the chart and query the selection

    Age bands come from a `CASE` expression, then `GROUP BY`. **Click a bar** (shift-click for several) to filter the table.
    """)
    return


@app.cell
def _(CLAUSE, alt, mo, run, styled):
    _bands = run("""
    SELECT CASE
             WHEN 2024 - year_of_birth < 40 THEN '18–39'
             WHEN 2024 - year_of_birth < 65 THEN '40–64'
             ELSE '65+'
           END AS age_band,
           COUNT(*) AS people
    FROM person
    GROUP BY 1
    ORDER BY 1
    """)
    age_chart = mo.ui.altair_chart(
        styled(alt.Chart(_bands).mark_bar(color=CLAUSE["select"]).encode(
            x=alt.X("age_band:N", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("people:Q", title="people"),
        ), w=360, h=240),
        chart_selection="point",
    )
    return (age_chart,)


@app.cell
def _(age_chart, mo, run, show_sql):
    _sel = age_chart.value
    _picked = sorted(_sel["age_band"].unique()) if len(_sel) else ["18–39", "40–64", "65+"]
    _in = ", ".join(f"'{b}'" for b in _picked)
    band_sql = f"""
    WITH banded AS (
      SELECT person_id,
             CASE WHEN 2024 - year_of_birth < 40 THEN '18–39'
                  WHEN 2024 - year_of_birth < 65 THEN '40–64'
                  ELSE '65+' END AS age_band
      FROM person
    )
    SELECT c.concept_name AS condition,
           COUNT(DISTINCT b.person_id) AS patients
    FROM banded AS b
    JOIN condition_occurrence AS co ON b.person_id = co.person_id
    JOIN concept AS c ON co.condition_concept_id = c.concept_id
    WHERE b.age_band IN ({_in})
    GROUP BY 1
    ORDER BY 2 DESC
    LIMIT 5
    """
    mo.hstack([
        age_chart,
        mo.vstack([mo.md(f"Showing: **{', '.join(_picked)}**"),
                   mo.ui.table(run(band_sql), selection=None, page_size=5),
                   mo.accordion({"Show the SQL": show_sql(band_sql)})]),
    ], widths=[1, 1], gap=2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## CTEs: build a cohort step by step

    *Of patients with type 2 diabetes, how many started metformin within N days of diagnosis?*
    Each `WITH` block is a named step; read them top to bottom.
    """)
    return


@app.cell
def _(mo):
    window_days = mo.ui.slider(0, 240, value=90, step=15,
                               label="Window (days)", show_value=True, full_width=True)
    window_days
    return (window_days,)


@app.cell
def _(CLAUSE, alt, mo, run, show_sql, styled, window_days):
    cohort_sql = f"""
    WITH t2dm AS (          -- index date = first T2DM diagnosis
      SELECT person_id, MIN(condition_start_date) AS index_date
      FROM condition_occurrence
      WHERE condition_concept_id = 201826
      GROUP BY person_id
    ),
    metformin AS (          -- first metformin exposure
      SELECT person_id, MIN(drug_exposure_start_date) AS first_rx
      FROM drug_exposure
      WHERE drug_concept_id = 1503297
      GROUP BY person_id
    )
    SELECT COUNT(*)                                  AS t2dm_patients,
           COUNT(m.person_id)                        AS any_metformin,
           COUNT(CASE WHEN date_diff('day', t.index_date, m.first_rx)
                           BETWEEN 0 AND {window_days.value}
                      THEN 1 END)                    AS within_window
    FROM t2dm AS t
    LEFT JOIN metformin AS m ON t.person_id = m.person_id
    """
    _c = run(cohort_sql).melt(var_name="step", value_name="patients")
    _c["label"] = ["T2DM", "Any metformin", f"Metformin ≤ {window_days.value} d"]
    _f = alt.Chart(_c).mark_bar(color=CLAUSE["join"], cornerRadiusEnd=3).encode(
        y=alt.Y("label:N", sort=None, title=None),
        x=alt.X("patients:Q", title="patients"),
    )
    _t = _f.mark_text(align="left", dx=4, color=CLAUSE["ink"]).encode(text="patients:Q")
    mo.vstack([styled(_f + _t, w=560, h=110), show_sql(cohort_sql)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    # Beyond the basics
    Pattern matching, subqueries, set operations and window functions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## LIKE finds concepts by text

    - `%` matches any run of characters; `_` matches exactly one
    - Use `LIKE` to *find* concept IDs, then filter event tables on the IDs
    - Text search misses synonyms and is slow on the full vocabulary

    Try `%disease`, `_etformin`, `%in%`, `%blood%`. The query below is a SQL cell, so the operator itself is interpolated from the switches.
    """)
    return


@app.cell
def _(mo):
    like_pat = mo.ui.text(value="%chronic%", label="Pattern")
    like_ci = mo.ui.switch(value=True, label="Case-insensitive (ILIKE)")
    like_not = mo.ui.switch(value=False, label="NOT")
    mo.hstack([like_pat, like_ci, like_not], justify="start", gap=2, align="center")
    return like_ci, like_not, like_pat


@app.cell
def _(con, like_ci, like_not, like_pat, mo):
    _df = mo.sql(
        f"""
        SELECT concept_id, concept_name, domain_id, vocabulary_id
        FROM concept
        WHERE concept_name {'NOT ' if like_not.value else ''}{'ILIKE' if like_ci.value else 'LIKE'} '{like_pat.value.replace("'", "''")}'
        ORDER BY domain_id, concept_name
        """,
        engine=con
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## String functions: CONCAT, SPLIT_PART, REGEXP_EXTRACT

    - `||` concatenates
    - `SPLIT_PART` and `regexp_extract` pull pieces out of a string
    - Source values in OMOP (`*_source_value`) are free text, so these functions do most of the cleanup
    """)
    return


@app.cell
def _(mo):
    str_domain = mo.ui.radio(["Measurement", "Drug", "Condition"], value="Measurement",
                             label="Domain", inline=True)
    str_domain
    return (str_domain,)


@app.cell
def _(mo, run, show_sql, str_domain):
    str_sql = f"""
    SELECT concept_name,
           LOWER(concept_name)                   AS lower_name,
           LENGTH(concept_name)                  AS n_chars,
           vocabulary_id || ':' || concept_id    AS code_label,
           SPLIT_PART(concept_name, ' ', 1)      AS first_word,
           regexp_extract(concept_name, '\\[(.*)\\]', 1) AS in_brackets
    FROM concept
    WHERE domain_id = '{str_domain.value}'
    """
    mo.vstack([show_sql(str_sql), mo.ui.table(run(str_sql), page_size=6, selection=None)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Subqueries: IN, EXISTS and NOT EXISTS

    *Which patients have a condition but no record of the usual drug?* This is a classic care-gap query.

    - `EXISTS` stops at the first match, so it never duplicates rows the way a `JOIN` can
    - `NOT IN` breaks if the subquery returns a `NULL`; prefer `NOT EXISTS`
    """)
    return


@app.cell
def _(mo):
    sub_cond = mo.ui.dropdown(
        {"Type 2 diabetes": 201826, "Essential hypertension": 320128,
         "Coronary arteriosclerosis": 317576},
        value="Type 2 diabetes", label="Has condition")
    sub_drug = mo.ui.dropdown(
        {"metformin": 1503297, "lisinopril": 1308216, "amlodipine": 1332418,
         "atorvastatin": 1545958, "aspirin": 1112807},
        value="metformin", label="Drug")
    sub_mode = mo.ui.radio(["EXISTS", "NOT EXISTS"], value="NOT EXISTS",
                           label="Drug check", inline=True)
    mo.hstack([sub_cond, sub_drug, sub_mode], justify="start", gap=2)
    return sub_cond, sub_drug, sub_mode


@app.cell
def _(mo, run, show_sql, sub_cond, sub_drug, sub_mode):
    sub_sql = f"""
    SELECT COUNT(*) AS patients
    FROM person AS p
    WHERE p.person_id IN (                 -- has the condition
            SELECT person_id FROM condition_occurrence
            WHERE condition_concept_id = {sub_cond.value})
      AND {sub_mode.value} (                   -- correlated subquery
            SELECT 1 FROM drug_exposure AS d
            WHERE d.person_id = p.person_id
              AND d.drug_concept_id = {sub_drug.value})
    """
    _n = int(run(sub_sql).patients[0])
    _base = int(run(f"SELECT COUNT(DISTINCT person_id) n FROM condition_occurrence "
                    f"WHERE condition_concept_id = {sub_cond.value}").n[0])
    mo.vstack([
        show_sql(sub_sql),
        mo.hstack([
            mo.stat(f"{_base:,}", label=f"with {sub_cond.selected_key}"),
            mo.stat(f"{_n:,}", label=f"{'on' if sub_mode.value == 'EXISTS' else 'not on'} {sub_drug.selected_key}"),
            mo.stat(f"{100 * _n / _base:.0f}%" if _base else "–", label="share"),
        ], justify="start", gap=2),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## UNION, INTERSECT and EXCEPT
    """)
    return


@app.cell
def _(mo):
    _conds = {"Type 2 diabetes": 201826, "Essential hypertension": 320128,
              "Obesity": 433736, "Chronic kidney disease": 46271022,
              "Depressive disorder": 440383}
    set_a = mo.ui.dropdown(_conds, value="Type 2 diabetes", label="A")
    set_b = mo.ui.dropdown(_conds, value="Essential hypertension", label="B")
    set_op = mo.ui.radio(["UNION", "INTERSECT", "EXCEPT", "UNION ALL"],
                         value="INTERSECT", label="Operator", inline=True)
    mo.hstack([set_a, set_b, set_op], justify="start", gap=2)
    return set_a, set_b, set_op


@app.cell(hide_code=True)
def _(CLAUSE, mo, run, set_a, set_b, set_op):
    _ab = run(f"""
    SELECT COUNT(DISTINCT person_id) FILTER (WHERE condition_concept_id = {set_a.value}) AS a,
           COUNT(DISTINCT person_id) FILTER (WHERE condition_concept_id = {set_b.value}) AS b
    FROM condition_occurrence""")
    _both = int(run(f"""
    SELECT COUNT(*) AS n FROM (
      SELECT person_id FROM condition_occurrence WHERE condition_concept_id = {set_a.value}
      INTERSECT
      SELECT person_id FROM condition_occurrence WHERE condition_concept_id = {set_b.value})""").n[0])
    _a, _b = int(_ab.a[0]), int(_ab.b[0])
    _fill = CLAUSE["from"]
    _shade = {
        "UNION": f'<circle cx="160" cy="130" r="100" fill="{_fill}"/><circle cx="260" cy="130" r="100" fill="{_fill}"/>',
        "UNION ALL": f'<circle cx="160" cy="130" r="100" fill="{_fill}"/><circle cx="260" cy="130" r="100" fill="{_fill}"/>',
        "INTERSECT": f'<circle cx="160" cy="130" r="100" fill="{_fill}" clip-path="url(#venn-b)"/>',
        "EXCEPT": f'<circle cx="160" cy="130" r="100" fill="{_fill}" mask="url(#venn-not-b)"/>',
    }[set_op.value]
    venn = mo.Html(f"""
    <svg viewBox="0 0 420 260" width="100%" style="max-width:420px" role="img" aria-label="Venn diagram of the two patient sets">
      <style>.v{{font:700 20px 'JetBrains Mono',monospace}}.vl{{font:15px Georgia,serif;fill:#5F6168}}</style>
      <defs>
        <clipPath id="venn-b"><circle cx="260" cy="130" r="100"/></clipPath>
        <mask id="venn-not-b"><rect width="420" height="260" fill="#fff"/><circle cx="260" cy="130" r="100" fill="#000"/></mask>
      </defs>
      <g opacity="0.3">{_shade}</g>
      <circle cx="160" cy="130" r="100" fill="none" stroke="{_fill}" stroke-width="2.5"/>
      <circle cx="260" cy="130" r="100" fill="none" stroke="{_fill}" stroke-width="2.5"/>
      <text class="vl" x="70" y="22">A</text><text class="vl" x="340" y="22">B</text>
      <text class="v" x="105" y="137" text-anchor="middle">{_a - _both}</text>
      <text class="v" x="210" y="137" text-anchor="middle">{_both}</text>
      <text class="v" x="315" y="137" text-anchor="middle">{_b - _both}</text>
      <text class="vl" x="210" y="252" text-anchor="middle">distinct patients in each region</text>
    </svg>""")
    return (venn,)


@app.cell
def _(mo, run, set_a, set_b, set_op, show_sql, venn):
    set_sql = f"""
    SELECT person_id FROM condition_occurrence
    WHERE condition_concept_id = {set_a.value}      -- A
    {set_op.value}
    SELECT person_id FROM condition_occurrence
    WHERE condition_concept_id = {set_b.value}      -- B
    """
    _s = run(set_sql)
    mo.hstack([
        venn,
        mo.vstack([
            show_sql(set_sql),
            mo.md(f"**{len(_s):,}** rows returned, **{_s.person_id.nunique():,}** distinct patients"),
            mo.md("Set operators stack two queries with the same columns. `UNION`, `INTERSECT` and "
                  "`EXCEPT` remove duplicates; `UNION ALL` keeps them, so a patient with both "
                  "conditions appears twice.").callout(kind="neutral"),
        ]),
    ], widths=[1, 1], gap=2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## NULL-safe summaries: COALESCE, NULLIF, FILTER

    - `race_concept_id = 0` means “no matching concept”, so the `LEFT JOIN` returns `NULL`; `COALESCE` swaps in a label
    - `FILTER (WHERE …)` counts a subset inside one group, turning rows into columns
    - `NULLIF(x, 0)` returns `NULL` when `x` is 0, so a division gives `NULL` instead of an error
    """)
    return


@app.cell
def _(mo):
    use_coalesce = mo.ui.switch(value=True, label="Wrap in COALESCE")
    use_coalesce
    return (use_coalesce,)


@app.cell
def _(mo, run, show_sql, use_coalesce):
    _race = ("COALESCE(c.concept_name, 'Unknown')" if use_coalesce.value else "c.concept_name")
    null_sql = f"""
    SELECT {_race} AS race,
           COUNT(*) AS people,
           COUNT(*) FILTER (WHERE p.gender_concept_id = 8532) AS female,
           COUNT(*) FILTER (WHERE p.gender_concept_id = 8507) AS male,
           ROUND(100.0 * COUNT(*) FILTER (WHERE p.gender_concept_id = 8532)
                 / NULLIF(COUNT(*), 0), 1) AS pct_female
    FROM person AS p
    LEFT JOIN concept AS c ON p.race_concept_id = c.concept_id
    GROUP BY 1
    ORDER BY people DESC
    """
    mo.vstack([show_sql(null_sql), mo.ui.table(run(null_sql), selection=None)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## OVER aggregates without collapsing rows

    `GROUP BY` turns 3 visits into 1 row. A window function keeps all 3 rows and adds the aggregate to each one.
    """)
    return


@app.cell
def _(mo):
    win_mode = mo.ui.radio(["GROUP BY", "Window: OVER (PARTITION BY …)"],
                           value="Window: OVER (PARTITION BY …)", label="Show", inline=True)
    win_mode
    return (win_mode,)


@app.cell
def _(mo, run, show_sql, win_mode):
    if win_mode.value == "GROUP BY":
        win_sql = """
    SELECT person_id,
           COUNT(*)              AS n_visits,
           MIN(visit_start_date) AS first_visit
    FROM visit_occurrence
    WHERE person_id IN (1, 2, 3)
    GROUP BY person_id
    ORDER BY person_id"""
    else:
        win_sql = """
    SELECT person_id, visit_start_date,
           COUNT(*)              OVER (PARTITION BY person_id) AS n_visits,
           MIN(visit_start_date) OVER (PARTITION BY person_id) AS first_visit,
           date_diff('day',
             MIN(visit_start_date) OVER (PARTITION BY person_id),
             visit_start_date)                                AS days_since_first
    FROM visit_occurrence
    WHERE person_id IN (1, 2, 3)
    ORDER BY person_id, visit_start_date"""
    mo.hstack([show_sql(win_sql), mo.ui.table(run(win_sql), page_size=6, selection=None)],
              widths=[1, 1], gap=2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ROW_NUMBER, RANK and DENSE_RANK

    - On ties, `ROW_NUMBER` still counts 1, 2, 3, `RANK` repeats and then skips, and `DENSE_RANK` repeats without skipping
    - `ROW_NUMBER() … = 1` is the standard OMOP “first event per person” pattern
    - DuckDB also lets you write `QUALIFY rn = 1` instead of the outer query
    """)
    return


@app.cell
def _(mo):
    rank_person = mo.ui.dropdown(["85", "306", "679", "1005"], value="306",
                                 label="Patient (has same-day diagnoses)")
    rank_first = mo.ui.switch(value=False, label="First diagnosis per patient (rn = 1)")
    mo.hstack([rank_person, rank_first], justify="start", gap=2, align="center")
    return rank_first, rank_person


@app.cell
def _(mo, rank_first, rank_person, run, show_sql):
    if not rank_first.value:
        rank_sql = f"""
    SELECT co.condition_start_date, c.concept_name,
           ROW_NUMBER() OVER w AS row_num,
           RANK()       OVER w AS rnk,
           DENSE_RANK() OVER w AS dense_rnk
    FROM condition_occurrence AS co
    JOIN concept AS c ON co.condition_concept_id = c.concept_id
    WHERE co.person_id = {rank_person.value}
    WINDOW w AS (ORDER BY co.condition_start_date)
    ORDER BY row_num"""
    else:
        rank_sql = """
    WITH ranked AS (
      SELECT co.person_id, c.concept_name, co.condition_start_date,
             ROW_NUMBER() OVER (PARTITION BY co.person_id
                                ORDER BY co.condition_start_date,
                                         co.condition_occurrence_id) AS rn
      FROM condition_occurrence AS co
      JOIN concept AS c ON co.condition_concept_id = c.concept_id
    )
    SELECT person_id, concept_name AS first_condition, condition_start_date
    FROM ranked
    WHERE rn = 1
    ORDER BY person_id"""
    _rk = run(rank_sql)
    mo.vstack([show_sql(rank_sql),
               mo.md(f"**{len(_rk):,}** rows, one per patient") if rank_first.value else mo.md(""),
               mo.ui.table(_rk, page_size=6, selection=None)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## LEAD and LAG: time between visits

    - `LEAD(x)` reads the next row's value in the window and `LAG(x)` reads the previous one
    - This is how readmission and gap-in-care measures are built
    """)
    return


@app.cell
def _(mo):
    lag_types = mo.ui.multiselect(
        {"Inpatient": 9201, "Outpatient": 9202, "Emergency": 9203},
        value=["Inpatient"], label="Index visit types")
    return_days = mo.ui.slider(7, 180, value=30, step=1,
                               label="Return within (days)", show_value=True, full_width=True)
    mo.hstack([lag_types, return_days], widths=[1, 2], gap=2, align="end")
    return lag_types, return_days


@app.cell
def _(CLAUSE, alt, lag_types, mo, np, return_days, run, show_sql, styled):
    mo.stop(not lag_types.value, mo.md("*Pick at least one visit type.*"))
    _ids = ", ".join(str(v) for v in lag_types.value)
    lag_sql = f"""
    WITH seq AS (
      SELECT person_id, visit_concept_id, visit_end_date,
             LEAD(visit_start_date) OVER (PARTITION BY person_id
                                          ORDER BY visit_start_date) AS next_visit
      FROM visit_occurrence
    )
    SELECT date_diff('day', visit_end_date, next_visit) AS days_to_next
    FROM seq
    WHERE visit_concept_id IN ({_ids})
      AND next_visit >= visit_end_date
    """
    _g = run(lag_sql)
    _g["returned"] = np.where(_g.days_to_next <= return_days.value,
                              f"within {return_days.value} d", "later")
    _pct = (_g.days_to_next <= return_days.value).mean() * 100 if len(_g) else 0
    _hist = alt.Chart(_g[_g.days_to_next <= 730]).mark_bar().encode(
        x=alt.X("days_to_next:Q", bin=alt.Bin(step=15), title="days to next visit (first 2 years)"),
        y=alt.Y("count():Q", title="visits"),
        color=alt.Color("returned:N", sort="descending",
                        scale=alt.Scale(range=[CLAUSE["window"], "#DCDDDC"]),
                        legend=alt.Legend(orient="top", title=None)),
    )
    mo.vstack([
        mo.md(f"**{_pct:.1f}%** of {len(_g):,} index visits had another visit within {return_days.value} days"),
        styled(_hist, w=620, h=180),
        mo.accordion({"Show the SQL": show_sql(lag_sql)}),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Window frames: running and moving values

    - The frame says which rows around the current one feed the aggregate
    - `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` gives a 3-reading moving average
    - With only `ORDER BY`, the frame runs from the first row, giving a running total or max
    """)
    return


@app.cell
def _(mo):
    roll_person = mo.ui.dropdown(["806", "648", "644", "431"], value="806", label="Patient")
    roll_k = mo.ui.slider(0, 5, value=2, label="ROWS … PRECEDING", show_value=True, full_width=True)
    mo.hstack([roll_person, roll_k], widths=[1, 2], gap=2, align="end")
    return roll_k, roll_person


@app.cell
def _(CLAUSE, alt, mo, roll_k, roll_person, run, show_sql, styled):
    roll_sql = f"""
    SELECT measurement_date,
           value_as_number AS sbp,
           AVG(value_as_number) OVER (PARTITION BY person_id ORDER BY measurement_date
                 ROWS BETWEEN {roll_k.value} PRECEDING AND CURRENT ROW) AS moving_avg,
           MAX(value_as_number) OVER (PARTITION BY person_id
                 ORDER BY measurement_date)                   AS running_max
    FROM measurement
    WHERE measurement_concept_id = 3004249        -- systolic BP
      AND person_id = {roll_person.value}
    ORDER BY measurement_date
    """
    _r = run(roll_sql).melt(id_vars="measurement_date", var_name="series", value_name="mmHg")
    _ln = alt.Chart(_r).mark_line(point=True).encode(
        x=alt.X("measurement_date:T", title=None),
        y=alt.Y("mmHg:Q", scale=alt.Scale(zero=False), title="systolic BP (mmHg)"),
        color=alt.Color("series:N", title=None, legend=alt.Legend(orient="top"),
                        scale=alt.Scale(domain=["sbp", "moving_avg", "running_max"],
                                        range=["#B3BCE3", CLAUSE["window"], CLAUSE["ink"]])),
        strokeDash=alt.StrokeDash("series:N", legend=None,
                                  scale=alt.Scale(domain=["sbp", "moving_avg", "running_max"],
                                                  range=[[1, 0], [1, 0], [5, 4]])),
        tooltip=["measurement_date:T", "series", alt.Tooltip("mmHg:Q", format=".1f")],
    )
    mo.vstack([styled(_ln, w=640, h=200), mo.accordion({"Show the SQL": show_sql(roll_sql)})])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## 🟢 Native only: explore without writing SQL

    Before you write a query, it helps to *look* at the data. marimo has two no-code tools:

    - **Data explorer**: drag columns onto encodings to build charts
    - **Dataframe transformer**: filter, group and aggregate from menus. It **writes the equivalent pandas code for you**, and its output (`transformer.value`) is an ordinary DataFrame that later cells can use

    Both need room and a live session, so the deck leaves them out. In Jupyter the closest equivalents are separate extensions.
    """)
    return


@app.cell
def _(mo, run):
    patient_summary = run("""
    SELECT p.person_id,
           g.concept_name                          AS sex,
           2024 - p.year_of_birth                  AS age,
           COALESCE(r.concept_name, 'Unknown')     AS race,
           COUNT(DISTINCT v.visit_occurrence_id)   AS n_visits,
           COUNT(DISTINCT co.condition_concept_id) AS n_conditions
    FROM person AS p
    JOIN concept AS g ON p.gender_concept_id = g.concept_id
    LEFT JOIN concept AS r ON p.race_concept_id = r.concept_id
    LEFT JOIN visit_occurrence AS v ON p.person_id = v.person_id
    LEFT JOIN condition_occurrence AS co ON p.person_id = co.person_id
    GROUP BY 1, 2, 3, 4
    """)
    explorer = mo.ui.data_explorer(patient_summary)
    transformer = mo.ui.dataframe(patient_summary)
    mo.ui.tabs({"Data explorer": explorer, "Dataframe transformer": transformer})
    return (transformer,)


@app.cell(hide_code=True)
def _(mo, transformer):
    mo.md(f"`transformer.value` currently has **{len(transformer.value):,} rows × {transformer.value.shape[1]} columns**. Add a transform in the tab above and this line updates.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Exercise

    Write any query against `person`, `visit_occurrence`, `condition_occurrence`, `drug_exposure`, `measurement` or `concept`.

    The deck uses a `code_editor` plus a separate `run_button`. Here the editor is wrapped in **`.form()`**, so nothing runs until you press *Run query*.
    In the native editor, the simplest option is to **add a SQL cell** with the `+ SQL` button.
    """)
    return


@app.cell
def _(mo):
    editor = mo.ui.code_editor(
        value="""SELECT c.concept_name, ROUND(AVG(m.value_as_number), 2) AS mean_value
    FROM measurement AS m
    JOIN concept AS c ON m.measurement_concept_id = c.concept_id
    GROUP BY c.concept_name""",
        language="sql", min_height=140,
    ).form(submit_button_label="Run query", bordered=True)
    editor
    return (editor,)


@app.cell
def _(editor, mo, run):
    mo.stop(editor.value is None, mo.md("*Press **Run query** to see results.*"))
    try:
        _out = run(editor.value)
        _res = mo.vstack([mo.md(f"{len(_out):,} rows"), mo.ui.table(_out, page_size=6, selection=None)])
    except Exception as _e:
        _res = mo.callout(mo.md(f"**The query failed.** {_e}"), kind="danger")
    _res
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Same query, three ways

    | Task | DuckDB (this notebook) | SQL Server | PostgreSQL |
    |---|---|---|---|
    | First *n* rows | `LIMIT 10` | `SELECT TOP 10 …` | `LIMIT 10` |
    | Days between dates | `date_diff('day', a, b)` | `DATEDIFF(day, a, b)` | `b - a` |
    | Truncate to year | `date_trunc('year', d)` | `DATETRUNC(year, d)` | `date_trunc('year', d)` |
    | Current date | `current_date` | `CAST(GETDATE() AS date)` | `current_date` |
    | String concat | `a || b` | `CONCAT(a, b)` | `a || b` |
    | Case-insensitive match | `s ILIKE '%ckd%'` | `s LIKE '%ckd%'` (default collation ignores case) | `s ILIKE '%ckd%'` |
    | Regex match | `regexp_matches(s, 'p')` | `LIKE` patterns only (`REGEXP_LIKE` from 2025) | `s ~ 'p'` |
    | Conditional count | `COUNT(*) FILTER (WHERE …)` | `SUM(CASE WHEN … THEN 1 ELSE 0 END)` | `COUNT(*) FILTER (WHERE …)` |
    | Keep first row per group | `QUALIFY ROW_NUMBER() OVER (…) = 1` | subquery with `WHERE rn = 1` | subquery with `WHERE rn = 1` |
    | Table reference | `cdm.person` | `cdm_db.dbo.person` | `cdm.person` |

    OHDSI’s **SqlRender** translates one parameterised query into each dialect, which is how ATLAS and HADES packages stay portable.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Export the result

    Pipe-delimited with every field quoted survives commas inside concept names. The year leads the filename so extracts sort by period.
    In DuckDB: `COPY (SELECT ...) TO '2024_t2dm_cohort.tsv' (HEADER, DELIMITER '|', FORCE_QUOTE *);`
    """)
    return


@app.cell
def _(mo):
    export_year = mo.ui.dropdown([str(y) for y in range(2016, 2025)], value="2024",
                                 label="Diagnosis year")
    export_year
    return (export_year,)


@app.cell
def _(export_year, mo, run):
    import csv as _csv
    _x = run(f"""
    SELECT co.person_id, c.concept_name, co.condition_start_date
    FROM condition_occurrence AS co
    JOIN concept AS c ON co.condition_concept_id = c.concept_id
    WHERE co.condition_concept_id = 201826
      AND EXTRACT(year FROM co.condition_start_date) = {export_year.value}
    ORDER BY co.condition_start_date
    """)
    _txt = _x.to_csv(sep="|", index=False, quoting=_csv.QUOTE_ALL)
    _fname = f"{export_year.value}_t2dm_cohort.tsv"
    mo.vstack([
        mo.md(f"**{len(_x):,}** rows → `{_fname}`"),
        mo.md("```text\n" + "\n".join(_txt.splitlines()[:5]) + "\n```"),
        mo.download(data=_txt.encode(), filename=_fname, mimetype="text/tab-separated-values",
                    label=f"Download {_fname}"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## marimo vs. Quarto vs. Jupyter

    The same lesson, the same queries, three ways to run them.

    | | Jupyter (`.ipynb`) | Quarto + marimo engine (`.qmd`) | Native marimo (`.py`) |
    |---|---|---|---|
    | **File format** | JSON with outputs embedded | Markdown with ` ```{python .marimo} ` blocks | Plain Python: runs as a script, an app or a notebook |
    | **Execution model** | You run cells in whatever order you like; state persists | Reactive (marimo), rendered into slides | Reactive: change a cell and its dependents rerun |
    | **Hidden state** | Common: delete or edit a cell and old variables survive | None | None: deleting a cell deletes its variables |
    | **Interactivity** | ipywidgets + `interact` / `observe` callbacks | `mo.ui` widgets in the browser (Pyodide) | `mo.ui` widgets, table and chart selections, forms |
    | **SQL** | Strings in `con.execute()` (or a `%sql` extension) | ` ```{sql .marimo} `; output is display-only | SQL cells; results are DataFrames you can query again |
    | **Layout** | Linear cells | Quarto / reveal.js: columns, themes, SCSS | `hstack`, `tabs`, `sidebar`; vertical, grid or slides layout |
    | **Git diffs** | Noisy (outputs and metadata) | Clean | Clean |
    | **Packages** | `requirements.txt` / environment | `pyproject:` in the front matter | PEP 723 header + `--sandbox`; molab installs on import |
    | **Sharing** | nbviewer, GitHub preview, Colab, Binder | Static site (GitHub Pages, Quarto Pub) | molab link, badge, WASM embed, `marimo export html-wasm` |
    | **Best for** | Ad-hoc exploration; the existing ecosystem | Polished lecture decks and course sites | Hands-on labs and reproducible, shareable apps |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Put this notebook on molab

    [molab](https://molab.marimo.io) is marimo's hosted notebook service. Once this file is on GitHub, molab opens it directly. Paste the repo path below to generate the links.
    """)
    return


@app.cell
def _(mo):
    gh_path = mo.ui.text(
        value="https://github.com/pc-piyush/F26_Marimo/PC/sql-basics-marimo.py",
        label="GitHub path (owner/repo/blob/branch/path.py)",
        full_width=True,
    )
    gh_path
    return (gh_path,)


@app.cell
def _(gh_path, mo):
    _p = gh_path.value.strip().removeprefix("https://github.com/").strip("/")
    _molab = f"https://molab.marimo.io/github/{_p}"
    _wasm = f"{_molab}/wasm"
    _embed = f"https://marimo.app/github/{_p}/wasm?embed=true"
    _badge = f"[![Open in molab](https://marimo.io/molab-shield.svg)]({_molab})"
    _iframe = f'<iframe src="{_embed}" width="100%" height="700" frameborder="0"></iframe>'
    mo.vstack([
        mo.md(_badge),
        mo.md(f"""
    | What | Link / snippet |
    |---|---|
    | **molab notebook** (static preview; *Run* starts a server) | <{_molab}> |
    | **WASM preview** (runs in the viewer's browser, no login) | <{_wasm}> |
    | **Badge** for a README or the Quarto site | `{_badge}` |
    """),
        mo.md("**Embed in a Quarto page** so the notebook sits next to the slides:"),
        mo.md(f"```html\n{_iframe}\n```"),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Running it yourself

    ```bash
    # Editable notebook in an isolated env built from the PEP 723 header
    uvx marimo edit --sandbox sql-basics-marimo.py

    # Same file as a read-only app (code hidden, still reactive)
    uvx marimo run --sandbox sql-basics-marimo.py

    # Plain script: every cell runs once, no widgets
    uv run sql-basics-marimo.py

    # Commit outputs so molab's static preview isn't blank
    uvx marimo export session sql-basics-marimo.py

    # Self-contained WASM site (the same runtime the Quarto deck uses)
    uvx marimo export html-wasm sql-basics-marimo.py -o site --mode run

    # Convert the Jupyter version (or any .ipynb) to marimo
    uvx marimo convert sql-basics-jupyter.ipynb -o converted.py
    ```

    In the editor, switch the app layout to **Slides** to compare marimo's own slide mode with the Quarto deck.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Recap

    | Clause | Job |
    |---|---|
    | **FROM** | which table (and alias) |
    | **JOIN … ON** | link tables, usually on `person_id` or `*_concept_id` |
    | **WHERE** | keep rows, before any grouping |
    | **GROUP BY** | collapse rows into groups for `COUNT`, `AVG`, `MIN` |
    | **HAVING** | keep groups, after aggregation |
    | **SELECT** | choose and compute output columns, incl. `CASE WHEN` |
    | **ORDER BY** | sort, then `LIMIT` to trim |
    | **LIKE / ILIKE** | match text with `%` and `_`, to find concept IDs |
    | **EXISTS** | keep rows that have (or lack) a related row, without duplicating them |
    | **UNION · INTERSECT · EXCEPT** | combine two result sets that have the same columns |
    | **COALESCE · NULLIF · FILTER** | replace `NULL`s, prevent division by zero, count a subset per group |
    | **OVER · ROW_NUMBER · LAG/LEAD · ROWS BETWEEN** | per-group aggregates that keep every row, first events, gaps, running values |

    Built with [DuckDB](https://duckdb.org/), [Quarto](https://quarto.org/) and [marimo](https://marimo.io/gallery).
    """)
    return


if __name__ == "__main__":
    app.run()
