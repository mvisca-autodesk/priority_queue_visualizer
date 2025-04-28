from math import log

import redis
import streamlit as st

from bar_chart import render_bar_chart_for
from clean import clean_all
from dequeue import dequeue, render_dequeued_items_for
from insert import insert_into_queue, insert_scenario_medium_then_x_small, insert_scenario_x_small_small_medium, \
    insert_scenario_medium_x_small_small_medium

r = redis.Redis()



def log_weight_priority_counter_strategy(base_priority: int, priority_counter: int, index: int, spacing: int,
                                         total_number_of_tasks: int, queue_length: int) -> int:
    """
    Balances priorities such that large packages do not block smaller ones,
    and smaller packages do not excessively punish larger ones.

    :param: base_priority: The base priority for the package
    :param: priority_counter: The number of times all packages have requested items to be prioritized
    :param: index: The index of the batch of total_number_of_tasks
    :param: spacing: A value to space out the priorities
    :param: total_number_of_tasks: The total number of items the package is requesting to be prioritized
    :param: queue_length: The length of the priority queue

    :return: The priority for the batch of items. A smaller number means higher priority.
    """
    weight = max(1, int(log(total_number_of_tasks, 5)))

    priority = (base_priority + priority_counter) + int((index * spacing) / weight)

    return priority

def log_weight_queue_length_strategy(base_priority: int, priority_counter: int, index: int, spacing: int,
                                         total_number_of_tasks: int, queue_length: int) -> int:
    """

    """
    # weight = max(1, int(log(total_number_of_tasks, 5)))
    # modulus = priority_counter % spacing # add this to the base_priority

    offset = priority_counter * max(1, int(log(queue_length + 1, 2)))
    priority = (base_priority + offset) + (index * spacing)

    return priority


def fair_strategy(base_priority: int, priority_counter: int, index: int, spacing: int,
                  total_number_of_tasks: int, queue_length: int) -> int:
    """
    Packages will enqueue a number of items multiple times one for each AssetType. These will be batched by a batch_size, the batch will be indicated by the index, and
    the priority of each batch will be calculated by this function.

    We do not want large packages to block smaller ones.
    We do not want a frequent number of smaller packages to punish larger ones.
    We want to balance the priorities such that things are spaced out for fairness, slightly punishing larger packages.
    The first packages in the queue should not be overly punished as more packages are added.

    :param: base_priority: The base priority for the package
    :param: priority_counter: The number of times all packages have requested items to be prioritized
    :param: index: The index of the batch of total_number_of_tasks
    :param: spacing: A value to space out the priorities
    :param: total_number_of_tasks: The total number of items the package is requesting to be prioritized
    :param: queue_length: The length of the priority queue

    :return: The priority for the batch of items. A smaller number means higher priority.
    """
    offset = priority_counter * max(1, int(log(queue_length + 1, 2) ** 1.5 + log(queue_length + 1, 10)))
    weight = max(1, int(log(total_number_of_tasks, 5)))
    spacing_offset = index * spacing
    priority = base_priority + offset + spacing_offset
    return priority


def base_priority_strategy(base_priority: int, priority_counter: int, index: int, spacing: int,
                           total_number_of_tasks: int, queue_length: int) -> int:
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
        "name": "Log (2) Priority * Queue Length",
        "function": log_weight_queue_length_strategy,
        "queue_name": "q2"
    },
    {
        "name": "Log (5) Weight Priority Counter",
        "function": log_weight_priority_counter_strategy,
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
