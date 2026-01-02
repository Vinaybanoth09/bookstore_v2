from flask import Blueprint, session, redirect, url_for, request, render_template
from auth_utils import login_required
from db import get_connection

cart = Blueprint('cart', __name__)

@cart.route('/add-to-cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart

    return redirect(url_for('index'))

@cart.route('/remove-from-cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('cart.view_cart'))



@cart.route('/cart')
@login_required
def view_cart():
    cart_data = session.get('cart', {})
    if not cart_data:
        return "Your cart is empty"

    product_ids = list(cart_data.keys())

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    placeholders = ','.join(['%s'] * len(product_ids))
    query = f"SELECT * FROM products WHERE product_id IN ({placeholders})"
    cursor.execute(query, product_ids)

    products = cursor.fetchall()
    cursor.close()
    conn.close()

    total = 0
    for product in products:
        qty = cart_data[str(product['product_id'])]
        total += product['price'] * qty
        product['quantity'] = qty
        product['subtotal'] = product['price'] * qty

    return render_template("cart.html", products=products, total=total)
