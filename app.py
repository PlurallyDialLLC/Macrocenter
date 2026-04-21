from flask import Flask, redirect, url_for
import os
from dotenv import load_dotenv
from flask_login import LoginManager, current_user, login_required

from cart import init_cart, cart_bp
from orders import orders_bp, init_orders

from admin import admin_bp, init_admin



from db import Database, Product, ProductType
from auth import auth, init_auth

# Load env FIRST
load_dotenv()

DB_ENDPOINT_PREFIX = "db"

# Create app FIRST
app = Flask(__name__)
app.secret_key = "your-secret-key"  # required for login sessions

# Setup database
database: Database = Database(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT"),
    use_pure=True
)

# Setup login manager AFTER app exists
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize auth system
init_auth(app, database, login_manager)
init_admin(database)
init_orders(database)
init_cart(database)
# Register blueprint
app.register_blueprint(auth)
app.register_blueprint(admin_bp, url_prefix="/admin")

app.register_blueprint(orders_bp)
app.register_blueprint(cart_bp, url_prefix="/cart")


@app.route("/")
def index():
    return redirect(url_for("get_all_products"))




@app.route(f"/{DB_ENDPOINT_PREFIX}/products/<filter_type>", methods=["GET"])
def get_products(filter_type: str = ""):
    filter_type: str = filter_type.lower()
    products = database.get_products()
    output_string = f"<p>Product Entries {filter_type}</p><br/>"

    for index, (pid, ptype, name, desc, price) in enumerate(products):
        if (filter_type != "") and (ProductType(ptype).name.lower() != filter_type):
            continue
        output_string += f"<p>Name: {name}.....Description: {desc}......Price: ${price:,.2f}......Type: {ProductType(ptype)}...."
    return output_string


from flask import render_template
@app.route(f"/products/", methods=["GET"])

def get_all_products():
    products = database.get_products()

    formatted_products = []

    for pid, ptype, name, desc, price, image_keyword in products:
        formatted_products.append({
            "pid": pid,
            "type": ProductType(ptype),
            "name": name,
            "desc": desc,
            "price": price,
            "image_keyword": image_keyword
        })

    return render_template("products.html", products=formatted_products)

@app.route("/product/<int:pid>")
def product_page(pid):
    product = database.get_product(pid)  # make sure this returns ONE product

    if not product:
        return "Product not found", 404

    pid, ptype, name, desc, price, image_keyword = product

    formatted_product = {
        "pid": pid,
        "type": ProductType(ptype),
        "name": name,
        "desc": desc,
        "price": price,
        "image_keyword": image_keyword
    }

    return render_template("product.html", product=formatted_product)


from flask import request, jsonify

@app.route("/search")
def search_products():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    products = database.search_products(query)

    formatted = []
    for pid, ptype, name, desc, price, image_keyword in products:
        formatted.append({
            "pid": pid,
            "name": name,
            "desc": desc,
            "price": float(price),
            "image_keyword": image_keyword
        })

    return jsonify(formatted)

@app.route("/products")
def products_by_type():
    products = database.get_products()

    formatted = []
    ptype = request.args.get("type")
    for pid, product_type, name, desc, price, image_keyword in products:
        if ProductType(product_type).name.lower() == ptype.lower():
            formatted.append({
                "pid": pid,
                "ptype": ProductType(product_type).name,
                "name": name,
                "desc": desc,
                "price": price,
                "image_keyword": image_keyword
            })

    return render_template("products.html", products=formatted)
