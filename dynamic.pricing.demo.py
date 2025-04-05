#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  5 03:40:51 2025

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

# Αρχικοποίηση session_state για το cart, αν δεν υπάρχει ήδη.
if "cart" not in st.session_state:
    st.session_state.cart = []  # λίστα προϊόντων στο καλάθι

# Inject custom CSS for a modern, eco-friendly look and for the floating cart icon.
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
        padding: 0.5rem; /* μειωμένο padding */
        margin: 0rem;    /* μειωμένο margin */
        border-radius: 10px;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.15);
        text-align: center;
    }
    .product-card h3 {
        color: #33691E;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin-top: 0;
        margin-bottom: 0.2rem;
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
    /* Floating cart icon styling */
    .floating-cart {
        position: fixed;
        top: 80px;
        right: 20px;
        background-color: #66BB6A;
        color: #ffffff;
        padding: 10px;
        border-radius: 50%;
        font-size: 24px;
        text-align: center;
        cursor: pointer;
        box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.3);
        z-index: 9999;
    }
    .cart-counter {
        position: absolute;
        top: -5px;
        right: -5px;
        background-color: #ff1744;
        color: #ffffff;
        border-radius: 50%;
        padding: 2px 6px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Update interval (seconds)
UPDATE_INTERVAL = 5

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

# Λίστα με URLs εικόνων από GitHub (χρησιμοποιώντας raw links)
image_links = {
    "Eco Backpack": "https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/eco.bacpac-min.png",
    "Reusable Water Bottle": "https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/water.bottle-min.png",
    "Organic T-Shirt": "https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/organic.tshirt-min.png",
    "Eco Sunglasses": "https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/trannos.west.png"
}

def get_cycle(current_dt):
    """
    Ορίζει τον ενεργό κύκλο τιμολόγησης.
    Ξεκινάει στις 05:00 (Europe/Athens) και διαρκεί 22 ώρες.
    Αν η τρέχουσα ώρα είναι πριν τις 05:00, ο κύκλος ξεκινάει χθες στις 05:00.
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
    Στρογγυλοποιεί το χρόνο από την έναρξη του κύκλου στο πλησιέστερο UPDATE_INTERVAL.
    Δηλαδή, ορίζει έναν κοινό χρόνο υπολογισμού για όλους τους χρήστες.
    """
    cycle_start, _ = get_cycle(current_dt)
    delta = (current_dt - cycle_start).total_seconds()
    floor_delta = int(delta // UPDATE_INTERVAL) * UPDATE_INTERVAL
    scheduled_time = cycle_start + datetime.timedelta(seconds=floor_delta)
    return scheduled_time

@st.cache_data(ttl=UPDATE_INTERVAL)
def get_global_scheduled_time():
    """
    Επιστρέφει τον παγκόσμιο κοινό χρόνο υπολογισμού (στρογγυλοποιημένο στο UPDATE_INTERVAL)
    ώστε όλοι οι χρήστες να βλέπουν την ίδια τιμή.
    """
    tz = pytz.timezone("Europe/Athens")
    now = datetime.datetime.now(tz)
    return get_current_scheduled_time(now)

def calculate_price(product, scheduled_time):
    """
    Υπολογίζει την τιμή χρησιμοποιώντας γραμμική παρεμβολή με βάση το κοινό χρόνο:
    
    $$ f(t) = \text{start\_price} + (\text{end\_price} - \text{start\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}} $$
    
    Χρησιμοποιεί τον κοινό χρόνο υπολογισμού.
    """
    cycle_start, cycle_end = get_cycle(scheduled_time)
    total_duration = (cycle_end - cycle_start).total_seconds()
    elapsed = (scheduled_time - cycle_start).total_seconds()
    fraction = elapsed / total_duration
    price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
    return price

# ---------------------
# Sidebar Navigation (Demo, Console, Cart)
# ---------------------
page = st.sidebar.selectbox("Select Page", options=["Demo", "Console", "Cart"])
tz = pytz.timezone("Europe/Athens")
now = datetime.datetime.now(tz)
scheduled_time = get_global_scheduled_time()

# ---------------------
# Floating Cart Icon (μικρό εικονίδιο στο κάτω δεξί)
cart_count = len(st.session_state.cart)
cart_icon_html = f"""
<div class="floating-cart" onclick="window.location.href='/?page=Cart'">
    🛒
    <div class="cart-counter">{cart_count}</div>
</div>
"""
st.markdown(cart_icon_html, unsafe_allow_html=True)

# ---------------------
# Demo Page: Real Store
# ---------------------
if page == "Demo":
    st.title("Welcome to Eco Store")
    
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
    
    cols = st.columns(2)
    for idx, product in enumerate(products):
        with cols[idx % 2]:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            
            # Εμφάνιση εικόνας μέσω HTML για να μην υπάρχουν white headers.
            image_url = image_links.get(product["name"], "https://via.placeholder.com/300x200.png")
            st.markdown(f'<img src="{image_url}" class="product-img">', unsafe_allow_html=True)
            
            st.markdown(f"<h3>{product['name']}</h3>", unsafe_allow_html=True)
            price = calculate_price(product, scheduled_time)
            st.markdown(f"<h4>Sale Price: €{price:.4f}</h4>", unsafe_allow_html=True)
            st.write("High-quality, sustainable, and ethically produced.")
            
            button_key = f"buy_{product['name']}_{idx}_{scheduled_time.strftime('%H%M%S')}"
            if st.button("Buy Now", key=button_key):
                st.success(f"Thank you for purchasing the {product['name']}!")
                # Προσθήκη προϊόντος στο cart (append το προϊόν στο session_state.cart)
                st.session_state.cart.append(product)
                # Αν είναι τα Eco Sunglasses, αναπαραγέι ο ήχος MP3
                if product["name"] == "Eco Sunglasses":
                    mp3_url = ("https://raw.githubusercontent.com/TheodorosKourtalis/georgia.demo/main/"
                               "TRANNOS%20Feat%20ATC%20Taff%20-%20MAURO%20GYALI%20(Official%20Music%20Video)%20-"
                               "Trapsion%20Entertainment%20(youtube)%20(mp3cut.net).mp3")
                    st.markdown(
                        f"""
                        <audio autoplay>
                          <source src="{mp3_url}" type="audio/mpeg">
                          Your browser does not support the audio element.
                        </audio>
                        """, unsafe_allow_html=True
                    )
            st.markdown("</div>", unsafe_allow_html=True)

# ---------------------
# Console Page: Detailed Analytics & Full Price History
# ---------------------
elif page == "Console":
    st.title("Console: Detailed Analytics & Full Price History")
    
    st.latex(
        r"f(t) = \text{start\_price} + (\text{end\_price} - \text{start\_price}) \times \frac{t - t_{\text{start}}}{t_{\text{end}} - t_{\text{start}}}"
    )
    
    cycle_start, cycle_end = get_cycle(now)
    total_duration = (cycle_end - cycle_start).total_seconds()
    elapsed_time = (scheduled_time - cycle_start).total_seconds()
    
    st.markdown(
        f"""
        **Cycle Details:**
        
        - **Cycle Start (tₛ):** {cycle_start.strftime("%H:%M:%S")}
        - **Cycle End (tₑ):** {cycle_end.strftime("%H:%M:%S")}
        - **Scheduled Calculation Time (t):** {scheduled_time.strftime("%H:%M:%S")}
        - **Elapsed Time:** {elapsed_time:.8f} seconds
        - **Total Duration:** {total_duration:.8f} seconds
        """
    )
    
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

# ---------------------
# Cart Page: Display the items in the cart nicely
# ---------------------
# ---------------------
# Cart Page: Nice Looking Cart
# ---------------------
elif page == "Cart":
    st.title("Your Shopping Cart")
    if st.session_state.cart:
        st.markdown("### Items in your Cart:")
        # Επαναυπολογισμός της τρέχουσας τιμής για κάθε προϊόν στο καλάθι
        updated_cart = []
        for item in st.session_state.cart:
            updated_item = item.copy()
            updated_item["current_price"] = calculate_price(item, get_global_scheduled_time())
            updated_cart.append(updated_item)
        cart_df = pd.DataFrame(updated_cart)
        st.dataframe(cart_df, use_container_width=True)
        total = sum(item["current_price"] for item in updated_cart)
        st.markdown(f"**Total:** €{total:.2f}")
        st.markdown("Thank you for shopping with us!")
    else:
        st.info("Your cart is empty.")
