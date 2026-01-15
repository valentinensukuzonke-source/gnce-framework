# ui/components/input_editor.py
from __future__ import annotations

from typing import Any, Dict, Tuple
from pathlib import Path
import json

import streamlit as st


def input_editor(
    config_path: Path,
    mode: str,
    regulator_view: bool,
    edit_before_run: bool,
) -> Tuple[Dict[str, Any], bool]:
    """
    GNCE v0.4 Input Editor

    - Loads the selected JSON config from disk.
    - If `edit_before_run` is False → no widget, just parse & return.
    - If `edit_before_run` is True → show editable JSON in the sidebar,
      backed by st.session_state["gn_input_json_text"].

    Returns:
        (payload_dict, is_valid_json)
    """
    session_key_text = "gn_input_json_text"

    # ------------------------------------------------------------------
    # 1. Load the raw file text
    # ------------------------------------------------------------------
    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except Exception as e:
        st.sidebar.error(f"Failed to load config: {e}")
        return {}, False

    # ------------------------------------------------------------------
    # 2. If not editing, do NOT create any widget.
    #    Just parse and return.
    # ------------------------------------------------------------------
    if not edit_before_run:
        try:
            payload = json.loads(raw_text)
            return payload, True
        except Exception as e:
            st.sidebar.error(f"Config JSON is invalid: {e}")
            return {}, False

    # ------------------------------------------------------------------
    # 3. Editing enabled: initialise session_state BEFORE widget.
    # ------------------------------------------------------------------
    # Only override if key is missing OR we switched to a new file.
    current_file_key = "gn_current_input_file"
    previous_path = st.session_state.get(current_file_key)

    if (
        "gn_input_json_text" not in st.session_state
        or previous_path != str(config_path)
    ):
        st.session_state[session_key_text] = raw_text
        st.session_state[current_file_key] = str(config_path)

    # At this point, st.session_state[session_key_text] holds the text
    # that will back the widget.

    # ------------------------------------------------------------------
    # 4. Render the editor widget in the sidebar
    # ------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### 🧾 GNCE Input JSON (editable)")
        st.caption(
            "You are in **LAB Mode** with input override enabled. "
            "Edits here will be used for the next GNCE run."
        )

        # IMPORTANT:
        # - We use `key=session_key_text`.
        # - We do NOT reassign st.session_state[session_key_text] after this.
        edited_text = st.text_area(
            label="Edit input JSON",
            key=session_key_text,
            height=260,
        )

    # `edited_text` and `st.session_state[session_key_text]` now point to
    # the same underlying value – no manual assignment needed.

    # ------------------------------------------------------------------
    # 5. Parse the JSON from the current text
    # ------------------------------------------------------------------
    try:
        payload = json.loads(edited_text)
        return payload, True
    except Exception as e:
        with st.sidebar:
            st.error(f"Edited JSON is invalid: {e}")
        return {}, False
