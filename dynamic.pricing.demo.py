#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  4 23:51:31 2025

@author: thodoreskourtales
"""

import streamlit as st
import datetime

# Ορισμός συναρτήσεων για δυναμική τιμολόγηση
def price_product_A():
    now = datetime.datetime.now()
    return 100 if now.hour < 12 else 150

def price_product_B():
    now = datetime.datetime.now()
    return 200 + now.minute * 0.5

# Λίστα προϊόντων με τα ονόματα και τις συναρτήσεις τιμολόγησης
products = [
    {"name": "Προϊόν Α", "price_func": price_product_A},
    {"name": "Προϊόν Β", "price_func": price_product_B}
]

# Τίτλος της εφαρμογής
st.title("Δυναμική Τιμολόγηση Προϊόντων")

# Κουμπί ανανέωσης που επαναφορτώνει την σελίδα για ενημέρωση των τιμών
if st.button('Ανανέωση Τιμών'):
    st.experimental_rerun()

# Εμφάνιση των προϊόντων με τις τρέχουσες τιμές
for product in products:
    price = product['price_func']()
    st.write(f"{product['name']}: {price} €")