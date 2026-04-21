from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user

admin_bp = Blueprint("admin", __name__)

database = None


def init_admin(db):
    global database
    database = db



def admin_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        # user tuple: (id, username, email, password)
        if not getattr(current_user, "id", None):
            return abort(403)

        user = database.get_user_by_id(current_user.id)

        if not user or not user[4]:  # adjust if column order differs
            return abort(403)

        return func(*args, **kwargs)

    return wrapper


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    products = database.get_products()
    return render_template("admin/dashboard.html", products=products)


@admin_bp.route("/product/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        desc = request.form["desc"]
        price = request.form["price"]
        ptype = request.form["type"]

        cursor = database.connection.cursor()
        cursor.execute("""
            INSERT INTO products (product_type, name, description, price)
            VALUES (%s, %s, %s, %s)
        """, (ptype, name, desc, price))

        database.connection.commit()

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_product.html")


@admin_bp.route("/product/delete/<int:pid>")
@login_required
@admin_required
def delete_product(pid):
    cursor = database.connection.cursor()
    cursor.execute("DELETE FROM products WHERE pid=%s", (pid,))
    database.connection.commit()

    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/orders")
@login_required
@admin_required
def view_orders():
    cursor = database.connection.cursor()
    cursor.execute("SELECT id, user_id, total, status, created_at, shipping_address FROM orders")
    orders = cursor.fetchall()

    return render_template("admin/orders.html", orders=orders)

@admin_bp.route("/orders/update/<int:order_id>", methods=["POST"])
@login_required
def update_order(order_id):
    status = request.form.get("status")

    database.update_order_status(order_id, status)

    return redirect(url_for("admin.view_orders"))

@admin_bp.route("/product/edit/<int:pid>", methods=["GET"])
def edit_product(pid):
    product = database.get_product(pid)

    if not product:
        return "Product not found", 404

    pid, ptype, name, desc, price, image_keyword = product

    return render_template("admin/edit_product.html", product={
        "pid": pid,
        "ptype": ptype,
        "name": name,
        "desc": desc,
        "price": price,
        "image_keyword": image_keyword
    })


@admin_bp.route("/product/edit/<int:pid>", methods=["POST"])
def update_product(pid):
    name = request.form.get("name")
    desc = request.form.get("desc")
    price = request.form.get("price")
    ptype = request.form.get("type")
    image = request.form.get("image_keyword")

    database.update_product(
        pid,
        name,
        desc,
        price,
        ptype,
        image
    )

    return redirect(url_for("admin.dashboard"))
