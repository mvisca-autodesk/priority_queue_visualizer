from math import log
from uuid import uuid4

import redis
import streamlit as st

from bar_chart import render_bar_chart, build_dataframe
from clean import clean_all
from dequeue import render_dequeued_batch, dequeue

r = redis.Redis()


def weight_3_priority_counter_strategy(base_priority: int, priority_counter: int, index: int, spacing: int,
                                       total_number_of_tasks: int) -> int:
    weight = max(1, int(log(total_number_of_tasks, 2)))

    priority = (base_priority + priority_counter) + int((index * spacing) / weight)

    return priority


def linear_weight_priority_counter_strategy(base_priority: int, priority_counter: int, index: int, spacing: int,
                                            total_number_of_tasks: int) -> int:
    """
    Balances priorities such that large packages do not block smaller ones,
    and smaller packages do not excessively punish larger ones.
    """
    weight = max(1, int(log(total_number_of_tasks, 2)))

    priority = (base_priority + priority_counter) + int((index * spacing) / weight)

    return priority


def weight_7_priority_counter_strategy(base_priority: int, priority_counter: int, index: int, spacing: int,
                                       total_number_of_tasks: int) -> int:
    # weight = max(1, int(total_number_of_tasks ** 0.5))
    # priority = (base_priority + int(priority_counter)) + int((index * spacing) / weight)
    #
    # return priority
    weight = max(1, int(log(total_number_of_tasks, 10)))

    priority = (base_priority + priority_counter) + int((index * spacing) / weight)

    return priority


def base_priority_strategy(base_priority: int, priority_counter: int, index: int, spacing: int,
                           total_number_of_tasks: int) -> int:
    """
    Every time a new item is added to the queue, it will punish a little bit the base_priority
    """
    return base_priority + index * spacing


strategies = [
    {"name": "Base Priority", "function": base_priority_strategy, "queue_name": "q1"},
    {"name": "Log with counter", "function": weight_3_priority_counter_strategy, "queue_name": "q2"},
    {"name": "Log (2) with counter", "function": linear_weight_priority_counter_strategy, "queue_name": "q3"},
    {"name": "Log (10) with counter", "function": weight_7_priority_counter_strategy, "queue_name": "q4"},
]

batch_size = 10
large_size = 21 * batch_size
medium_size = 9 * batch_size
small_size = 5 * batch_size


def main():
    st.set_page_config(layout="wide")
    insert_number = st.sidebar.number_input("Number of items to add", min_value=1, max_value=100, value=50)

    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {strat["queue_name"]: None for strat in strategies}
    if "package_number" not in st.session_state:
        st.session_state.package_number = 1

    if st.sidebar.button("Insert into queue"):
        insert_into_queue(insert_number)

    if st.sidebar.button("Insert L1,L2,M3,S4,M5,S6,S7,S8,S9"):
        insert_scenario_large_then_small()
    if st.sidebar.button("Insert S1,S2,S3,M4,S5,L6,L7"):
        insert_into_queue(small_size)
        insert_into_queue(small_size)
        insert_into_queue(small_size)
        insert_into_queue(medium_size)
        insert_into_queue(small_size)
        insert_into_queue(large_size)
        insert_into_queue(large_size)
    if st.sidebar.button("Insert L1,S2,L3,S4,M5,S6,M7,S8,L9"):
        insert_into_queue(large_size)
        insert_into_queue(small_size)
        insert_into_queue(large_size)
        insert_into_queue(small_size)
        insert_into_queue(medium_size)
        insert_into_queue(small_size)
        insert_into_queue(medium_size)
        insert_into_queue(small_size)
        insert_into_queue(large_size)

    dequeue_number = st.sidebar.number_input("Number to dequeue", min_value=1, max_value=500, value=100)

    if st.sidebar.button("Dequeue"):
        dequeue(dequeue_number, strategies)
    if st.sidebar.button("Dequeue 3 rounds"):
        for _ in range(3):
            dequeue(dequeue_number, strategies)
    if st.sidebar.button("Dequeue 5 rounds"):
        for _ in range(5):
            dequeue(dequeue_number, strategies)

    # Render charts dynamically
    for strategy in strategies:
        if st.session_state.dataframes[strategy["queue_name"]] is not None:
            render_bar_chart(st.session_state.dataframes[strategy["queue_name"]], strategy["name"])

    # Render dequeued items dynamically
    columns = st.columns(len(strategies))
    for col, strategy in zip(columns, strategies):
        with col:
            if f"dequeued_{strategy['queue_name']}" in st.session_state and st.session_state[
                f"dequeued_{strategy['queue_name']}"] is not None:
                st.title(f"{strategy['name']} Queue: dequeued")
                for i, batch in enumerate(st.session_state[f"dequeued_{strategy['queue_name']}"]):
                    render_dequeued_batch(batch, i)

    st.sidebar.button("Clean", on_click=lambda: clean_all(strategies))


