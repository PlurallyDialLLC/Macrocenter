from typing import Any
import mysql.connector
import enum


class ProductType(enum.Enum):
    """
    Enumeration for product types.
    DO NOT CHANGE THIS WITHOUT DISCUSSING!
    """
    UNSORTED: int = 0
    PREBUILT: int = 1
    HARDWARE: int = 2
    SOFTWARE: int = 3
    ACCESSORY: int = 4
    TOOLS: int = 5

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Product:
    """
    Class for Products. (Yea, its in the name.)
    """

    def __init__(self, **kwargs):
        raise NotImplementedError("Currently not Implemented.")
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key: str) -> Any:
        return getattr(self, key, None)

    def set(self, key: str, value: Any):
        setattr(self, key, value)


class Database:
    PRODUCT_COLUMNS_FOR_RETURN = 'pid, product_type, name, description, price, product_image_keyword'

    def __init__(self, **kwargs):
        self.connection = kwargs.get("connection") or mysql.connector.connect(**kwargs)
        self.connection.autocommit = True

        self.db_info = self.connection.get_server_info() if self.connection.is_connected() else None

    # =========================
    # PRODUCT METHODS
    # =========================

    def get_products(self) -> list | None:
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute(f"SELECT {self.PRODUCT_COLUMNS_FOR_RETURN} FROM products;")
            return cursor.fetchall()

    def get_featured(self):
        return

    def get_product(self, pid: int) -> list:
        with self.connection.cursor(buffered=True) as cursor:
            query = f"""
                SELECT {self.PRODUCT_COLUMNS_FOR_RETURN}
                FROM products
                WHERE pid = %s AND do_hidden = FALSE
            """
            cursor.execute(query, (pid,))
            return cursor.fetchone()

    def search_products(self, query: str):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute(f"""
                SELECT {self.PRODUCT_COLUMNS_FOR_RETURN}
                FROM products
                WHERE name LIKE %s AND do_hidden = FALSE
                LIMIT 10
            """, (f"%{query}%",))
            return cursor.fetchall()

    # =========================
    # USER AUTH METHODS
    # =========================

    def create_user(self, username: str, email: str, password: str) -> None:
        """
        `password` should already be hashed before calling this.
        """
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )

    def get_user_by_username(self, username: str):
        """
        Allows login via username OR email.
        Returns: (id, username, email, password)
        """
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute(
                "SELECT id, username, email, password, is_admin FROM users WHERE username=%s OR email=%s",
                (username, username)
            )
            return cursor.fetchone()

    def get_user_by_id(self, user_id: int):
        """
        Required for Flask-Login session loading.
        """
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute(
                "SELECT id, username, email, password, is_admin FROM users WHERE id=%s",
                (user_id,)
            )
            return cursor.fetchone()

    def user_exists(self, username: str, email: str) -> bool:
        """
        Prevent duplicate accounts.
        """
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE username=%s OR email=%s",
                (username, email)
            )
            return cursor.fetchone() is not None

    def get_orders_by_user(self, user_id: int):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute("""
                SELECT id, total, status, created_at, shipping_address
                FROM orders
                WHERE user_id=%s
                ORDER BY created_at DESC
            """, (user_id,))
            return cursor.fetchall()

    def create_order(self, user_id, total, shipping_address):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute("""
                INSERT INTO orders (user_id, total, status, shipping_address)
                VALUES (%s, %s, %s, %s)
            """, (user_id, total, "Processing", shipping_address))

            return cursor.lastrowid
    def add_order_item(self, order_id: int, product_id: int, quantity: int, price: float):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, product_id, quantity, price))

    def get_order_items(self, order_id: int):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute("""
                SELECT product_id, quantity, price
                FROM order_items
                WHERE order_id=%s
            """, (order_id,))
            return cursor.fetchall()

    def get_order(self, order_id: int):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute("""
                SELECT id, user_id, total, status, created_at, shipping_address
                FROM orders
                WHERE id=%s
            """, (order_id,))
            return cursor.fetchone()

    def get_all_orders(self):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute("""
                SELECT id, user_id, total, status, created_at, shipping_address
                FROM orders
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()

    def update_order_status(self, order_id: int, status: str):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute("""
                UPDATE orders
                SET status=%s
                WHERE id=%s
            """, (status, order_id))

    def cancel_order(self, order_id: int, user_id: int):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute("""
                UPDATE orders
                SET status = 'Cancelled'
                WHERE id = %s AND user_id = %s AND status != 'Delivered'
            """, (order_id, user_id))


    def update_product(self, pid, name, description, price, product_type, image_keyword):
        with self.connection.cursor(buffered=True) as cursor:
            cursor.execute("""
                UPDATE products
                SET name=%s,
                    description=%s,
                    price=%s,
                    product_type=%s,
                    product_image_keyword=%s
                WHERE pid=%s
            """, (name, description, price, product_type, image_keyword, pid))
