import json
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'urban_pizza_secret'

# ---------------- DATA ----------------
def load_data():
    try:
        with open('data/pizzas.json') as file:
            pizzas = json.load(file)

        with open('data/addons.json') as file:
            addons = json.load(file)

        return pizzas, addons

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return {}, {}
    
# ---------------- CALCULATE TOTAL ----------------
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

# ---------------- FIND PIZZA ----------------

def find_pizza(pizza_name, pizzas):

    for category in pizzas.values():
        if pizza_name in category:
            return category[pizza_name]
        
    return None

# ---------------- HOME / ORDER ----------------

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

# ---------------- MENU ----------------

@app.route('/menu')
def menu():

    pizzas, addons = load_data()

    return render_template(
        'menu.html',
        pizzas=pizzas,
        addons=addons
    )

# ---------------- ADD PIZZA ----------------

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():

    pizza_name = request.form.get('pizza')
    size = request.form.get('size', 'Medium')

    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        quantity = 1

    pizzas, _ = load_data()

    pizza = find_pizza(pizza_name, pizzas)

    if pizza:
        cart = session.get('cart', {})
        current_quantity = sum(
            item['quantity']
            for item in cart.values()
        )

        # Maximum amount of pizzas allowed in an order are 5.
        if current_quantity + quantity > 5:

            flash("You can only order a maximum of 5 pizzas.")

            return redirect(url_for('index'))
        
        price = pizza['prices'][size]
        item_name = f"{pizza_name} ({size})"

        if item_name in cart:
            cart[item_name]['quantity'] += quantity

        else:

            cart[item_name] = {
                'price': price,
                'quantity': quantity
            }

        session['cart'] = cart
        session.modified = True
        flash(f"{quantity} x {item_name} added to your cart.")

    return redirect(url_for('index'))

#----Select Addons----
@app.route('/select_addon', methods=['POST'])
def select_addon():
    selected_addons = {}
    _, addons = load_data()
    selected = request.form.getlist('addons')

    for addon in selected:
        if addon in addons:
            selected_addons[addon] = float(
                addons[addon]['price']
            )
    session['selected_addons'] = selected_addons
    session.modified = True
    flash("Add-ons updated.")

    return redirect(url_for('index'))

#----Remove from Cart-----

