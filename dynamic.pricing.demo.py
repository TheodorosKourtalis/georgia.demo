#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  4 23:51:31 2025

@author: thodoreskourtales
"""

import streamlit as st
import datetime
import time
import random

# Title and display current time when the user enters the site
st.title("Dynamic Product Pricing")
current_time = datetime.datetime.now()
st.write("Current time:", current_time.strftime("%H:%M:%S"))

# Define two products with starting prices
products = [
    {"name": "Product A", "start_price": 100},
    {"name": "Product B", "start_price": 200}
]

# For each product, calculate a random ending price in the specified range
for product in products:
    product["end_price"] = random.uniform(0.30 * product["start_price"], 0.70 * product["start_price"])

st.write("Prices will degrade dynamically over 60 seconds (each second = 10 minutes).")

# Create a placeholder for price updates
price_placeholder = st.empty()

# Update the product prices every second for 60 seconds
for second in range(61):  # 0 to 60 seconds
    price_info = ""
    for product in products:
        start_price = product["start_price"]
        end_price = product["end_price"]
        # Calculate current price with linear interpolation
        current_price = start_price + (end_price - start_price) * (second / 60)
        price_info += f"{product['name']}: {current_price:.2f} €\n"
    price_placeholder.text(price_info)
    time.sleep(1)
