#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  5 03:21:47 2025

@author: thodoreskourtales
"""

import streamlit as st
import datetime
import random
import pandas as pd
import pytz
import time

# Set page configuration with a plant emoji favicon.
st.set_page_config(page_title="Eco Store", page_icon="🌱", layout="wide")

# Inject custom CSS for a modern, eco-friendly look.
st.markdown(
    """
    <style>
    /* Overall background with a soft green gradient */
    .stApp {
        background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
    }
    /* Header styling */
    h1 {
        color: #2E7D32;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
        padding-top: 1rem;
    }
    /* Product card styling */
    .product-card {
        background-color: #ffffff;
        padding: 1rem;
        margin: 0.5rem;
        border-radius: 10px;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.15);
        text-align: center;
    }
    .product-card h3 {
        color: #33691E;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .product-card p {
        color: #555555;
        font-size: 0.9rem;
    }
    /* Button styling */
    .stButton>button {
        background-color: #66BB6A;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
    }
    /* Time info styling */
    .time-info {
        text-align: center;
        font-size: 1rem;
        color: #2E7D32;
        margin-bottom: 1rem;
    }
    /* Floating Cart Icon */
    .cart-icon {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 100;
    }
    .cart-icon a {
        text-decoration: none;
        color: inherit;
    }
    .cart-icon .icon {
        position: relative;
        font-size: 2rem;
    }
    .cart-icon .badge {
        position: absolute;
        top: -10px;
        right: -10px;
        background: red;
        color: white;
        border-radius: 50%;
        padding: 2px 6px;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state for cart if not already set.
if 'cart_items' not in st.session_state:
    st.session_state['cart_items'] = []

# --- Global Product Data (cached) ---
@st.cache_resource
def get_products():
    return [
        {
            "name": "Eco Backpack",
            "start_price": 50.0,
            "end_price": random.uniform(0.30 * 50.0, 0.70 * 50.0)
        },
        {
            "name": "Reusable Water Bottle",
            "start_price": 20.0,
            "end_price": random.uniform(0.30 * 20.0, 0.70 * 20.0)
        },
        {
            "name": "Organic T-Shirt",
            "start_price": 30.0,
            "end_price": random.uniform(0.30 * 30.0, 0.70 * 30.0)
        },
        {
            "name": "Eco Sunglasses",
            "start_price": 40.0,
            "end_price": random.uniform(0.30 * 40.0, 0.70 * 40.0)
        }
    ]

products = get_products()

# List of image URLs from GitHub (replace with your own URLs using raw links)
image_links = {
    "Eco Backpack": "https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/eco.bacpac-min.png",
    "Reusable Water Bottle": "https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/water.bottle-min.png",
    "Organic T-Shirt": "https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/organic.tshirt-min.png",
    "Eco Sunglasses": "https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/trannos.west.png"
}

# Update interval in seconds
UPDATE_INTERVAL = 5

def get_cycle(current_dt):
    """
    Defines the active pricing cycle.
    The cycle starts at 05:00 (Europe/Athens) and lasts for 22 hours.
    If the current time is before 05:00, the cycle started yesterday at 05:00.
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
    Rounds the time elapsed since the cycle start to the nearest UPDATE_INTERVAL.
    This creates a common calculation time for all users.
    """
    cycle_start, _ = get_cycle(current_dt)
    delta = (current_dt - cycle_start).total_seconds()
    floor_delta = int(delta // UPDATE_INTERVAL) * UPDATE_INTERVAL
    scheduled_time = cycle_start + datetime.timedelta(seconds=floor_delta)
    return scheduled_time

@st.cache_data(ttl=UPDATE_INTERVAL)
def get_global_scheduled_time():
    """
    Returns the global common calculation time (rounded to the nearest UPDATE_INTERVAL)
    so that all users see the same value.
    """
    tz = pytz.timezone("Europe/Athens")
    now = datetime.datetime.now(tz)
    return get_current_scheduled_time(now)

def calculate_price(product, scheduled_time):
    """
    Calculates the price using linear interpolation based on the common time:
    
    $$ f(t) = \text{start\_price} + (\text{end\_price} - \text{start\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}} $$
    
    Uses the common calculation time.
    """
    cycle_start, cycle_end = get_cycle(scheduled_time)
    total_duration = (cycle_end - cycle_start).total_seconds()
    elapsed = (scheduled_time - cycle_start).total_seconds()
    fraction = elapsed / total_duration
    price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
    return price

# --- Auto-refresh setup ---
# This auto-refreshes the page every UPDATE_INTERVAL seconds.
st.experimental_autorefresh(interval=UPDATE_INTERVAL * 1000, limit=0, key="autorefresh")

# Determine current page: if query parameter 'page' is set to 'Cart', use that; otherwise use the sidebar.
query_params = st.query_params
if "page" in query_params and query_params["page"][0] == "Cart":
    current_page = "Cart"
else:
    current_page = st.sidebar.selectbox("Select Page", options=["Demo", "Console"])

# Function to render the floating cart icon.
def render_cart_icon():
    cart_count = len(st.session_state['cart_items'])
    cart_icon_html = f"""
    <div class="cart-icon">
      <a href="/?page=Cart">
        <div class="icon">
          🛒
          <span class="badge">{cart_count}</span>
        </div>
      </a>
    </div>
    """
    st.markdown(cart_icon_html, unsafe_allow_html=True)

# --- Page Rendering ---

if current_page == "Cart":
    st.title("Your Shopping Cart")
    st.markdown("<hr>", unsafe_allow_html=True)
    
    if st.session_state['cart_items']:
        st.subheader("Items in your cart:")
        for i, item in enumerate(st.session_state['cart_items'], start=1):
            st.markdown(f"**{i}. {item}**")
    else:
        st.write("Your cart is empty!")
    
    if st.button("Continue Shopping"):
        # Reset the URL query parameter to return to Demo page.
        st.experimental_set_query_params(page="Demo")
        st.rerun()
    
    # Also show the floating cart icon (optional on Cart page)
    render_cart_icon()

elif current_page == "Demo":
    st.title("Welcome to Eco Store")
    tz = pytz.timezone("Europe/Athens")
    now = datetime.datetime.now(tz)
    scheduled_time = get_global_scheduled_time()
    
    st.markdown(
        f"""
        <div class="time-info">
            <strong>Current Greek Time:</strong> {now.strftime('%H:%M:%S')}<br>
            <strong>Sale Price Calculation Time:</strong> {scheduled_time.strftime('%H:%M:%S')}
        </div>
        """, unsafe_allow_html=True
    )
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.header("Featured Products")
    # Display products in 2 columns
    cols = st.columns(2)
    for idx, product in enumerate(products):
        with cols[idx % 2]:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            
            # Display product image
            image_url = image_links.get(product["name"], "https://via.placeholder.com/300x200.png")
            st.image(image_url, use_container_width=True)
            
            st.markdown(f"<h3>{product['name']}</h3>", unsafe_allow_html=True)
            price = calculate_price(product, scheduled_time)
            st.markdown(f"<h4>Sale Price: €{price:.4f}</h4>", unsafe_allow_html=True)
            st.write("High-quality, sustainable, and ethically produced.")
            
            # Unique key for each Buy Now button.
            button_key = f"buy_{product['name']}_{idx}_{scheduled_time.strftime('%H%M%S')}"
            if st.button("Buy Now", key=button_key):
                st.success(f"Thank you for purchasing the {product['name']}!")
                st.session_state.cart_items.append(product['name'])
                # Special audio for Eco Sunglasses.
                if product["name"] == "Eco Sunglasses":
                    mp3_url = "https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/TRANNOS%20Feat%20ATC%20Taff%20-%20MAURO%20GYALI%20(Official%20Music%20Video)%20-%20Trapsion%20Entertainment%20(youtube)%20(mp3cut.net).mp3"
                    st.markdown(f"""
                    <audio autoplay>
                      <source src="{mp3_url}" type="audio/mpeg">
                      Your browser does not support the audio element.
                    </audio>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Render the floating cart icon in Demo view.
    render_cart_icon()

elif current_page == "Console":
    st.title("Console: Detailed Analytics & Full Price History")
    tz = pytz.timezone("Europe/Athens")
    now = datetime.datetime.now(tz)
    cycle_start, cycle_end = get_cycle(now)
    total_duration = (cycle_end - cycle_start).total_seconds()
    scheduled_time = get_global_scheduled_time()
    elapsed_time = (scheduled_time - cycle_start).total_seconds()
    
    st.latex(
        r"f(t) = \text{start\_price} + (\text{end\_price} - \text{start\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}}"
    )
    details = f"""
**Cycle Details:**

- **Cycle Start (tₛ):** {cycle_start.strftime("%H:%M:%S")}
- **Cycle End (tₑ):** {cycle_end.strftime("%H:%M:%S")}
- **Scheduled Calculation Time (t):** {scheduled_time.strftime("%H:%M:%S")}
- **Elapsed Time:** {elapsed_time:.8f} seconds
- **Total Duration:** {total_duration:.8f} seconds
    """
    st.markdown(details)
    
    # Create a table with price history (step = UPDATE_INTERVAL)
    schedule = []
    current_time = cycle_start
    while current_time <= scheduled_time:
        row = {"Time": current_time.strftime("%H:%M:%S")}
        for product in products:
            delta = (current_time - cycle_start).total_seconds()
            fraction = delta / total_duration
            price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
            row[product["name"]] = f"{price:.4f} €"
        schedule.append(row)
        current_time += datetime.timedelta(seconds=UPDATE_INTERVAL)
    
    df = pd.DataFrame(schedule)
    if not df.empty:
        if len(df) > 100:
            st.markdown("### First 100 Entries")
            st.dataframe(df.head(100), use_container_width=True)
            st.markdown("### Last 100 Entries")
            st.dataframe(df.tail(100), use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Full Price History",
        data=csv,
        file_name="price_history.csv",
        mime="text/csv",
        key=f"download_{int(time.time())}"
    )
    
    # Render the floating cart icon in Console view.
    render_cart_icon()
