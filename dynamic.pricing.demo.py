#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  4 23:51:31 2025

@author: thodoreskourtales
"""

import streamlit as st
import datetime
import random
import pandas as pd
import pytz

# --- Global product data ---
# This function is executed only once per server session.
@st.cache_resource
def get_products():
    # Define two products with fixed starting prices.
    # Their ending prices are randomly generated in the range: 0.30*start < end < 0.70*start.
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

# --- Helper function to calculate current price ---
def calculate_price(product, current_dt):
    """
    Computes the current price of a product based on current time.
    The degradation is linear from 7:00 (start_price) to midnight (end_price).
    If current time is before 7:00, returns start_price;
    if after midnight, returns end_price.
    """
    # Greek time zone
    tz = pytz.timezone("Europe/Athens")
    # Define start and end times (today's date)
    today = current_dt.astimezone(tz).date()
    start_time = tz.localize(datetime.datetime.combine(today, datetime.time(7, 0)))
    end_time = tz.localize(datetime.datetime.combine(today, datetime.time(23, 59, 59)))
    # Before start, return starting price; after end, return ending price.
    if current_dt < start_time:
        return product["start_price"]
    if current_dt > end_time:
        return product["end_price"]
    # Calculate fraction of time elapsed between start and end.
    total_duration = (end_time - start_time).total_seconds()
    elapsed = (current_dt - start_time).total_seconds()
    fraction = elapsed / total_duration
    # Linear interpolation between start and end.
    current_price = product["start_price"] + (product["end_price"] - product["start_price"]) * fraction
    return current_price

# --- Sidebar for navigation ---
page = st.sidebar.selectbox("Select Page", options=["Demo", "Console"])

# Get current time in Greek time zone
tz = pytz.timezone("Europe/Athens")
now = datetime.datetime.now(tz)

if page == "Demo":
    st.title("Product Demo Page")
    st.write("Current Greek Time:", now.strftime("%H:%M:%S"))
    st.write("Prices degrade linearly from 7:00 to midnight for all users.")
    st.markdown("---")
    # Display each product’s current price based on the current time.
    for product in products:
        current_price = calculate_price(product, now)
        st.subheader(product["name"])
        st.write(f"Current Price: {current_price:.2f} €")
    st.info("Refresh the page to see updated prices based on the current time.")

elif page == "Console":
    st.title("Console: Price Degradation Details")
    st.write("This page displays detailed product data and a schedule of price degradation.")
    st.markdown("### Product Details")
    for product in products:
        st.write(f"**{product['name']}**: Start Price = {product['start_price']:.2f} €, "
                 f"End Price = {product['end_price']:.2f} €")
    
    st.markdown("---")
    st.markdown("### Price Schedule from 7:00 to Midnight")
    # Generate schedule table: for a range of times from 7:00 to midnight.
    today = now.date()
    tz = pytz.timezone("Europe/Athens")
    start_dt = tz.localize(datetime.datetime.combine(today, datetime.time(7, 0)))
    end_dt = tz.localize(datetime.datetime.combine(today, datetime.time(23, 59, 59)))
    
    # Choose a resolution for the schedule. Here we use 15-minute intervals.
    schedule = []
    current_dt = start_dt
    while current_dt <= end_dt:
        row = {"Time": current_dt.strftime("%H:%M")}
        for product in products:
            price = calculate_price(product, current_dt)
            row[product["name"]] = f"{price:.2f} €"
        schedule.append(row)
        current_dt += datetime.timedelta(minutes=15)
    
    df = pd.DataFrame(schedule)
    st.dataframe(df)