def insert_scenario_large_then_small():
    """
    Large, Large, Medium, Small, Medium, Small, Small, Small, Small
    """
    large = 100
    medium = 50
    small = 20
    L1 = insert_into_queue(large)  # L1-Forms
    insert_into_queue_for(L1, large, large)  # L1-RFIs

    L2 = insert_into_queue(large)  # L2-Forms
    insert_into_queue_for(L2, large, large)  # L2-RFIs
    insert_into_queue_for(L1, large, 2 * large)  # L1-Issues
    insert_into_queue_for(L2, large, 2 * large)  # L2-Issues

    M3 = insert_into_queue(medium)  # M3-Forms
    insert_into_queue_for(L2, large, 3 * large)  # L2-Submittals
    insert_into_queue_for(M3, medium, medium)  # M3-RFIs
    insert_into_queue_for(L1, large, 3 * large)  # L1-Submittals
    insert_into_queue_for(M3, medium, 2 * medium)  # M3-Issues

    S4 = insert_into_queue(small)  # S4-Forms
    insert_into_queue_for(M3, medium, 3 * medium)  # M3-Submittals
    insert_into_queue_for(S4, small, small)  # S4-RFIs
    insert_into_queue_for(S4, small, 2 * small)  # S4-Issues

    M5 = insert_into_queue(medium)  # M5-Forms
    insert_into_queue_for(S4, small, 3 * small)  # S4-Submittals
    insert_into_queue_for(M5, medium, medium)  # M5-RFIs

    S6 = insert_into_queue(small)  # S6-Forms
    insert_into_queue_for(M5, medium, 2 * medium)  # M5-Issues
    insert_into_queue_for(S6, small, small)  # M6-RFIs

    S7 = insert_into_queue(small)  # S7-Forms
    insert_into_queue_for(S6, small, 2 * small)  # M6-Issues
    insert_into_queue_for(S7, small, small)  # M7-RFIs
    insert_into_queue_for(M5, medium, 3 * medium)  # M5-Submittals
    insert_into_queue_for(S6, small, 3 * small)  # M6-Submittals
    insert_into_queue_for(S7, small, 2 * small)  # M7-Issues
    insert_into_queue_for(S7, small, 3 * small)  # M7-Submittals

    S8 = insert_into_queue(small)  # S8-Forms
    insert_into_queue_for(S8, small, small)  # S8-RFIs
    insert_into_queue_for(S8, small, 2 * small)  # S8-Issues
    insert_into_queue_for(S8, small, 3 * small)  # S8-Submittals

    S9 = insert_into_queue(small)  # S9-Forms
    insert_into_queue_for(S9, small, small)  # S9-RFIs
    insert_into_queue_for(S9, small, 2 * small)  # S9-Issues
    insert_into_queue_for(S9, small, 3 * small)  # S9-Submittals


def insert_into_queue_for(package_id, insert_number, start):
    for strategy in strategies:
        st.session_state.dataframes[strategy["queue_name"]] = build_dataframe(
            strategy["function"],
            queue_name=strategy["queue_name"],
            identifier=package_id,
            number=insert_number,
            start=start
        )


def insert_into_queue(insert_number) -> str:
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


if __name__ == "__main__":
    main()
