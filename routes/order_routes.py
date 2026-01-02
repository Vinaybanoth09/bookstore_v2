from flask import Blueprint, session, redirect, url_for, render_template, request
from auth_utils import login_required
from db import get_connection

order = Blueprint('order', __name__)

@order.route('/checkout')
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart.view_cart'))
    return render_template("checkout.html")

@order.route('/place-order', methods=['POST'])
@login_required
def place_order():
    address = request.form['address']
    payment_method = request.form['payment_method']
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('index'))

    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Create order
        cursor.execute(
    "INSERT INTO orders (user_id, status, address) VALUES (%s, 'PLACED', %s)",
    (user_id, address)
)

        order_id = cursor.lastrowid

        payment_status = 'SUCCESS' if payment_method == 'COD' else 'PENDING'

        cursor.execute(
    "INSERT INTO payments (order_id, method, status) VALUES (%s, %s, %s)",
    (order_id, payment_method, payment_status)
)


        # Insert order items
        for product_id, qty in cart.items():
            cursor.execute(
                "SELECT price, stock FROM products WHERE product_id=%s",
                (product_id,)
            )
            product = cursor.fetchone()

            if product['stock'] < qty:
                raise Exception("Insufficient stock")

            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price_at_time) "
                "VALUES (%s, %s, %s, %s)",
                (order_id, product_id, qty, product['price'])
            )

            # Reduce stock
            cursor.execute(
                "UPDATE products SET stock = stock - %s WHERE product_id = %s",
                (qty, product_id)
            )

        conn.commit()
        session.pop('cart', None)
        return render_template("order_confirmation.html", order_id=order_id)

    except Exception as e:
        conn.rollback()
        return str(e)

    finally:
        cursor.close()
        conn.close()


@order.route('/orders')
@login_required
def order_history():
    user_id = session['user_id']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    orders = cursor.fetchall()

    for order in orders:
        cursor.execute("""
            SELECT p.product_id, p.title
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s
        """, (order['order_id'],))
        order['order_items'] = cursor.fetchall()

        cursor.execute("""
            SELECT SUM(quantity * price_at_time) AS total
            FROM order_items
            WHERE order_id = %s
        """, (order['order_id'],))
        order['total'] = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template("orders.html", orders=orders)
