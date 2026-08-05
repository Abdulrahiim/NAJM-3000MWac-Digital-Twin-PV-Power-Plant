"""NAJM-3000 Digital Twin — optional read-only results viewer.

Run with::

    streamlit run notebooks/streamlit_viewer.py

This is a **thin UI shell**. All engineering logic lives in
``najm3000.reporting.viewer``, which is covered by the test suite; this file
only arranges the results on screen. It reads configuration and runs the
physics chain in-process. It never writes to the configuration, never
connects to SCADA, and never downloads weather.

Everything displayed is produced from SYNTHETIC_SOFTWARE_TEST inputs and is
labeled: SYNTHETIC DEMONSTRATION — NOT PRODUCTION VALIDATION.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from najm3000 import SYNTHETIC_DISCLAIMER, __version__
from najm3000.config.loader import ConfigError
from najm3000.reporting.plots import (
    plot_irradiance,
    plot_loss_waterfall,
    plot_power_chain,
    plot_temperature,
)
from najm3000.reporting.viewer import (
    ViewerError,
    available_blocks,
    load_viewer_context,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Defaults are overridable by environment variable so the viewer can be pointed
# at a different configuration set (for example the test fixtures) without
# editing this file.
DEFAULT_CONFIG_DIR = os.environ.get(
    "NAJM3000_CONFIG_DIR", str(REPO_ROOT / "config")
)
DEFAULT_ASSUMPTIONS_REGISTER = os.environ.get(
    "NAJM3000_ASSUMPTIONS_REGISTER", str(REPO_ROOT / "ASSUMPTIONS_REGISTER.md")
)
DEFAULT_GAP_REGISTER = os.environ.get(
    "NAJM3000_GAP_REGISTER", str(REPO_ROOT / "DATA_GAP_REGISTER.md")
)
DEFAULT_DAY = os.environ.get("NAJM3000_DAY", "2025-06-21")

st.set_page_config(page_title="NAJM-3000 Digital Twin (POC)", layout="wide")

st.title("NAJM-3000 Digital Twin — Results Viewer")
st.error(
    f"**{SYNTHETIC_DISCLAIMER}**\n\n"
    "NAJM-3000 is under construction and pre-operational. This model is "
    "**not calibrated** and **not validated**. Nothing shown here represents "
    "actual or predicted NAJM-3000 production."
)

with st.sidebar:
    st.header("Run settings")
    config_dir = Path(
        st.text_input("Configuration directory", value=DEFAULT_CONFIG_DIR)
    )
    assumptions_register = Path(
        st.text_input("Assumptions register", value=DEFAULT_ASSUMPTIONS_REGISTER)
    )
    gap_register = Path(
        st.text_input("Data gap register", value=DEFAULT_GAP_REGISTER)
    )
    day = st.text_input("Simulation day (YYYY-MM-DD)", value=DEFAULT_DAY)
    try:
        block_names = available_blocks(config_dir)
    except ConfigError as exc:
        st.error(f"Configuration invalid:\n\n{exc}")
        st.stop()
    block = st.selectbox("Block", block_names)
    st.caption(f"najm3000 v{__version__}")

try:
    context = load_viewer_context(
        config_dir=config_dir,
        assumptions_register=assumptions_register,
        gap_register=gap_register,
        block=block,
        day=day,
    )
except (ConfigError, ViewerError) as exc:
    st.error(f"Could not run the block:\n\n{exc}")
    st.stop()

status_columns = st.columns(4)
status_columns[0].metric("Net block energy [kWh]", f"{context.energy_kwh():,.1f}")
status_columns[1].metric("Weather source", context.weather_classification)
status_columns[2].metric("Calibration", context.calibration_status)
status_columns[3].metric("Validation", context.validation_status)

(
    tab_power,
    tab_losses,
    tab_provenance,
    tab_assumptions,
) = st.tabs(
    ["Irradiance & temperature", "Losses", "Provenance", "Assumptions & risk"]
)

with tab_power:
    st.caption(SYNTHETIC_DISCLAIMER)
    st.pyplot(plot_irradiance(context.result))
    st.pyplot(plot_temperature(context.result))
    st.pyplot(plot_power_chain(context.result))

with tab_losses:
    st.caption(SYNTHETIC_DISCLAIMER)
    st.pyplot(plot_loss_waterfall(context.result))
    st.subheader("Loss ledger")
    st.dataframe(context.waterfall, width="stretch")

with tab_provenance:
    st.caption(SYNTHETIC_DISCLAIMER)
    st.subheader("Parameter provenance")
    st.write(
        f"{len(context.provenance.rows)} parameters, each traceable to a "
        "source ID or a registered assumption ID."
    )
    st.json(context.provenance.summary_by_status())
    st.dataframe(context.provenance.to_dataframe(), width="stretch")

with tab_assumptions:
    st.caption(SYNTHETIC_DISCLAIMER)
    st.subheader("Assumed, conflicting, and missing parameters")
    st.write(
        "Risk levels are read from `ASSUMPTIONS_REGISTER.md` — they are not "
        "derived or inferred here."
    )
    if context.assumptions.unregistered_ids:
        st.warning(
            "Unregistered assumption IDs found: "
            + ", ".join(context.assumptions.unregistered_ids)
        )
    st.json(context.assumptions.summary_by_risk())
    st.dataframe(context.assumptions.to_dataframe(), width="stretch")

st.divider()
st.caption(f"{SYNTHETIC_DISCLAIMER} — NAJM-3000 Digital Twin POC v{__version__}")
