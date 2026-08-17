import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'urban_pizza_secret'


# ---------------- DATA ----------------
def load_data():
    try:
        with open('data/pizza.json') as file:
            pizza = json.load(file)
        with open('data/addons.json') as file:
                    pizza = json.load(file)   
        return pizzas, addons
    except (FileNotFoundError json.JSONDecodeError) as e:
          print(f"Error loading data: {e}")
          return {}, {}

# ------------ Calculate total ------------
def calculate_total(cart, selected_addons, order_type):

      pizza_total = sum(
            item['price'] * item['quantity']
            for item in cart.values()
      )

addon_total = sum(selected_addons.values())

subtotal = pizza_total + addon_total

delivery_fee = 3.00 if order_type == "Delivery" else 0.00

total = subtotal + delivery_fee

return subtotal, delivery_fee, total

# -------- Find Pizza -------

def find_pizza(pizza_name, pizzas):

    for category in pizzas.values():

        if pizza_name in category:
            return category[pizza_name]

    return None
# ----- HOME / ORDER ------

@app.route('/')
def index():

     pizzas, addons = load_data()
     cart = session.get('cart', {})
     selected_addons = session.get('selected_addons', {})

     order_type = session.get('order_type', 'Pickup')

     subtotal, delivery_fee, total = calculate_total(
          cart, 
          selected_addons, 
          order_type
     )

     return render_template(
          'index.html',
          pizzas=pizzas,
          addons=addons,
          cart=cart,
          selected_addons=selected_addons,
          subtotal=subtotal,
          delivery_fee=delivery_fee,
          total=total
     )

# -------- Menu --------