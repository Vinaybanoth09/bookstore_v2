from auth_utils import login_required
from routes.auth_routes import auth
from flask import Flask, render_template
from db import get_connection
from routes.cart_routes import cart
from routes.order_routes import order
from routes.review_routes import review


app = Flask(__name__)
app.secret_key = "dev-secret-key"


app.register_blueprint(auth)
app.register_blueprint(cart)
app.register_blueprint(order)
app.register_blueprint(review)



@app.route("/")
@login_required
def index():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT p.*,
           IFNULL(AVG(r.rating), 0) AS avg_rating,
           COUNT(r.review_id) AS review_count
    FROM products p
    LEFT JOIN reviews r ON p.product_id = r.product_id
    GROUP BY p.product_id
""")
    products = cursor.fetchall()

   
    cursor.close()
    conn.close()
    return render_template("index.html", products=products)

if __name__ == "__main__":
    app.run()
