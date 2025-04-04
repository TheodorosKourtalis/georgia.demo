import streamlit as st
import datetime
import random
import pandas as pd
import pytz
import time

# Common update interval in seconds.
UPDATE_INTERVAL = 5

# --- Global Product Data (cached for performance) ---
@st.cache_resource
def get_products():
    products = [
        {
            "name": "Product A",
            "start_price": 100.0,
            "end_price": random.uniform(0.30 * 100.0, 0.70 * 100.0)
        },
        {
            "name": "Product B",
            "start_price": 200.0,
            "end_price": random.uniform(0.30 * 200.0, 0.70 * 200.0)
        }
    ]
    return products

products = get_products()

def get_cycle(current_dt):
    """
    Determines the active degradation cycle.
    The cycle starts at 05:00 (Europe/Athens time) and lasts 22 hours.
    If the current time is before 05:00, the cycle start is set to yesterday at 05:00.
    """
    tz = pytz.timezone("Europe/Athens")
    current_dt = current_dt.astimezone(tz)
    today = current_dt.date()
    if current_dt.time() >= datetime.time(5, 0):
        cycle_start = tz.localize(datetime.datetime.combine(today, datetime.time(5, 0)))
    else:
        yesterday = today - datetime.timedelta(days=1)
        cycle_start = tz.localize(datetime.datetime.combine(yesterday, datetime.time(5, 0)))
    cycle_end = cycle_start + datetime.timedelta(hours=22)
    return cycle_start, cycle_end

def get_current_scheduled_time(current_dt):
    """
    Floors the time elapsed since cycle start to the nearest UPDATE_INTERVAL.
    This yields a common “scheduled calculation time” for all users.
    """
    cycle_start, _ = get_cycle(current_dt)
    delta = (current_dt - cycle_start).total_seconds()
    floor_delta = int(delta // UPDATE_INTERVAL) * UPDATE_INTERVAL
    scheduled_time = cycle_start + datetime.timedelta(seconds=floor_delta)
    return scheduled_time

@st.cache_data(ttl=UPDATE_INTERVAL)
def get_global_scheduled_time():
    """
    Returns the globally cached scheduled time computed on the server.
    With a TTL equal to the update interval, all users receive the same value.
    """
    tz = pytz.timezone("Europe/Athens")
    now = datetime.datetime.now(tz)
    return get_current_scheduled_time(now)

def calculate_price(product, scheduled_time):
    """
    Computes the price using linear interpolation based on the scheduled time:
    
    $$ f(t) = \text{start\\_price} + (\text{end\\_price} - \text{start\\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}} $$
    
    This calculation uses the common scheduled time.
    """
    cycle_start, cycle_end = get_cycle(scheduled_time)
    total_duration = (cycle_end - cycle_start).total_seconds()
    elapsed = (scheduled_time - cycle_start).total_seconds()
    fraction = elapsed / total_duration
    price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
    return price

# --- Sidebar Navigation ---
page = st.sidebar.selectbox("Select Page", options=["Demo", "Console"])
tz = pytz.timezone("Europe/Athens")
now = datetime.datetime.now(tz)
scheduled_time = get_global_scheduled_time()

if page == "Demo":
    st.title("Eco Happy Product Demo")
    demo_placeholder = st.empty()
    # Loop to update the demo output every UPDATE_INTERVAL seconds.
    while True:
        now = datetime.datetime.now(tz)
        scheduled_time = get_global_scheduled_time()
        demo_text = (
            f"**Current Greek Time:** {now.strftime('%H:%M:%S')}  \n"
            f"**Scheduled Calculation Time:** {scheduled_time.strftime('%H:%M:%S')}\n\n"
            "Prices degrade linearly from **05:00** (cycle start) over 22 hours.\n\n"
        )
        for product in products:
            price = calculate_price(product, scheduled_time)
            demo_text += (
                f"**{product['name']}**: {price:.8f} €  \n"
                f"*Calculated at {scheduled_time.strftime('%H:%M:%S')}*\n\n"
            )
        demo_placeholder.markdown(demo_text)
        time.sleep(UPDATE_INTERVAL)
        demo_placeholder.empty()

elif page == "Console":
    st.title("Eco Happy Console: Analytics & Price History")
    # Create dedicated placeholders for each dynamic section.
    latex_placeholder = st.empty()
    details_placeholder = st.empty()
    table_placeholder = st.empty()
    download_placeholder = st.empty()
    
    while True:
        now = datetime.datetime.now(tz)
        cycle_start, cycle_end = get_cycle(now)
        total_duration = (cycle_end - cycle_start).total_seconds()
        scheduled_time = get_global_scheduled_time()
        elapsed_time = (scheduled_time - cycle_start).total_seconds()
        
        # Update LaTeX formula.
        latex_placeholder.latex(
            r"f(t) = \text{start\_price} + (\text{end\_price} - \text{start\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}}"
        )
        # Update cycle details.
        details = f"""
**Cycle Details:**

- **Cycle Start (tₛ):** {cycle_start.strftime("%H:%M:%S")}
- **Cycle End (tₑ):** {cycle_end.strftime("%H:%M:%S")}
- **Scheduled Calculation Time (t):** {scheduled_time.strftime("%H:%M:%S")}
- **Elapsed Time:** {elapsed_time:.8f} seconds
- **Total Duration:** {total_duration:.8f} seconds
        """
        details_placeholder.markdown(details)
        
        # Build full price history table from cycle start to scheduled time in UPDATE_INTERVAL steps.
        schedule = []
        current_time = cycle_start
        while current_time <= scheduled_time:
            row = {"Time": current_time.strftime("%H:%M:%S")}
            for product in products:
                delta = (current_time - cycle_start).total_seconds()
                fraction = delta / total_duration
                price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
                row[product["name"]] = f"{price:.8f} €"
            schedule.append(row)
            current_time += datetime.timedelta(seconds=UPDATE_INTERVAL)
        
        df = pd.DataFrame(schedule)
        if not df.empty:
            if len(df) > 100:
                table_placeholder.markdown("### First 100 Entries")
                table_placeholder.dataframe(df.head(100), use_container_width=True)
                table_placeholder.markdown("### Last 100 Entries")
                table_placeholder.dataframe(df.tail(100), use_container_width=True)
            else:
                table_placeholder.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        download_placeholder.download_button(
            label="Download Full Price History",
            data=csv,
            file_name="price_history.csv",
            mime="text/csv",
            key="download_full_history"
        )
        time.sleep(UPDATE_INTERVAL)
        latex_placeholder.empty()
        details_placeholder.empty()
        table_placeholder.empty()
        download_placeholder.empty()
