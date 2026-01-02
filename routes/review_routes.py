from flask import Blueprint, session, redirect, url_for, render_template, request
from auth_utils import login_required
from db import get_connection

review = Blueprint('review', __name__)

@review.route('/review/<int:product_id>', methods=['GET', 'POST'])
@login_required
def add_review(product_id):
    user_id = session['user_id']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if user bought this product
    cursor.execute("""
        SELECT 1 FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.user_id = %s AND oi.product_id = %s
    """, (user_id, product_id))

    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return "You can only review products you purchased."

    if request.method == 'POST':
        rating = request.form['rating']
        comment = request.form['comment']

        cursor.execute(
            "INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (%s, %s, %s, %s)",
            (user_id, product_id, rating, comment)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('order.order_history'))

    cursor.close()
    conn.close()
    return render_template("review.html")
