from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from flask import send_file
from flask_login import login_required, current_user
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

orders_bp = Blueprint("orders", __name__)

database = None


def init_orders(db):
    global database
    database = db


@orders_bp.route("/orders")
@login_required
def orders():
    orders = database.get_orders_by_user(current_user.id)

    formatted = []
    for oid, total, status, created_at, shipping_address in orders:
        formatted.append({
            "id": oid,
            "total": total,
            "status": status,
            "created_at": created_at,
            "shipping_address" : shipping_address
        })

    return render_template("orders.html", orders=formatted)

@orders_bp.route("/orders/buy/<pid>", methods=["POST"])
@login_required
def buy_now(pid):
    print(current_user.id)
    product = database.get_product(pid)

    if not product:
        return "Product not found", 404

    _, _, name, desc, price, _ = product

    # create order
    order_id = database.create_order(current_user.id, float(price))

    return redirect(url_for("orders.orders"))

@orders_bp.route("/orders/seek/<int:order_id>")
@login_required
def order_details(order_id):
    order = database.get_order(order_id)

    if not order:
        return "Order not found", 404

    # security: ensure user owns order
    if order[1] != current_user.id:
        return "Unauthorized", 403

    items = database.get_order_items(order_id)

    formatted_items = []
    for product_id, qty, price in items:
        product = database.get_product(product_id)

        if product:
            _, _, name, desc, _, image = product

            formatted_items.append({
                "name": name,
                "qty": qty,
                "price": float(price),
                "subtotal": float(price) * qty
            })

    formatted_order = {
        "id": order[0],
        "total": order[2],
        "status": order[3],
        "created_at": order[4]
    }

    return render_template(
        "order_details.html",
        order=formatted_order,
        items=formatted_items
    )

@orders_bp.route("/orders/seek/<int:order_id>/pdf")
@login_required
def download_receipt(order_id):
    order = database.get_order(order_id)

    if not order:
        return "Order not found", 404

    if order[1] != current_user.id:
        return "Unauthorized", 403

    items = database.get_order_items(order_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    elements = []

    # HEADER
    elements.append(Paragraph("Macrocenter Receipt", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Order ID: {order[0]}", styles["Normal"]))
    elements.append(Paragraph(f"Status: {order[3]}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {order[4]}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # TABLE DATA
    data = [["Product ID", "Quantity", "Price", "Subtotal"]]

    total = 0

    for product_id, qty, price in items:
        subtotal = qty * float(price)
        total += subtotal

        data.append([
            str(product_id),
            str(qty),
            f"${price:.2f}",
            f"${subtotal:.2f}"
        ])

    data.append(["", "", "TOTAL", f"${total:.2f}"])

    table = Table(data)

    table.setStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ])

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"receipt_{order_id}.pdf",
        mimetype="application/pdf"
    )


@orders_bp.route("/orders/cancel/<int:order_id>", methods=["POST"])
@login_required
def cancel_order(order_id):
     database.cancel_order(order_id, current_user.id)
     return redirect(url_for("orders.orders"))




