from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
import hive_db as db

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

ANALYSES = {
    "category": {"column": "category", "title": "Category Analysis", "label": "category"},
    "region":   {"column": "region", "title": "Region Analysis", "label": "region"},
    "product":  {"column": "product", "title": "Product Analysis", "label": "product"},
    "payment":  {"column": "payment_method", "title": "Payment Analysis", "label": "payment method"},
}


@app.template_filter("money")
def money(v):
    return f"₹{float(v or 0):,.2f}"


@app.errorhandler(Exception)
def hive_error(e):
    if hasattr(e, "code") and isinstance(getattr(e, "code"), int):  # HTTP errors
        return e
    return render_template("error.html", error=str(e), active=""), 500


@app.route("/")
def dashboard():
    return render_template("index.html", s=db.get_summary(), active="dashboard")


@app.route("/sales")
def sales():
    q = request.args.get("q", "").strip()
    rows = db.search_sales(q) if q else db.get_all_sales()
    return render_template("sales.html", rows=rows, q=q, active="sales")


@app.route("/analysis/<kind>")
@app.route("/analysis/<kind>/<path:value>")
def analysis(kind, value=None):
    cfg = ANALYSES.get(kind)
    if not cfg:
        return redirect(url_for("dashboard"))
    groups = db.get_groups(cfg["column"])
    rows = db.get_sales_by(cfg["column"], value) if value else None
    total = sum(r["total_amount"] for r in rows) if rows else 0
    return render_template("analysis.html", kind=kind, cfg=cfg, groups=groups,
                           value=value, rows=rows, total=total, active=kind)


@app.route("/add", methods=["GET", "POST"])
def add_sale():
    form = request.form if request.method == "POST" else {}
    if request.method == "POST":
        try:
            sale = {
                "order_id": int(form["order_id"]),
                "order_date": datetime.strptime(form["order_date"], "%Y-%m-%d").strftime("%Y-%m-%d"),
                "product": form["product"].strip(),
                "category": form["category"].strip(),
                "quantity": int(form["quantity"]),
                "price": float(form["price"]),
                "region": form["region"].strip(),
                "payment_method": form["payment_method"].strip(),
            }
            if sale["quantity"] <= 0 or sale["price"] < 0:
                raise ValueError("Quantity must be above 0 and price cannot be negative.")
            if not all([sale["product"], sale["category"], sale["region"], sale["payment_method"]]):
                raise ValueError("All fields are required.")
            if db.order_exists(sale["order_id"]):
                raise ValueError(f"Order ID {sale['order_id']} already exists in Hive.")
            db.insert_sale(sale)
            if not db.order_exists(sale["order_id"]):  # confirm the row is really in Hive
                raise RuntimeError("Hive finished the insert but the row is not visible in ecommerce.sales. "
                                   "Check table location / permissions.")
            flash(f"Order {sale['order_id']} saved to Hive successfully.", "success")
            return redirect(url_for("sales"))
        except (ValueError, KeyError) as e:
            flash(f"Could not save: {e}", "error")
        except Exception as e:  # Hive errors must never look like success
            flash(f"Hive insert failed: {e}", "error")
    return render_template("add_sale.html", form=form, active="add",
                           categories=[g["name"] for g in safe(db.get_groups, "category")],
                           regions=[g["name"] for g in safe(db.get_groups, "region")],
                           payments=[g["name"] for g in safe(db.get_groups, "payment_method")])


def safe(fn, *a):
    try:
        return fn(*a)
    except Exception:
        return []


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
