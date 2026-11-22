"""
Database seed data generator.

Generates realistic e-commerce data using Faker with a fixed random seed
for deterministic, reproducible results.

Target volumes:
- ~1,000 customers
- ~100 products
- ~5,000 orders
- ~10,000+ order items
- Corresponding payments
"""

import logging
import random
from datetime import date, timedelta
from decimal import Decimal

from faker import Faker
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import admin_session, get_admin_engine
from app.database.models import Base, Customer, Order, OrderItem, Payment, Product

logger = logging.getLogger(__name__)

# Fixed seed for deterministic data
RANDOM_SEED = 42
fake = Faker()
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Product catalog
# ---------------------------------------------------------------------------

PRODUCT_CATALOG = [
    # Electronics
    ("Wireless Bluetooth Headphones", "Electronics", 79.99, 32.00),
    ("USB-C Fast Charger", "Electronics", 24.99, 8.50),
    ("Portable Power Bank 20000mAh", "Electronics", 44.99, 18.00),
    ("Smart Watch Pro", "Electronics", 199.99, 85.00),
    ("Noise Cancelling Earbuds", "Electronics", 129.99, 48.00),
    ("4K Webcam", "Electronics", 89.99, 35.00),
    ("Mechanical Keyboard RGB", "Electronics", 109.99, 42.00),
    ("Wireless Gaming Mouse", "Electronics", 59.99, 22.00),
    ("Portable Bluetooth Speaker", "Electronics", 49.99, 18.00),
    ("Smart Home Hub", "Electronics", 149.99, 62.00),
    ("Tablet Stand Adjustable", "Electronics", 29.99, 10.00),
    ("Wireless Charging Pad", "Electronics", 34.99, 12.00),
    ("HDMI Cable 6ft", "Electronics", 12.99, 3.50),
    ("USB Hub 7-Port", "Electronics", 39.99, 14.00),
    ("Smart LED Light Strip", "Electronics", 27.99, 9.00),
    # Clothing
    ("Classic Cotton T-Shirt", "Clothing", 19.99, 6.00),
    ("Slim Fit Denim Jeans", "Clothing", 49.99, 18.00),
    ("Casual Hoodie", "Clothing", 39.99, 14.00),
    ("Winter Puffer Jacket", "Clothing", 89.99, 35.00),
    ("Running Sneakers", "Clothing", 74.99, 28.00),
    ("Formal Dress Shirt", "Clothing", 44.99, 16.00),
    ("Yoga Pants", "Clothing", 34.99, 11.00),
    ("Canvas Backpack", "Clothing", 54.99, 20.00),
    ("Leather Belt", "Clothing", 29.99, 10.00),
    ("Wool Beanie Hat", "Clothing", 14.99, 4.00),
    ("Athletic Shorts", "Clothing", 24.99, 8.00),
    ("Silk Scarf", "Clothing", 39.99, 12.00),
    ("Rain Jacket", "Clothing", 64.99, 25.00),
    ("Cotton Socks 6-Pack", "Clothing", 16.99, 4.50),
    ("Polarized Sunglasses", "Clothing", 34.99, 11.00),
    # Home & Kitchen
    ("Stainless Steel Water Bottle", "Home & Kitchen", 22.99, 7.00),
    ("Non-Stick Frying Pan", "Home & Kitchen", 34.99, 12.00),
    ("Coffee Maker Programmable", "Home & Kitchen", 69.99, 28.00),
    ("Memory Foam Pillow", "Home & Kitchen", 44.99, 16.00),
    ("Bamboo Cutting Board Set", "Home & Kitchen", 29.99, 10.00),
    ("Electric Kettle", "Home & Kitchen", 39.99, 15.00),
    ("Cast Iron Dutch Oven", "Home & Kitchen", 59.99, 24.00),
    ("Silicone Baking Mat", "Home & Kitchen", 14.99, 4.00),
    ("Glass Food Storage Set", "Home & Kitchen", 34.99, 12.00),
    ("Ceramic Dinner Plate Set", "Home & Kitchen", 49.99, 18.00),
    ("Kitchen Knife Set", "Home & Kitchen", 79.99, 30.00),
    ("Microfiber Cleaning Cloths", "Home & Kitchen", 12.99, 3.00),
    ("Air Purifier HEPA", "Home & Kitchen", 129.99, 52.00),
    ("Desk Organizer", "Home & Kitchen", 24.99, 8.00),
    ("Scented Candle Set", "Home & Kitchen", 19.99, 6.00),
    # Books
    ("Python Programming Guide", "Books", 39.99, 12.00),
    ("Data Science Handbook", "Books", 44.99, 14.00),
    ("Machine Learning Basics", "Books", 49.99, 16.00),
    ("Business Strategy 101", "Books", 29.99, 9.00),
    ("Creative Writing Workshop", "Books", 24.99, 8.00),
    ("Financial Planning Guide", "Books", 34.99, 11.00),
    ("Cooking for Beginners", "Books", 22.99, 7.00),
    ("History of Innovation", "Books", 27.99, 9.00),
    ("Mindfulness & Meditation", "Books", 19.99, 6.00),
    ("Photography Masterclass", "Books", 36.99, 12.00),
    # Sports & Outdoors
    ("Yoga Mat Premium", "Sports & Outdoors", 34.99, 12.00),
    ("Resistance Bands Set", "Sports & Outdoors", 19.99, 6.00),
    ("Camping Tent 2-Person", "Sports & Outdoors", 89.99, 35.00),
    ("Hiking Backpack 40L", "Sports & Outdoors", 69.99, 28.00),
    ("Jump Rope Speed", "Sports & Outdoors", 14.99, 4.00),
    ("Foam Roller", "Sports & Outdoors", 24.99, 8.00),
    ("Dumbbell Set Adjustable", "Sports & Outdoors", 149.99, 60.00),
    ("Bike Helmet", "Sports & Outdoors", 44.99, 16.00),
    ("Fishing Rod Combo", "Sports & Outdoors", 59.99, 22.00),
    ("Soccer Ball Official", "Sports & Outdoors", 29.99, 10.00),
    # Beauty & Health
    ("Moisturizing Face Cream", "Beauty & Health", 24.99, 7.00),
    ("Vitamin D Supplements", "Beauty & Health", 14.99, 4.00),
    ("Hair Dryer Professional", "Beauty & Health", 49.99, 18.00),
    ("Essential Oils Set", "Beauty & Health", 29.99, 9.00),
    ("Electric Toothbrush", "Beauty & Health", 39.99, 14.00),
    ("Sunscreen SPF 50", "Beauty & Health", 16.99, 5.00),
    ("Protein Powder 2lb", "Beauty & Health", 34.99, 12.00),
    ("Lip Balm Collection", "Beauty & Health", 9.99, 2.50),
    ("Hand Sanitizer Pack", "Beauty & Health", 12.99, 3.00),
    ("First Aid Kit", "Beauty & Health", 22.99, 8.00),
    # Toys & Games
    ("Building Blocks 500pc", "Toys & Games", 34.99, 12.00),
    ("Board Game Classic", "Toys & Games", 24.99, 8.00),
    ("Remote Control Car", "Toys & Games", 44.99, 16.00),
    ("Puzzle 1000 Pieces", "Toys & Games", 19.99, 6.00),
    ("Card Game Strategy", "Toys & Games", 14.99, 4.00),
    ("Action Figure Collectible", "Toys & Games", 29.99, 10.00),
    ("Science Experiment Kit", "Toys & Games", 39.99, 14.00),
    ("Art Supply Set", "Toys & Games", 27.99, 9.00),
    ("Stuffed Animal Plush", "Toys & Games", 17.99, 5.00),
    ("Outdoor Play Set", "Toys & Games", 54.99, 20.00),
    # Office Supplies
    ("Ergonomic Office Chair", "Office Supplies", 249.99, 100.00),
    ("Standing Desk Converter", "Office Supplies", 179.99, 72.00),
    ("Notebook 3-Pack", "Office Supplies", 12.99, 3.50),
    ("Ballpoint Pen Set", "Office Supplies", 8.99, 2.00),
    ("Desk Lamp LED", "Office Supplies", 34.99, 12.00),
    ("File Organizer", "Office Supplies", 19.99, 6.00),
    ("Whiteboard 24x36", "Office Supplies", 44.99, 16.00),
    ("Sticky Notes Assorted", "Office Supplies", 7.99, 2.00),
    ("Paper Shredder", "Office Supplies", 59.99, 24.00),
    ("Monitor Stand Riser", "Office Supplies", 39.99, 14.00),
]

