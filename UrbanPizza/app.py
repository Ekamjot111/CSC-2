import json
import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'urban_pizza_secret_key'

# ---------- LOAD DATA ----------
def load_data():
    with open('data/pizzas.json') as file:
        pizzas = json.load(file)
    with open('data/addons.json') as file:
        addons = json.load(file)
    return pizzas, addons

# ---------- DATABASE ----------
def initialise_database():
    with sqlite3.connect('pizza_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT,
                customer_name TEXT,
                phone TEXT,
                order_type TEXT,
                address TEXT,
                items TEXT,
                addons TEXT,
                total REAL,
                date TEXT
            )
        ''')
        conn.commit()

# ---------- FIND PIZZA ----------
def find_pizza(pizza_name, pizzas):
    for category in pizzas.values():
        if pizza_name in category:
            return category[pizza_name]
    return None

# ---------- CALCULATE TOTAL ----------
def calculate_total(cart, selected_addons, order_type):
    subtotal = 0
    for item in cart.values():
        subtotal += item['price'] * item['quantity']
    for price in selected_addons.values():
        subtotal += price
    delivery_fee = 3.00 if order_type == 'Delivery' else 0.00
    total = subtotal + delivery_fee
    return subtotal, delivery_fee, total

# ---------- HOME PAGE ----------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- ORDER PAGE ----------
@app.route('/order')
def order():
    pizzas, addons = load_data()
    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})
    subtotal, delivery_fee, total = calculate_total(
        cart,
        selected_addons,
        'Delivery'
    )
    return render_template(
        'order.html',
        pizzas=pizzas,
        addons=addons,
        cart=cart,
        selected_addons=selected_addons,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total
    )

# ---------- MENU PAGE ----------
@app.route('/menu')
def menu():
    pizzas, addons = load_data()
    return render_template(
        'menu.html',
        pizzas=pizzas,
        addons=addons
    )

# ---------- ADD PIZZA TO CART ----------
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    pizza_name = request.form.get('pizza')
    size = request.form.get('size')
    quantity = int(request.form.get('quantity', 1))
    pizzas, addons = load_data()
    pizza = find_pizza(pizza_name, pizzas)
    if pizza is None:
        flash('Pizza could not be found.')
        return redirect(url_for('order'))

    cart = session.get('cart', {})
    # Maximum of 5 pizzas per order
    pizza_count = sum(item['quantity'] for item in cart.values())
    if pizza_count + quantity > 5:
        flash('You can only order a maximum of 5 pizzas.')
        return redirect(url_for('order'))

    price = pizza['prices'][size]
    item_name = pizza_name + ' (' + size + ')'
    if item_name in cart:
        cart[item_name]['quantity'] += quantity
    else:
        cart[item_name] = {
            'price': price,
            'quantity': quantity
        }
    session['cart'] = cart
    session.modified = True
    flash(f"Added {quantity} x {pizza_name} ({size}) to your cart.")
    return redirect(url_for('order'))

# ---------- SELECT ADD-ONS ----------
@app.route('/select_addon', methods=['POST'])
def select_addon():
    selected_addons = {}
    _, addons = load_data()
    selected = request.form.getlist('addons')
    for addon in selected:
        if addon in addons:
            selected_addons[addon] = float(addons[addon]['price'])
    session['selected_addons'] = selected_addons
    session.modified = True
    flash('Add-ons updated.')
    return redirect(url_for('order'))

# ---------- REMOVE FROM CART ----------
@app.route('/remove_from_cart/<item>')
def remove_from_cart(item):
    cart = session.get('cart', {})
    if item in cart:
        del cart[item]
    session['cart'] = cart
    session.modified = True
    flash('Item removed from cart.')
    return redirect(url_for('order'))

# ---------- CHECKOUT ----------
@app.route('/checkout', methods=['POST'])
def checkout():
    customer_name = request.form.get('customer_name', '').strip()
    phone = request.form.get('phone', '').strip()
    order_type = request.form.get('order_type')
    address = request.form.get('address', '').strip()
    cart = session.get('cart', {})
    selected_addons = session.get('selected_addons', {})

    if not cart:
        flash('Your cart is empty.')
        return redirect(url_for('order'))
    if not customer_name:
        flash('Please enter your name.')
        return redirect(url_for('order'))
    
    # Check if the customer name contains numbers or invalid symbols
    if customer_name.isdigit() or not all(char.isalpha() or char.isspace() for char in customer_name):
        flash('Please enter a valid customer name (numbers/symbols are not allowed).')
        return redirect(url_for('order'))

    if not phone:
        flash('Please enter your phone number.')
        return redirect(url_for('order'))
    if order_type == 'Delivery' and not address:
        flash('Please enter a delivery address.')
        return redirect(url_for('order'))

    subtotal, delivery_fee, total = calculate_total(
        cart,
        selected_addons,
        order_type
    )
    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with sqlite3.connect('pizza_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM orders')
        order_count = cursor.fetchone()[0]
        invoice_number = 'ORD-' + str(order_count + 1001)
        cursor.execute('''
            INSERT INTO orders
            (invoice_number, customer_name, phone, order_type,
             address, items, addons, total, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_number,
            customer_name,
            phone,
            order_type,
            address,
            json.dumps(cart),
            json.dumps(selected_addons),
            total,
            date
        ))
        conn.commit()

    order = {
        'invoice_number': invoice_number,
        'customer_name': customer_name,
        'phone': phone,
        'order_type': order_type,
        'address': address,
        'items': cart,
        'addons': selected_addons,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'date': date
    }

    session.pop('cart', None)
    session.pop('selected_addons', None)
    session.modified = True
    return render_template('receipt.html', order=order)

# ---------- CANCEL CURRENT ORDER ----------
@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    session.pop('cart', None)
    session.pop('selected_addons', None)
    session.modified = True
    flash('Order cancelled.')
    return redirect(url_for('order'))

# ---------- ORDER HISTORY ----------
@app.route('/order_history')
def order_history():
    orders = []
    with sqlite3.connect('pizza_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders ORDER BY order_id DESC')
        rows = cursor.fetchall()
        for row in rows:
            orders.append({
                'order_id': row[0],
                'invoice_number': row[1],
                'customer_name': row[2],
                'phone': row[3],
                'order_type': row[4],
                'address': row[5],
                'items': json.loads(row[6]),
                'addons': json.loads(row[7]),
                'total': row[8],
                'date': row[9]
            })
    return render_template('history.html', orders=orders)

# ---------- CANCEL SAVED ORDER ----------
@app.route('/cancel_saved_order/<int:order_id>', methods=['POST'])
def cancel_saved_order(order_id):
    with sqlite3.connect('pizza_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM orders WHERE order_id = ?', (order_id,))
        conn.commit()
    flash('Order cancelled from order history.')
    return redirect(url_for('order_history'))

if __name__ == '__main__':
    initialise_database()
    app.run(debug=True)