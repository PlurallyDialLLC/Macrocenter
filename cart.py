from flask import Blueprint, session, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

cart_bp = Blueprint("cart", __name__)

database = None


def init_cart(db):
    global database
    database = db


@cart_bp.route("/add/<int:pid>", methods=["POST"])
@login_required
def add_to_cart(pid):
    cart = session.get("cart", {})

    pid = str(pid)

    if pid in cart:
        cart[pid] += 1
    else:
        cart[pid] = 1

    session["cart"] = cart
    flash("Added to cart!", "success")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/")
@login_required
def view_cart():
    cart = session.get("cart", {})

    items = []
    total = 0

    for pid, qty in cart.items():
        product = database.get_product(int(pid))

        if product:
            _, _, name, desc, price, image = product

            subtotal = float(price) * qty
            total += subtotal

            items.append({
                "pid": pid,
                "name": name,
                "price": float(price),
                "qty": qty,
                "subtotal": subtotal,
                "image": image
            })

    return render_template("cart.html", items=items, total=total)


@cart_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart = session.get("cart", {})

    if not cart:
        return redirect(url_for("cart.view_cart"))

    # ✅ NEW: get shipping address
    shipping_address = request.form.get("shipping_address")

    if not shipping_address:
        flash("Shipping address is required", "error")
        return redirect(url_for("cart.view_cart"))

    total = 0
    items_data = []

    # 1. Calculate total + prepare items
    for pid, qty in cart.items():
        product = database.get_product(int(pid))

        if product:
            _, _, name, desc, price, image = product
            price = float(price)

            total += price * qty

            items_data.append({
                "product_id": int(pid),
                "quantity": qty,
                "price": price
            })

    # 2. Create order (UPDATED)
    order_id = database.create_order(
        current_user.id,
        total,
        shipping_address   # ✅ ADD THIS
    )

    # 3. Insert order items
    for item in items_data:
        database.add_order_item(
            order_id,
            item["product_id"],
            item["quantity"],
            item["price"]
        )

    # 4. Clear cart
    session["cart"] = {}

    flash("Order Placed. Cheers!", "success")

    return redirect(url_for("orders.orders"))