COUNTRIES_CITIES = {
    "United States": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "San Francisco", "Seattle", "Denver", "Miami", "Boston"],
    "United Kingdom": ["London", "Manchester", "Birmingham", "Edinburgh", "Bristol", "Leeds"],
    "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne"],
    "France": ["Paris", "Lyon", "Marseille", "Toulouse", "Nice"],
    "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
    "India": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"],
    "Japan": ["Tokyo", "Osaka", "Yokohama", "Nagoya", "Sapporo"],
    "Brazil": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Curitiba"],
    "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht"],
}

ORDER_STATUSES = ["completed", "completed", "completed", "completed", "processing", "pending", "cancelled", "refunded"]
PAYMENT_METHODS = ["credit_card", "credit_card", "credit_card", "debit_card", "debit_card", "paypal", "bank_transfer", "crypto"]


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

def _is_seeded(session: Session) -> bool:
    """Check if seed data already exists."""
    count = session.execute(text("SELECT COUNT(*) FROM customers")).scalar()
    return count > 0


def _seed_customers(session: Session, count: int = 1000) -> list[Customer]:
    """Generate customer records."""
    logger.info("Seeding %d customers...", count)
    customers = []
    used_emails: set[str] = set()

    for i in range(count):
        country = random.choice(list(COUNTRIES_CITIES.keys()))
        city = random.choice(COUNTRIES_CITIES[country])

        # Ensure unique email
        email = fake.email()
        while email in used_emails:
            email = fake.email()
        used_emails.add(email)

        # Signup dates spread across 2023-01-01 to 2025-12-31
        start = date(2023, 1, 1)
        end = date(2025, 12, 31)
        days_range = (end - start).days
        signup = start + timedelta(days=random.randint(0, days_range))

        customer = Customer(
            name=fake.name(),
            email=email,
            country=country,
            city=city,
            signup_date=signup,
        )
        customers.append(customer)

    session.add_all(customers)
    session.flush()
    logger.info("Customers seeded: %d", len(customers))
    return customers


