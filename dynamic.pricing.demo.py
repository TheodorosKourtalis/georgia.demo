import streamlit as st
import datetime
import random
import pandas as pd
import pytz
import time

# --- Global Product Data (cached for performance) ---
@st.cache_resource
def get_products():
    # Two products with fixed starting prices and randomly generated ending prices
    # within 30%-70% of the starting price.
    products = [
        {
            "name": "Product A",
            "start_price": 100,
            "end_price": random.uniform(0.30 * 100, 0.70 * 100)
        },
        {
            "name": "Product B",
            "start_price": 200,
            "end_price": random.uniform(0.30 * 200, 0.70 * 200)
        }
    ]
    return products

products = get_products()

def get_cycle(current_dt):
    """
    Determines the active price degradation cycle based on Greek time.
    - If current time is before 5:00 AM, the cycle is from yesterday 7:00 AM to today 5:00 AM.
    - If current time is between 5:00 and 7:00 AM, the previous cycle has ended.
    - Otherwise, the cycle is from today 7:00 AM to tomorrow 5:00 AM.
    """
    tz = pytz.timezone("Europe/Athens")
    current_dt = current_dt.astimezone(tz)
    today = current_dt.date()
    current_time = current_dt.time()

    if current_time < datetime.time(5, 0):
        yesterday = today - datetime.timedelta(days=1)
        cycle_start = tz.localize(datetime.datetime.combine(yesterday, datetime.time(7, 0)))
        cycle_end = tz.localize(datetime.datetime.combine(today, datetime.time(5, 0)))
    elif current_time < datetime.time(7, 0):
        yesterday = today - datetime.timedelta(days=1)
        cycle_start = tz.localize(datetime.datetime.combine(yesterday, datetime.time(7, 0)))
        cycle_end = tz.localize(datetime.datetime.combine(today, datetime.time(5, 0)))
    else:
        cycle_start = tz.localize(datetime.datetime.combine(today, datetime.time(7, 0)))
        cycle_end = tz.localize(datetime.datetime.combine(today + datetime.timedelta(days=1), datetime.time(5, 0)))
    return cycle_start, cycle_end

def calculate_price(product, current_dt):
    """
    Computes the current price using a linear interpolation function:
    
        f(t) = start_price + (end_price - start_price) * ((t - t_start) / (t_end - t_start))
    
    where t_start and t_end define the current degradation cycle.
    For times between 5:00 and 7:00, the final (degraded) price is returned.
    """
    tz = pytz.timezone("Europe/Athens")
    current_dt = current_dt.astimezone(tz)

    # Between 5:00 and 7:00, return the final price.
    if datetime.time(5, 0) <= current_dt.time() < datetime.time(7, 0):
        return product["end_price"]

    cycle_start, cycle_end = get_cycle(current_dt)
    if current_dt < cycle_start:
        return product["start_price"]
    if current_dt > cycle_end:
        return product["end_price"]

    total_duration = (cycle_end - cycle_start).total_seconds()
    elapsed = (current_dt - cycle_start).total_seconds()
    fraction = elapsed / total_duration
    current_price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
    return current_price

# --- Sidebar Navigation ---
page = st.sidebar.selectbox("Select Page", options=["Demo", "Console"])
tz = pytz.timezone("Europe/Athens")

if page == "Demo":
    st.title("Product Demo Page")
    # A placeholder for dynamic price updates
    demo_placeholder = st.empty()
    while True:
        now = datetime.datetime.now(tz)
        demo_text = f"**Current Greek Time:** {now.strftime('%H:%M:%S')}\n\n"
        demo_text += "Prices degrade linearly from **7:00 AM** (cycle start) to **5:00 AM** (cycle end) for all users.\n\n"
        for product in products:
            current_price = calculate_price(product, now)
            demo_text += f"**{product['name']}**: {current_price:.4f} €\n\n"
        demo_placeholder.markdown(demo_text)
        time.sleep(2)

elif page == "Console":
    st.title("Console: Detailed Analytics & Full Price History")
    # Create two placeholders: one for analytics and one for the table
    analytics_placeholder = st.empty()
    table_placeholder = st.empty()
    
    while True:
        now = datetime.datetime.now(tz)
        cycle_start, cycle_end = get_cycle(now)
        total_duration = (cycle_end - cycle_start).total_seconds()
        elapsed = (now - cycle_start).total_seconds()
        
        # Markdown with mathematical explanation
        analytic_text = f"""
        ### Price Degradation Function
        
        The current price is computed using a **linear interpolation** function:
        
        \\[
        f(t) = start\\_price + (end\\_price - start\\_price) \\times \\frac{{t - t_{{start}}}}{{t_{{end}} - t_{{start}}}}
        \\]
        
        **Cycle Details:**  
        - **Cycle Start (tₛ):** {cycle_start.strftime("%H:%M:%S")}  
        - **Cycle End (tₑ):** {cycle_end.strftime("%H:%M:%S")}  
        - **Current Time (t):** {now.strftime("%H:%M:%S")}  
        - **Elapsed Time:** {elapsed:.2f} seconds  
        - **Total Duration:** {total_duration:.2f} seconds  
        """
        analytics_placeholder.markdown(analytic_text)
        
        # Build the full price history table from cycle start to current time at 2-second intervals.
        schedule = []
        current_dt = cycle_start
        # Note: For long cycles, this table can become large. This demo assumes moderate usage.
        while current_dt <= now:
            row = {"Time": current_dt.strftime("%H:%M:%S")}
            for product in products:
                price = calculate_price(product, current_dt)
                row[product["name"]] = f"{price:.4f} €"
            schedule.append(row)
            current_dt += datetime.timedelta(seconds=2)
        
        df = pd.DataFrame(schedule)
        table_placeholder.dataframe(df, use_container_width=True)
        
        time.sleep(2)
