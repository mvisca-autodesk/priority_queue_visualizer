from math import log

import redis
import streamlit as st

from bar_chart import render_bar_chart_for
from clean import clean_all
from dequeue import dequeue, render_dequeued_items_for
from insert import insert_into_queue, insert_scenario_medium_then_x_small, insert_scenario_x_small_small_medium, \
    insert_scenario_medium_x_small_small_medium

r = redis.Redis()



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
    {
        "name": "Base Priority",
        "function": base_priority_strategy,
        "queue_name": "q1"
    },
    {
        "name": "Log (10) with counter",
        "function": weight_7_priority_counter_strategy,
        "queue_name": "q2"
    },
    {
        "name": "Log (2) with counter",
        "function": linear_weight_priority_counter_strategy,
        "queue_name": "q3"
    },
]


def main():
    st.set_page_config(layout="wide")
    insert_number = st.sidebar.number_input("Number of items to add", min_value=1, max_value=10_000, value=50)

    if "dataframes" not in st.session_state:
        st.session_state.dataframes = {strat["queue_name"]: None for strat in strategies}
    if "package_number" not in st.session_state:
        st.session_state.package_number = 1

    if st.sidebar.button("Insert into queue"):
        insert_into_queue(insert_number, strategies)

    if st.sidebar.button("Insert M1,M2,S3,S4,S5,XS6,XS7,XS8,XS9"):
        insert_scenario_medium_then_x_small(strategies)
    if st.sidebar.button("Insert XS1,XS2,XS3,S4,XS5,M6,M7"):
        insert_scenario_x_small_small_medium(strategies)
    if st.sidebar.button("Insert M1,XS2,M3,XS4,S5,XS6,S7,XS8,M9"):
        insert_scenario_medium_x_small_small_medium(strategies)

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
    render_bar_chart_for(strategies)

    # Render dequeued items dynamically
    render_dequeued_items_for(strategies)

    st.sidebar.button("Clean", on_click=lambda: clean_all(strategies))


if __name__ == "__main__":
    main()