def _seed_products(session: Session) -> list[Product]:
    """Generate product records from the catalog."""
    logger.info("Seeding %d products...", len(PRODUCT_CATALOG))
    products = []
    for name, category, price, cost in PRODUCT_CATALOG:
        product = Product(
            product_name=name,
            category=category,
            price=Decimal(str(price)),
            cost=Decimal(str(cost)),
        )
        products.append(product)

    session.add_all(products)
    session.flush()
    logger.info("Products seeded: %d", len(products))
    return products


def _seed_orders_and_items(
    session: Session,
    customers: list[Customer],
    products: list[Product],
    order_count: int = 5000,
) -> tuple[list[Order], list[OrderItem]]:
    """Generate orders and order items."""
    logger.info("Seeding %d orders...", order_count)
    orders = []
    all_items = []

    for _ in range(order_count):
        customer = random.choice(customers)

        # Order date: after customer signup, up to 2025-12-31
        earliest = max(customer.signup_date, date(2023, 1, 1))
        latest = date(2025, 12, 31)
        if earliest > latest:
            earliest = latest
        days_range = (latest - earliest).days
        order_date = earliest + timedelta(days=random.randint(0, max(days_range, 0)))

        status = random.choice(ORDER_STATUSES)

        # Generate 1-5 line items per order
        num_items = random.choices([1, 2, 3, 4, 5], weights=[30, 35, 20, 10, 5])[0]
        selected_products = random.sample(products, min(num_items, len(products)))

        order_total = Decimal("0.00")
        items = []

        for prod in selected_products:
            quantity = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
            # Slight price variation (sales, discounts)
            price_factor = random.uniform(0.85, 1.05)
            unit_price = round(float(prod.price) * price_factor, 2)
            line_total = Decimal(str(round(unit_price * quantity, 2)))
            order_total += line_total

            item = OrderItem(
                product_id=prod.product_id,
                quantity=quantity,
                unit_price=Decimal(str(unit_price)),
            )
            items.append(item)

        order = Order(
            customer_id=customer.customer_id,
            order_date=order_date,
            status=status,
            total_amount=order_total,
        )
        orders.append(order)
        session.add(order)
        session.flush()  # Get order_id

        for item in items:
            item.order_id = order.order_id
            all_items.append(item)

    session.add_all(all_items)
    session.flush()
    logger.info("Orders seeded: %d, Order items seeded: %d", len(orders), len(all_items))
    return orders, all_items


