from uuid import uuid4

from bar_chart import build_dataframe
import streamlit as st

batch_size = 10
large_size = 21 * batch_size
medium_size = 9 * batch_size
small_size = 5 * batch_size
large = 100
medium = 50
small = 20

def insert_scenario_large_then_small(strategies):
    """
    Large, Large, Medium, Small, Medium, Small, Small, Small, Small
    """
    L1 = insert_into_queue(large, strategies)  # L1-Forms
    insert_into_queue_for(L1, large, large, strategies)  # L1-RFIs

    L2 = insert_into_queue(large, strategies)  # L2-Forms
    insert_into_queue_for(L2, large, large, strategies)  # L2-RFIs
    insert_into_queue_for(L1, large, 2 * large, strategies)  # L1-Issues
    insert_into_queue_for(L2, large, 2 * large, strategies)  # L2-Issues

    M3 = insert_into_queue(medium, strategies)  # M3-Forms
    insert_into_queue_for(L2, large, 3 * large, strategies)  # L2-Submittals
    insert_into_queue_for(M3, medium, medium, strategies)  # M3-RFIs
    insert_into_queue_for(L1, large, 3 * large, strategies)  # L1-Submittals
    insert_into_queue_for(M3, medium, 2 * medium, strategies)  # M3-Issues

    S4 = insert_into_queue(small, strategies)  # S4-Forms
    insert_into_queue_for(M3, medium, 3 * medium, strategies)  # M3-Submittals
    insert_into_queue_for(S4, small, small, strategies)  # S4-RFIs
    insert_into_queue_for(S4, small, 2 * small, strategies)  # S4-Issues

    M5 = insert_into_queue(medium, strategies)  # M5-Forms
    insert_into_queue_for(S4, small, 3 * small, strategies)  # S4-Submittals
    insert_into_queue_for(M5, medium, medium, strategies)  # M5-RFIs

    S6 = insert_into_queue(small, strategies)  # S6-Forms
    insert_into_queue_for(M5, medium, 2 * medium, strategies)  # M5-Issues
    insert_into_queue_for(S6, small, small, strategies)  # M6-RFIs

    S7 = insert_into_queue(small, strategies)  # S7-Forms
    insert_into_queue_for(S6, small, 2 * small, strategies)  # M6-Issues
    insert_into_queue_for(S7, small, small, strategies)  # M7-RFIs
    insert_into_queue_for(M5, medium, 3 * medium, strategies)  # M5-Submittals
    insert_into_queue_for(S6, small, 3 * small, strategies)  # M6-Submittals
    insert_into_queue_for(S7, small, 2 * small, strategies)  # M7-Issues
    insert_into_queue_for(S7, small, 3 * small, strategies)  # M7-Submittals

    S8 = insert_into_queue(small, strategies)  # S8-Forms
    insert_into_queue_for(S8, small, small, strategies)  # S8-RFIs
    insert_into_queue_for(S8, small, 2 * small, strategies)  # S8-Issues
    insert_into_queue_for(S8, small, 3 * small, strategies)  # S8-Submittals

    S9 = insert_into_queue(small, strategies)  # S9-Forms
    insert_into_queue_for(S9, small, small, strategies)  # S9-RFIs
    insert_into_queue_for(S9, small, 2 * small, strategies)  # S9-Issues
    insert_into_queue_for(S9, small, 3 * small, strategies)  # S9-Submittals

def insert_scenario_small_medium_large(strategies):
    insert_into_queue(small_size, strategies)
    insert_into_queue(small_size, strategies)
    insert_into_queue(small_size, strategies)
    insert_into_queue(medium_size, strategies)
    insert_into_queue(small_size, strategies)
    insert_into_queue(large_size, strategies)
    insert_into_queue(large_size, strategies)

def insert_scenario_large_small_medium_large(strategies):
    insert_into_queue(large_size, strategies)
    insert_into_queue(small_size, strategies)
    insert_into_queue(large_size, strategies)
    insert_into_queue(small_size, strategies)
    insert_into_queue(medium_size, strategies)
    insert_into_queue(small_size, strategies)
    insert_into_queue(medium_size, strategies)
    insert_into_queue(small_size, strategies)
    insert_into_queue(large_size, strategies)

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