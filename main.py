
import streamlit as st
import pandas as pd
import redis
from uuid import uuid4
from collections import defaultdict

r = redis.Redis()


# Strategies

def punish_new_ones(number: int=2, base_priority: int = 0, spacing: int = 10, queue_name: str = "test_queue"):
    """
    Every time a new item is added to the queue, it will punish a little bit the base_priority
    """

    identifier = uuid4().hex[:5]
    priority_counter = int(r.get("priority_counter") or 0)  # type: ignore
    for i in range(number):
        priority = (base_priority + int(priority_counter))+ i * spacing
        r.zadd(queue_name, {f"p_{identifier}|{i}": priority})

    r.incr("priority_counter")

def use_base_priority_always(number: int=2, base_priority: int = 0, spacing: int = 10, queue_name:str = "test_queue"):
    """
    Every time a new item is added to the queue, it will punish a little bit the base_priority
    """

    identifier = uuid4().hex[:5]
    for i in range(number):
        priority = base_priority + i * spacing
        r.zadd(queue_name, {f"p_{identifier}|{i}": priority})


# Generate dataset to plot
def dump_queue(queue_name):
    return r.zrange(queue_name, 0, -1, withscores=True)

def build_dataframe(prioritization_strategy, queue_name: str, number: int, base_priority: int = 0, spacing: int = 10):

    prioritization_strategy(number=number, base_priority=base_priority, spacing=spacing, queue_name=queue_name)

    dump = dump_queue(queue_name)

    priorities = list({int(p) for _, p in dump})
    chart_data = pd.DataFrame.from_dict({"priorities": priorities})

    packages = defaultdict(list)

    for item, priority in dump:
        package, chunk = item.decode().split("|")
        packages[package].append(priority)

    for package, package_entries in packages.items():
        chart_data[package] = None

        for entry in package_entries:
            chart_data.loc[chart_data["priorities"] == entry, package] = 1

    return chart_data


def clean_chart(dataframes, queues):
    for queue in queues:
        r.delete(queue)

    for d in dataframes:
        d.drop(index=d.index, inplace=True)

    r.set("priority_counter", 0)

def main():
    st.title("Normal Queue")
    s1 = build_dataframe(use_base_priority_always, "q1", number=10, base_priority=0, spacing=10)
    st.bar_chart(s1, x="priorities", stack=False, use_container_width=True)

    st.title("Punish new ones Queue")
    s2 = build_dataframe(punish_new_ones, "q2", number=10, base_priority=0, spacing=10)
    st.bar_chart(s2, x="priorities", stack=False, use_container_width=True)

    st.button("Insert into queue")
    st.button("Clean", on_click=lambda: clean_chart([s1,s2], ["q1", "q2"]))




if __name__ == "__main__":
    main()