def _seed_payments(session: Session, orders: list[Order]) -> list[Payment]:
    """Generate payment records for orders."""
    logger.info("Seeding payments for %d orders...", len(orders))
    payments = []

    for order in orders:
        payment_method = random.choice(PAYMENT_METHODS)

        # Payment status mirrors order status
        if order.status == "cancelled":
            payment_status = "failed"
        elif order.status == "refunded":
            payment_status = "refunded"
        elif order.status == "pending":
            payment_status = "pending"
        else:
            payment_status = "completed"

        # Payment date: same day or a few days after order
        payment_date = order.order_date + timedelta(days=random.randint(0, 3))

        payment = Payment(
            order_id=order.order_id,
            payment_method=payment_method,
            payment_status=payment_status,
            payment_date=payment_date,
            amount=order.total_amount,
        )
        payments.append(payment)

    session.add_all(payments)
    session.flush()
    logger.info("Payments seeded: %d", len(payments))
    return payments


# ---------------------------------------------------------------------------
# Main seed entry point
# ---------------------------------------------------------------------------

def create_tables() -> None:
    """Create all tables if they don't exist."""
    engine = get_admin_engine()
    Base.metadata.create_all(engine)
    logger.info("Database tables created/verified")


def seed_database() -> None:
    """
    Seed the database with realistic e-commerce data.

    Idempotent: skips if data already exists.
    Deterministic: uses fixed random seed for reproducibility.
    """
    create_tables()

    with admin_session() as session:
        if _is_seeded(session):
            logger.info("Database already seeded — skipping")
            return

        logger.info("Starting database seed...")
        customers = _seed_customers(session, count=1000)
        products = _seed_products(session)
        orders, items = _seed_orders_and_items(session, customers, products, order_count=5000)
        _seed_payments(session, orders)

        logger.info(
            "Seed complete: %d customers, %d products, %d orders, %d items",
            len(customers), len(products), len(orders), len(items),
        )


def create_readonly_user() -> None:
    """
    Create a read-only database user for safe query execution.

    This should be run once during initial setup.
    Failures are logged but not raised (user may already exist).
    """
    engine = get_admin_engine()
    try:
        with engine.connect() as conn:
            # Create user if not exists
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly_user') THEN
                        CREATE ROLE readonly_user WITH LOGIN PASSWORD 'readonly_pass';
                    END IF;
                END
                $$;
            """))
            conn.execute(text("GRANT CONNECT ON DATABASE agenticsql TO readonly_user;"))
            conn.execute(text("GRANT USAGE ON SCHEMA public TO readonly_user;"))
            conn.execute(text("GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;"))
            conn.execute(text(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;"
            ))
            conn.commit()
        logger.info("Read-only database user created/verified")
    except Exception as e:
        logger.warning("Could not create readonly user (may already exist): %s", e)
