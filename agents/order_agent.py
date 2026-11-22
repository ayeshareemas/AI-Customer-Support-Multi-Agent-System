import sqlite3


def lookup_order(order_id, db_path="customer_support.db"):

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT order_id, customer_name,
                   product_name, order_status
            FROM orders
            WHERE order_id = ? COLLATE NOCASE
        """, (order_id,))

        order = cursor.fetchone()

        if order:
            return dict(order)

        return None

    finally:
        conn.close()