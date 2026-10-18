"""All Hive access lives here. Hive is the ONLY database used."""
import time
from pyhive import hive
from TCLIService.ttypes import TOperationState

TABLE = "ecommerce.sales"
COLUMNS = ["order_id", "order_date", "product", "category",
           "quantity", "price", "region", "payment_method", "total_amount"]

SELECT_ROWS = (
    "SELECT order_id, CAST(order_date AS STRING), product, category, quantity, "
    "price, region, payment_method, quantity * price AS total_amount "
    f"FROM {TABLE}"
)


def get_connection():
    return hive.Connection(
        host="localhost",
        port=10000,
        username="hive",
        auth="NONE",
        # COUNT(*) etc. must scan real data, not stale metastore statistics
        configuration={"hive.compute.query.using.stats": "false"},
    )


def query(sql, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params) if params else cur.execute(sql)
        return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=None):
    """Run a statement and WAIT until Hive has really finished it.

    Without waiting, closing the connection right after submit cancels the
    INSERT job, so the app said "saved" but no row was ever written.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params, async_=True)
        status = cur.poll()
        while status.operationState in (
            TOperationState.INITIALIZED_STATE,
            TOperationState.PENDING_STATE,
            TOperationState.RUNNING_STATE,
        ):
            time.sleep(1)
            status = cur.poll()
        if status.operationState != TOperationState.FINISHED_STATE:
            raise RuntimeError(
                f"Hive job failed ({TOperationState._VALUES_TO_NAMES.get(status.operationState)}): "
                f"{status.errorMessage or 'no error message returned'}"
            )
        cur.close()
    finally:
        conn.close()


def _to_dicts(rows):
    return [dict(zip(COLUMNS, r)) for r in rows]


def get_summary():
    r = query(f"SELECT COUNT(*), SUM(quantity * price), AVG(quantity * price) FROM {TABLE}")[0]
    orders = int(r[0] or 0)
    total = float(r[1] or 0)
    avg = float(r[2] or 0)
    return {"orders": orders, "sales": total, "avg": avg}


def get_all_sales():
    return _to_dicts(query(SELECT_ROWS + " ORDER BY order_id"))


def get_groups(column):
    """Distinct values of a column with order count and sales total."""
    assert column in ("category", "region", "product", "payment_method")
    rows = query(
        f"SELECT {column}, COUNT(*), SUM(quantity * price) FROM {TABLE} "
        f"GROUP BY {column} ORDER BY {column}"
    )
    return [{"name": r[0], "orders": int(r[1]), "sales": float(r[2] or 0)} for r in rows]


def get_sales_by(column, value):
    assert column in ("category", "region", "product", "payment_method")
    rows = query(SELECT_ROWS + f" WHERE {column} = %(v)s ORDER BY order_id", {"v": value})
    return _to_dicts(rows)


def order_exists(order_id):
    r = query(f"SELECT COUNT(*) FROM {TABLE} WHERE order_id = %(i)s", {"i": int(order_id)})
    return int(r[0][0]) > 0


def insert_sale(s):
    execute(
        f"INSERT INTO TABLE {TABLE} SELECT "
        "%(order_id)s, CAST(%(order_date)s AS DATE), %(product)s, %(category)s, "
        "%(quantity)s, %(price)s, %(region)s, %(payment_method)s",
        s,
    )


def search_sales(text):
    like = "%" + text.lower() + "%"
    rows = query(
        SELECT_ROWS + " WHERE lower(product) LIKE %(q)s OR lower(category) LIKE %(q)s "
        "OR lower(region) LIKE %(q)s OR lower(payment_method) LIKE %(q)s "
        "OR CAST(order_id AS STRING) LIKE %(q)s ORDER BY order_id",
        {"q": like},
    )
    return _to_dicts(rows)
