import redis
import streamlit as st

from bar_chart import build_dataframe

r = redis.Redis()

def render_dequeued_batch(batch, index):
    batch_items = []
    for item, priority in batch:
        item_decoded = item.decode()
        identifier = item_decoded.split("|")[0]
        chunk = item_decoded.split("|")[1]
        color = "#D3D3D3"
        size = 35
        batch_items.append(
            f"<div style='display:inline-block;text-align:center;margin-right:15px;margin-bottom:0px;'>"
            f"<div style='width:{size}px;height:{size}px;background-color:{color};'>{chunk}</div>"
            f"<div style='color:black;'>{identifier}</div>"
            f"</div>")
    st.write(f"Batch {index + 1}")
    markdown_to_write = " ".join(batch_items)
    st.markdown(markdown_to_write, unsafe_allow_html=True)
    st.divider()


def dequeue(dequeue_number, strategies):
    for strategy in strategies:
        dequeued_items = r.zpopmin(strategy["queue_name"], count=dequeue_number)
        if f"dequeued_{strategy['queue_name']}" not in st.session_state:
            st.session_state[f"dequeued_{strategy['queue_name']}"] = []
        st.session_state[f"dequeued_{strategy['queue_name']}"].append(dequeued_items)

        if st.session_state.dataframes[strategy["queue_name"]] is not None:
            st.session_state.dataframes[strategy["queue_name"]] = build_dataframe(
                strategy["function"],
                queue_name=strategy["queue_name"],
                identifier="n/a",
                number=0,
                start=0
            )