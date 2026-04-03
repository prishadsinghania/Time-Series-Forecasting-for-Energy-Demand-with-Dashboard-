"""
Interactive dashboard: load profile, generation mix, weather relationships, pipeline reports.
Run from repository root: streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data" / "combined_avg.csv"
REPORTS_DIR = REPO_ROOT / "reports"
SUMMARY_JSON = REPORTS_DIR / "dataset_summary.json"
QUALITY_JSON = REPORTS_DIR / "data_quality.json"
METRICS_JSON = REPORTS_DIR / "model_metrics.json"
ROLLING_JSON = REPORTS_DIR / "rolling_load.json"

px.defaults.template = "plotly_dark"
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,23,42,0.9)",
    font=dict(color="#e2e8f0"),
    margin=dict(l=48, r=24, t=48, b=48),
)


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=True)
def load_combined() -> pd.DataFrame:
    if not DATA_PATH.is_file():
        raise FileNotFoundError(str(DATA_PATH))
    df = pd.read_csv(DATA_PATH, index_col="time", parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df.sort_index()


def main() -> None:
    st.set_page_config(
        page_title="Energy demand — dashboard",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; max-width: 1400px; }
        h1 { font-weight: 600; letter-spacing: -0.02em; }
        div[data-testid="stMetricValue"] { font-size: 1.6rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        df = load_combined()
    except FileNotFoundError:
        st.error(
            f"Missing `{DATA_PATH.relative_to(REPO_ROOT)}`. "
            "Run notebooks: Data_Wrangling → Exploratory_Data_Analysis, then `python3 -m pipeline`."
        )
        st.stop()

    summary = _load_json(SUMMARY_JSON)
    quality = _load_json(QUALITY_JSON)
    metrics = _load_json(METRICS_JSON)
    rolling = _load_json(ROLLING_JSON)

    with st.sidebar:
        st.header("Filters")
        dmin, dmax = df.index.min().date(), df.index.max().date()
        dr = st.date_input("Date range", value=(dmin, dmax), min_value=dmin, max_value=dmax)
        if isinstance(dr, tuple) and len(dr) == 2:
            start, end = pd.Timestamp(dr[0], tz="UTC"), pd.Timestamp(dr[1], tz="UTC") + pd.Timedelta(days=1)
            dff = df.loc[(df.index >= start) & (df.index < end)]
        else:
            dff = df
        st.divider()
        st.caption("Reports")
        st.text(f"Summary: {'ok' if summary else 'run pipeline'}")
        st.text(f"Quality: {'ok' if quality else 'run pipeline'}")
        st.text(f"Metrics: {'ok' if metrics else 'run pipeline'}")

    st.title("Electricity demand — monitoring")
    st.caption("Hourly Spain system load, generation, weather (combined panel).")

    c1, c2, c3, c4 = st.columns(4)
    load = dff["total load actual"].dropna()
    c1.metric("Rows (filtered)", f"{len(dff):,}")
    c2.metric("Mean load (MW)", f"{load.mean():,.0f}" if len(load) else "—")
    c3.metric("Max load (MW)", f"{load.max():,.0f}" if len(load) else "—")
    if "price actual" in dff.columns:
        pr = dff["price actual"].dropna()
        c4.metric("Mean price (€)", f"{pr.mean():.2f}" if len(pr) else "—")
    else:
        c4.metric("Mean price", "—")

    if rolling.get("rolling_mean_latest_mw") is not None:
        st.caption(
            f"7-day centered rolling mean of load (latest): **{rolling['rolling_mean_latest_mw']:,.0f} MW** "
            f"(from `reports/rolling_load.json`)."
        )

    tab_ts, tab_mix, tab_weather, tab_pattern, tab_quality, tab_models = st.tabs(
        ["Load & price", "Generation mix", "Weather vs load", "Seasonality", "Data quality", "Models"]
    )

    with tab_ts:
        st.subheader("Total load and system forecast")
        ts = dff.reset_index()
        tcol = "time" if "time" in ts.columns else ts.columns[0]
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ts[tcol],
                y=ts["total load actual"],
                name="Actual load",
                line=dict(color="#38bdf8", width=1.2),
                opacity=0.9,
            )
        )
        if "total load forecast" in ts.columns:
            fig.add_trace(
                go.Scatter(
                    x=ts[tcol],
                    y=ts["total load forecast"],
                    name="TSO day-ahead forecast",
                    line=dict(color="#a78bfa", width=1, dash="dot"),
                    opacity=0.7,
                )
            )
        fig.update_layout(**CHART_LAYOUT, height=420, hovermode="x unified", legend=dict(orientation="h"))
        fig.update_xaxes(gridcolor="rgba(148,163,184,0.15)")
        fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)", title="MW")
        st.plotly_chart(fig, use_container_width=True)

        if "price actual" in dff.columns and "price day ahead" in dff.columns:
            st.subheader("Price — actual vs day-ahead")
            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(x=ts[tcol], y=ts["price actual"], name="Actual", line=dict(color="#f472b6", width=1))
            )
            fig2.add_trace(
                go.Scatter(
                    x=ts[tcol],
                    y=ts["price day ahead"],
                    name="Day-ahead",
                    line=dict(color="#fb923c", width=1, dash="dash"),
                )
            )
            fig2.update_layout(**CHART_LAYOUT, height=360, hovermode="x unified", legend=dict(orientation="h"))
            fig2.update_xaxes(gridcolor="rgba(148,163,184,0.15)")
            fig2.update_yaxes(gridcolor="rgba(148,163,184,0.15)", title="€ / MWh")
            st.plotly_chart(fig2, use_container_width=True)

    with tab_mix:
        st.subheader("Stacked generation (selected fuels)")
        gen_cols = [
            c
            for c in [
                "generation solar",
                "generation wind onshore",
                "generation fossil gas",
                "generation nuclear",
                "generation hydro water reservoir",
                "generation biomass",
            ]
            if c in dff.columns
        ]
        if not gen_cols:
            st.warning("No generation columns found.")
        else:
            sub = dff[gen_cols].fillna(0)
            # Downsample for plotting if very long
            step = max(1, len(sub) // 4000)
            sub = sub.iloc[::step]
            fig = go.Figure()
            for c in gen_cols:
                fig.add_trace(go.Scatter(x=sub.index, y=sub[c], name=c.replace("generation ", ""), stackgroup="one"))
            fig.update_layout(**CHART_LAYOUT, height=480, hovermode="x unified", legend=dict(orientation="h"))
            fig.update_xaxes(gridcolor="rgba(148,163,184,0.15)")
            fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)", title="MW")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Share of average output (filtered window)")
        if gen_cols:
            avg = dff[gen_cols].mean().sort_values(ascending=False)
            fig_p = px.pie(
                names=[c.replace("generation ", "") for c in avg.index],
                values=avg.values,
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            fig_p.update_layout(**CHART_LAYOUT, height=400, showlegend=True)
            st.plotly_chart(fig_p, use_container_width=True)

    with tab_weather:
        st.subheader("Scatter — humidity vs solar generation")
        if "humidity" in dff.columns and "generation solar" in dff.columns:
            sample = dff[["humidity", "generation solar"]].dropna()
            if len(sample) > 8000:
                sample = sample.sample(8000, random_state=42)
            fig = px.density_contour(
                sample,
                x="humidity",
                y="generation solar",
                color_discrete_sequence=["#38bdf8"],
            )
            fig.update_layout(**CHART_LAYOUT, height=440)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Required columns not present.")

        st.subheader("Wind speed vs onshore wind generation")
        if "wind_speed" in dff.columns and "generation wind onshore" in dff.columns:
            sample = dff[["wind_speed", "generation wind onshore"]].dropna()
            if len(sample) > 8000:
                sample = sample.sample(8000, random_state=42)
            fig2 = px.scatter(
                sample,
                x="wind_speed",
                y="generation wind onshore",
                opacity=0.25,
                trendline="lowess",
                color_discrete_sequence=["#34d399"],
            )
            fig2.update_layout(**CHART_LAYOUT, height=440)
            fig2.update_traces(marker=dict(size=6))
            st.plotly_chart(fig2, use_container_width=True)

    with tab_pattern:
        st.subheader("Mean load by hour and weekday")
        pat = dff[["total load actual"]].copy()
        pat["hour"] = pat.index.hour
        pat["dow"] = pat.index.day_name()
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        g = pat.groupby(["hour", "dow"])["total load actual"].mean().reset_index()
        heat = g.pivot(index="hour", columns="dow", values="total load actual")
        heat = heat[[c for c in order if c in heat.columns]]
        fig_h = px.imshow(
            heat,
            labels=dict(x="Weekday", y="Hour (UTC)", color="Mean MW"),
            aspect="auto",
            color_continuous_scale="Blues",
        )
        fig_h.update_layout(**CHART_LAYOUT, height=480)
        st.plotly_chart(fig_h, use_container_width=True)

        st.subheader("Average daily profile (overall)")
        hourly = dff.groupby(dff.index.hour)["total load actual"].mean()
        fig_l = px.area(
            x=hourly.index,
            y=hourly.values,
            labels={"x": "Hour", "y": "Mean load (MW)"},
        )
        fig_l.update_traces(fill="tozeroy", line_color="#38bdf8", fillcolor="rgba(56,189,248,0.25)")
        fig_l.update_layout(**CHART_LAYOUT, height=320, showlegend=False)
        fig_l.update_xaxes(gridcolor="rgba(148,163,184,0.15)")
        fig_l.update_yaxes(gridcolor="rgba(148,163,184,0.15)")
        st.plotly_chart(fig_l, use_container_width=True)

    with tab_quality:
        st.subheader("Pipeline data-quality report")
        if not quality:
            st.warning("Run `python3 -m pipeline` to generate `reports/data_quality.json`.")
        else:
            st.json(quality)
            miss = quality.get("missing_pct_by_column") or {}
            if miss:
                fig_q = px.bar(
                    x=list(miss.keys()),
                    y=list(miss.values()),
                    labels={"x": "Column", "y": "Missing %"},
                    color=list(miss.values()),
                    color_continuous_scale="Reds",
                )
                fig_q.update_layout(**CHART_LAYOUT, height=420, showlegend=False)
                fig_q.update_xaxes(tickangle=45)
                st.plotly_chart(fig_q, use_container_width=True)

    with tab_models:
        st.subheader("Model metrics (pipeline + notebooks)")
        st.caption(
            "Quick sklearn baselines refresh when you run `python3 -m pipeline`. "
            "Prophet / XGBoost / SARIMAX live in `Modeling.ipynb`."
        )
        if not metrics:
            st.warning("Run `python3 -m pipeline` to generate `reports/model_metrics.json`.")
        else:
            res = metrics.get("results") or []
            if res:
                st.dataframe(pd.DataFrame(res), use_container_width=True, hide_index=True)
            nb = metrics.get("notebook_models") or []
            if nb:
                st.markdown("**Notebook-only models** (update RMSE in JSON after notebook runs if desired)")
                st.dataframe(pd.DataFrame(nb), use_container_width=True, hide_index=True)
            with st.expander("Raw JSON"):
                st.json(metrics)

    with st.expander("Dataset summary (JSON)"):
        st.json(summary if summary else {"hint": "Run python3 -m pipeline"})


if __name__ == "__main__":
    main()
