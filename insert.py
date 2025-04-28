from traceback import extract_tb
from uuid import uuid4

import pandas as pd
import streamlit as st

from bar_chart import build_dataframe

batch_size = 10
large_package = 10_000
medium_package = 2_000
small_package = 800
extra_small_package = 300
reduction_factor = 10


medium = (medium_package // reduction_factor) // 4
small = (small_package // reduction_factor) // 4
extra_small = (extra_small_package // reduction_factor) // 4


def insert_scenario_medium_then_x_small(strategies):

    M1 = insert_into_queue(medium, strategies)  # M1-Forms
    insert_into_queue_for(M1, medium, medium, strategies)  # M1-RFIs

    M2 = insert_into_queue(medium, strategies)  # M2-Forms
    insert_into_queue_for(M2, medium, medium, strategies)  # M2-RFIs
    insert_into_queue_for(M1, medium, 2 * medium, strategies)  # M1-Issues
    insert_into_queue_for(M2, medium, 2 * medium, strategies)  # M2-Issues

    S3 = insert_into_queue(small, strategies)  # S3-Forms
    insert_into_queue_for(M2, medium, 3 * medium, strategies)  # M2-Submittals
    insert_into_queue_for(S3, small, small, strategies)  # S3-RFIs
    insert_into_queue_for(M1, medium, 3 * medium, strategies)  # M1-Submittals
    insert_into_queue_for(S3, small, 2 * small, strategies)  # S3-Issues

    XS4 = insert_into_queue(extra_small, strategies)  # XS4-Forms
    insert_into_queue_for(S3, small, 3 * small, strategies)  # S3-Submittals
    insert_into_queue_for(XS4, extra_small, extra_small, strategies)  # XS4-RFIs
    insert_into_queue_for(XS4, extra_small, 2 * extra_small, strategies)  # XS4-Issues

    S5 = insert_into_queue(small, strategies)  # S5-Forms
    insert_into_queue_for(XS4, extra_small, 3 * extra_small, strategies)  # XS4-Submittals
    insert_into_queue_for(S5, small, small, strategies)  # S5-RFIs

    XS6 = insert_into_queue(extra_small, strategies)  # XS6-Forms
    insert_into_queue_for(S5, small, 2 * small, strategies)  # S5-Issues
    insert_into_queue_for(XS6, extra_small, extra_small, strategies)  # S6-RFIs

    XS7 = insert_into_queue(extra_small, strategies)  # XS7-Forms
    insert_into_queue_for(XS6, extra_small, 2 * extra_small, strategies)  # S6-Issues
    insert_into_queue_for(XS7, extra_small, extra_small, strategies)  # S7-RFIs
    insert_into_queue_for(S5, small, 3 * small, strategies)  # S5-Submittals
    insert_into_queue_for(XS6, extra_small, 3 * extra_small, strategies)  # S6-Submittals
    insert_into_queue_for(XS7, extra_small, 2 * extra_small, strategies)  # S7-Issues
    insert_into_queue_for(XS7, extra_small, 3 * extra_small, strategies)  # S7-Submittals

    XS8 = insert_into_queue(extra_small, strategies)  # XS8-Forms
    insert_into_queue_for(XS8, extra_small, extra_small, strategies)  # XS8-RFIs
    insert_into_queue_for(XS8, extra_small, 2 * extra_small, strategies)  # XS8-Issues
    insert_into_queue_for(XS8, extra_small, 3 * extra_small, strategies)  # XS8-Submittals

    XS9 = insert_into_queue(extra_small, strategies)  # XS9-Forms
    insert_into_queue_for(XS9, extra_small, extra_small, strategies)  # XS9-RFIs
    insert_into_queue_for(XS9, extra_small, 2 * extra_small, strategies)  # XS9-Issues
    insert_into_queue_for(XS9, extra_small, 3 * extra_small, strategies)  # XS9-Submittals


def insert_scenario_x_small_small_medium(strategies):
    XS1 = insert_into_queue(extra_small, strategies)  # XS1-Forms

    XS2 = insert_into_queue(extra_small, strategies)  # XS2-Forms
    insert_into_queue_for(XS1, extra_small, extra_small, strategies)  # XS1-RFIs
    insert_into_queue_for(XS1, extra_small, 2 * extra_small, strategies)  # XS1-Issues
    insert_into_queue_for(XS2, extra_small, extra_small, strategies)  # XS2-RFIs
    insert_into_queue_for(XS1, extra_small, 3 * extra_small, strategies)  # XS1-Submittals

    XS3 = insert_into_queue(extra_small, strategies)  # XS3-Forms
    insert_into_queue_for(XS2, extra_small, 2 * extra_small, strategies)  # XS2-Issues
    insert_into_queue_for(XS3, extra_small, extra_small, strategies)  # XS3-RFIs
    insert_into_queue_for(XS2, extra_small, 3 * extra_small, strategies)  # XS2-Submittals

    S4 = insert_into_queue(small, strategies)  # S4-Forms
    insert_into_queue_for(XS3, extra_small, 2 * extra_small, strategies)  # XS3-Issues
    insert_into_queue_for(S4, small, small, strategies)  # S4-RFIs
    insert_into_queue_for(XS3, extra_small, 3 * extra_small, strategies)  # XS3-Submittals

    XS5 = insert_into_queue(extra_small, strategies)
    insert_into_queue_for(S4, small, 2 * small, strategies)  # S4-Issues
    insert_into_queue_for(XS5, extra_small, extra_small, strategies)  # XS5-RFIs
    insert_into_queue_for(S4, small, 3 * small, strategies)  # S4-Submittals
    insert_into_queue_for(XS5, extra_small, 2 * extra_small, strategies)  # XS5-Issues
    insert_into_queue_for(XS5, extra_small, 3 * extra_small, strategies)  # XS5-Submittals

    M6 = insert_into_queue(medium, strategies)
    insert_into_queue_for(M6, medium, medium, strategies)  # M6-RFIs
    insert_into_queue_for(M6, medium, 2 * medium, strategies)  # M6-Issues
    insert_into_queue_for(M6, medium, 3 * medium, strategies)  # M6-Submittals

    M7 = insert_into_queue(medium, strategies)
    insert_into_queue_for(M7, medium, medium, strategies)  # M7-RFIs
    insert_into_queue_for(M7, medium, 2 * medium, strategies)  # M7-Issues
    insert_into_queue_for(M7, medium, 3 * medium, strategies)  # M7-Submittals


def insert_scenario_medium_x_small_small_medium(strategies):
    M1 = insert_into_queue(medium, strategies)
    XS2 = insert_into_queue(extra_small, strategies)

    insert_into_queue_for(M1, medium, medium, strategies)  # M1-RFIs
    insert_into_queue_for(XS2, extra_small, extra_small, strategies)  # XS2-RFIs
    insert_into_queue_for(M1, medium, 2 * medium, strategies)  # M1-Issues
    insert_into_queue_for(XS2, extra_small, 2 * extra_small, strategies)  # XS2-Issues
    insert_into_queue_for(M1, medium, 3 * medium, strategies)  # M1-Submittals
    M3 = insert_into_queue(medium, strategies)
    insert_into_queue_for(XS2, extra_small, 3 * extra_small, strategies)  # XS2-Submittals
    insert_into_queue_for(M3, medium, medium, strategies)  # M3-RFIs
    XS4 = insert_into_queue(extra_small, strategies)
    insert_into_queue_for(M3, medium, 2 * medium, strategies)  # M3-Issues
    insert_into_queue_for(XS4, extra_small, extra_small, strategies)  # XS4-RFIs
    insert_into_queue_for(M3, medium, 3 * medium, strategies)  # M3-Submittals
    S5 = insert_into_queue(small, strategies)
    insert_into_queue_for(XS4, extra_small, 2 * extra_small, strategies)  # XS4-Issues
    insert_into_queue_for(S5, small, small, strategies)  # S5-RFIs
    insert_into_queue_for(XS4, extra_small, 3 * extra_small, strategies)  # XS4-Submittals
    XS6 = insert_into_queue(extra_small, strategies)
    insert_into_queue_for(S5, small, 2 * small, strategies)  # S5-Issues
    insert_into_queue_for(XS6, extra_small, extra_small, strategies)  # XS6-RFIs
    insert_into_queue_for(S5, small, 3 * small, strategies)  # S5-Submittals
    S7 = insert_into_queue(small, strategies)
    insert_into_queue_for(XS6, extra_small, 2 * extra_small, strategies)  # XS6-Issues
    insert_into_queue_for(S7, small, small, strategies)  # S7-RFIs
    insert_into_queue_for(XS6, extra_small, 3 * extra_small, strategies)  # XS6-Submittals
    XS8 = insert_into_queue(extra_small, strategies)
    insert_into_queue_for(S7, small, 2 * small, strategies)  # S7-Issues
    insert_into_queue_for(XS8, extra_small, extra_small, strategies)  # XS8-RFIs
    insert_into_queue_for(XS8, extra_small, 2 * extra_small, strategies)  # XS8-Issues
    insert_into_queue_for(S7, small, 3 * small, strategies)  # S7-Submittals
    insert_into_queue_for(XS8, extra_small, 3 * extra_small, strategies)  # XS8-Submittals
    M9 = insert_into_queue(medium, strategies)
    insert_into_queue_for(M9, medium, medium, strategies)  # M9-RFIs
    insert_into_queue_for(M9, medium, 2 * medium, strategies)  # M9-Issues
    insert_into_queue_for(M9, medium, 3 * medium, strategies)  # M9-Submittals


def insert_into_queue_for(package_id, insert_number, start, strategies):
    for strategy in strategies:
        st.session_state.dataframes[strategy["queue_name"]] = build_dataframe(
            strategy["function"],
            queue_name=strategy["queue_name"],
            identifier=package_id,
            number=insert_number,
            start=start
        )


def insert_into_queue(insert_number, strategies) -> str:
    identifier = f"{str(st.session_state.package_number).zfill(2)}_{uuid4().hex[:6]}"  # Generate the identifier  # Generate the identifier
    for strategy in strategies:
        st.session_state.dataframes[strategy["queue_name"]] = build_dataframe(
            strategy["function"],
            queue_name=strategy["queue_name"],
            identifier=identifier,
            number=insert_number,
            start=1
        )
    st.session_state.package_number += 1
    return identifier
