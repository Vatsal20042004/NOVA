"""
Seed script to populate database with sample data
"""
import asyncio
from decimal import Decimal

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.product import Category, Product, ProductCategory
from app.models.inventory import Inventory

# Sample Categories
CATEGORIES = [
    {
        "name": "Electronics",
        "slug": "electronics",
        "description": "Latest gadgets and electronic devices",
        "image_url": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=400"
    },
    {
        "name": "Fashion",
        "slug": "fashion",
        "description": "Trendy clothing and accessories",
        "image_url": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=400"
    },
    {
        "name": "Home & Living",
        "slug": "home-living",
        "description": "Everything for your home",
        "image_url": "https://images.unsplash.com/photo-1484101403633-562f891dc89a?w=400"
    },
    {
        "name": "Sports & Outdoors",
        "slug": "sports-outdoors",
        "description": "Gear for active lifestyles",
        "image_url": "https://images.unsplash.com/photo-1461896836934-6df7d1c8be80?w=400"
    },
    {
        "name": "Beauty",
        "slug": "beauty",
        "description": "Skincare, makeup and beauty products",
        "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400"
    },
]

# Sample Products (prices in Indian Rupees - INR)
PRODUCTS = [
    # Electronics
    {
        "name": "Wireless Noise-Canceling Headphones",
        "slug": "wireless-noise-canceling-headphones",
        "description": "Premium over-ear headphones with active noise cancellation, 40-hour battery life, and crystal-clear audio. Features Bluetooth 5.2 and multipoint connection.",
        "price": Decimal("24999"),
        "discount_percent": Decimal("15.00"),
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600",
        "is_featured": True,
        "category": "electronics",
        "stock": 45
    },
    {
        "name": "Smart Watch Pro",
        "slug": "smart-watch-pro",
        "description": "Advanced smartwatch with health monitoring, GPS, and 7-day battery. Water resistant to 50m with always-on AMOLED display.",
        "price": Decimal("37499"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600",
        "is_featured": True,
        "category": "electronics",
        "stock": 30
    },
    {
        "name": "Portable Bluetooth Speaker",
        "slug": "portable-bluetooth-speaker",
        "description": "360° surround sound speaker with 20-hour playtime. IPX7 waterproof, perfect for outdoor adventures.",
        "price": Decimal("10899"),
        "discount_percent": Decimal("10.00"),
        "image_url": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600",
        "is_featured": False,
        "category": "electronics",
        "stock": 75
    },
    {
        "name": "4K Webcam",
        "slug": "4k-webcam",
        "description": "Ultra HD webcam with auto-focus, noise-canceling mic, and low-light correction. Perfect for remote work.",
        "price": Decimal("14999"),
        "discount_percent": Decimal("20.00"),
        "image_url": "https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=600",
        "is_featured": False,
        "category": "electronics",
        "stock": 50
    },
    {
        "name": "Mechanical Keyboard RGB",
        "slug": "mechanical-keyboard-rgb",
        "description": "Full-size mechanical keyboard with Cherry MX switches, per-key RGB backlight, and aluminium frame.",
        "price": Decimal("8999"),
        "discount_percent": Decimal("12.00"),
        "image_url": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=600",
        "is_featured": True,
        "category": "electronics",
        "stock": 55
    },
    {
        "name": "Wireless Earbuds Pro",
        "slug": "wireless-earbuds-pro",
        "description": "True wireless earbuds with active noise cancellation, 30hr total battery, and premium sound.",
        "price": Decimal("12999"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1598331668826-20cecc596b86?w=600",
        "is_featured": True,
        "category": "electronics",
        "stock": 90
    },
    {
        "name": "Tablet 10 inch",
        "slug": "tablet-10-inch",
        "description": "10-inch IPS display tablet with 128GB storage, quad speakers, and all-day battery.",
        "price": Decimal("18999"),
        "discount_percent": Decimal("15.00"),
        "image_url": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600",
        "is_featured": False,
        "category": "electronics",
        "stock": 40
    },
    {
        "name": "Power Bank 20000mAh",
        "slug": "power-bank-20000mah",
        "description": "Fast charging power bank with dual USB and Type-C. 20000mAh capacity, compact design.",
        "price": Decimal("2499"),
        "discount_percent": Decimal("10.00"),
        "image_url": "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=600",
        "is_featured": False,
        "category": "electronics",
        "stock": 120
    },
    # Fashion
    {
        "name": "Premium Leather Jacket",
        "slug": "premium-leather-jacket",
        "description": "Handcrafted genuine leather jacket with quilted lining. Timeless design meets modern comfort.",
        "price": Decimal("33299"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600",
        "is_featured": True,
        "category": "fashion",
        "stock": 20
    },
    {
        "name": "Designer Sunglasses",
        "slug": "designer-sunglasses",
        "description": "Polarized lenses with UV400 protection. Lightweight titanium frame with classic aviator style.",
        "price": Decimal("15799"),
        "discount_percent": Decimal("25.00"),
        "image_url": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600",
        "is_featured": True,
        "category": "fashion",
        "stock": 60
    },
    {
        "name": "Minimalist Watch",
        "slug": "minimalist-watch",
        "description": "Elegant timepiece with Swiss movement. Sapphire crystal glass and Italian leather strap.",
        "price": Decimal("20799"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=600",
        "is_featured": False,
        "category": "fashion",
        "stock": 35
    },
    {
        "name": "Classic Denim Jacket",
        "slug": "classic-denim-jacket",
        "description": "Vintage wash denim jacket with brass buttons. Comfortable fit for everyday wear.",
        "price": Decimal("4499"),
        "discount_percent": Decimal("20.00"),
        "image_url": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600",
        "is_featured": False,
        "category": "fashion",
        "stock": 70
    },
    {
        "name": "Leather Crossbody Bag",
        "slug": "leather-crossbody-bag",
        "description": "Handcrafted leather crossbody bag with multiple compartments. Perfect for daily use.",
        "price": Decimal("5999"),
        "discount_percent": Decimal("15.00"),
        "image_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=600",
        "is_featured": True,
        "category": "fashion",
        "stock": 45
    },
    {
        "name": "Running Shoes",
        "slug": "running-shoes",
        "description": "Lightweight running shoes with cushioned sole and breathable mesh upper. Ideal for long runs.",
        "price": Decimal("7499"),
        "discount_percent": Decimal("10.00"),
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600",
        "is_featured": True,
        "category": "fashion",
        "stock": 85
    },
    {
        "name": "Silk Scarf",
        "slug": "silk-scarf",
        "description": "Pure silk scarf with elegant print. Soft finish, versatile styling.",
        "price": Decimal("2999"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600",
        "is_featured": False,
        "category": "fashion",
        "stock": 100
    },
    # Home & Living
    {
        "name": "Scandinavian Floor Lamp",
        "slug": "scandinavian-floor-lamp",
        "description": "Modern minimalist design with adjustable arm. Warm LED lighting with dimmer control.",
        "price": Decimal("13299"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600",
        "is_featured": False,
        "category": "home-living",
        "stock": 25
    },
    {
        "name": "Luxury Scented Candle Set",
        "slug": "luxury-scented-candle-set",
        "description": "Set of 3 hand-poured soy candles. Notes of sandalwood, vanilla, and ocean breeze. 50-hour burn time each.",
        "price": Decimal("6649"),
        "discount_percent": Decimal("15.00"),
        "image_url": "https://images.unsplash.com/photo-1602028915047-37269d1a73f7?w=600",
        "is_featured": True,
        "category": "home-living",
        "stock": 100
    },
    {
        "name": "Ergonomic Office Chair",
        "slug": "ergonomic-office-chair",
        "description": "Premium mesh back with lumbar support. Adjustable armrests and headrest for all-day comfort.",
        "price": Decimal("45699"),
        "discount_percent": Decimal("10.00"),
        "image_url": "https://images.unsplash.com/photo-1592078615290-033ee584e267?w=600",
        "is_featured": True,
        "category": "home-living",
        "stock": 15
    },
    {
        "name": "Cotton Bed Sheet Set",
        "slug": "cotton-bed-sheet-set",
        "description": "300 thread count 100% cotton bed sheet set. Includes flat sheet, fitted sheet, and pillowcases.",
        "price": Decimal("4999"),
        "discount_percent": Decimal("20.00"),
        "image_url": "https://images.unsplash.com/photo-1631889993959-41b4e9c6e3c5?w=600",
        "is_featured": False,
        "category": "home-living",
        "stock": 80
    },
    {
        "name": "Decorative Throw Pillows",
        "slug": "decorative-throw-pillows",
        "description": "Set of 4 designer throw pillows with removable covers. Mix of geometric and solid colours.",
        "price": Decimal("3499"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=600",
        "is_featured": False,
        "category": "home-living",
        "stock": 60
    },
    {
        "name": "Stainless Steel Cookware Set",
        "slug": "stainless-steel-cookware-set",
        "description": "5-piece induction-compatible cookware set. Dishwasher safe, even heat distribution.",
        "price": Decimal("8999"),
        "discount_percent": Decimal("12.00"),
        "image_url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600",
        "is_featured": True,
        "category": "home-living",
        "stock": 35
    },
    {
        "name": "Wooden Bookshelf",
        "slug": "wooden-bookshelf",
        "description": "Solid wood 5-tier bookshelf. Modern design, easy assembly, fits in compact spaces.",
        "price": Decimal("12499"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1594620300380-7ef9c2f518a6?w=600",
        "is_featured": False,
        "category": "home-living",
        "stock": 22
    },
    # Sports & Outdoors
    {
        "name": "Premium Yoga Mat",
        "slug": "premium-yoga-mat",
        "description": "Eco-friendly natural rubber mat with alignment lines. Extra thick 6mm cushioning with non-slip surface.",
        "price": Decimal("7499"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=600",
        "is_featured": False,
        "category": "sports-outdoors",
        "stock": 80
    },
    {
        "name": "Stainless Steel Water Bottle",
        "slug": "stainless-steel-water-bottle",
        "description": "Double-walled vacuum insulation keeps drinks cold 24hr or hot 12hr. 32oz capacity, BPA-free.",
        "price": Decimal("3329"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600",
        "is_featured": False,
        "category": "sports-outdoors",
        "stock": 150
    },
    {
        "name": "Resistance Bands Set",
        "slug": "resistance-bands-set",
        "description": "Set of 5 resistance bands with different strength levels. Includes carry bag and door anchor.",
        "price": Decimal("1499"),
        "discount_percent": Decimal("25.00"),
        "image_url": "https://images.unsplash.com/photo-1598289431512-b97b0917affc?w=600",
        "is_featured": True,
        "category": "sports-outdoors",
        "stock": 95
    },
    {
        "name": "Camping Tent 2-Person",
        "slug": "camping-tent-2-person",
        "description": "Lightweight 2-person tent, water-resistant, easy setup. Perfect for weekend getaways.",
        "price": Decimal("8999"),
        "discount_percent": Decimal("10.00"),
        "image_url": "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=600",
        "is_featured": True,
        "category": "sports-outdoors",
        "stock": 30
    },
    {
        "name": "Cycling Helmet",
        "slug": "cycling-helmet",
        "description": "Ventilated cycling helmet with adjustable fit. Meets safety standards, lightweight.",
        "price": Decimal("2499"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?w=600",
        "is_featured": False,
        "category": "sports-outdoors",
        "stock": 75
    },
    {
        "name": "Dumbbells Set 2x5kg",
        "slug": "dumbbells-set-2x5kg",
        "description": "Pair of 5kg cast iron dumbbells with neoprene coating. Ideal for home workouts.",
        "price": Decimal("2999"),
        "discount_percent": Decimal("15.00"),
        "image_url": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=600",
        "is_featured": False,
        "category": "sports-outdoors",
        "stock": 50
    },
    {
        "name": "Running Armband",
        "slug": "running-armband",
        "description": "Adjustable armband for phone while running. Sweat-resistant, fits most smartphones.",
        "price": Decimal("499"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=600",
        "is_featured": False,
        "category": "sports-outdoors",
        "stock": 200
    },
    # Beauty
    {
        "name": "Vitamin C Serum",
        "slug": "vitamin-c-serum",
        "description": "20% Vitamin C with hyaluronic acid and Vitamin E. Brightening formula for radiant skin.",
        "price": Decimal("4999"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=600",
        "is_featured": True,
        "category": "beauty",
        "stock": 120
    },
    {
        "name": "Luxury Perfume",
        "slug": "luxury-perfume",
        "description": "Exquisite blend of jasmine, bergamot, and musk. Long-lasting 50ml eau de parfum.",
        "price": Decimal("12499"),
        "discount_percent": Decimal("20.00"),
        "image_url": "https://images.unsplash.com/photo-1541643600914-78b084683601?w=600",
        "is_featured": True,
        "category": "beauty",
        "stock": 40
    },
    {
        "name": "Makeup Brush Set",
        "slug": "makeup-brush-set",
        "description": "Professional 12-piece brush set with vegan bristles. Includes elegant carrying case.",
        "price": Decimal("5829"),
        "discount_percent": Decimal("10.00"),
        "image_url": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=600",
        "is_featured": False,
        "category": "beauty",
        "stock": 65
    },
    {
        "name": "Sunscreen SPF 50",
        "slug": "sunscreen-spf-50",
        "description": "Broad spectrum SPF 50 PA+++ sunscreen. Lightweight, non-greasy, suitable for all skin types.",
        "price": Decimal("899"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=600",
        "is_featured": True,
        "category": "beauty",
        "stock": 150
    },
    {
        "name": "Hyaluronic Acid Moisturiser",
        "slug": "hyaluronic-acid-moisturiser",
        "description": "Intensive hydrating moisturiser with hyaluronic acid. 50ml, dermatologist tested.",
        "price": Decimal("1299"),
        "discount_percent": Decimal("15.00"),
        "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=600",
        "is_featured": False,
        "category": "beauty",
        "stock": 110
    },
    {
        "name": "Lipstick Set",
        "slug": "lipstick-set",
        "description": "Set of 4 long-lasting lipsticks in nude and red shades. Cruelty-free, vegan formula.",
        "price": Decimal("2499"),
        "discount_percent": Decimal("20.00"),
        "image_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=600",
        "is_featured": True,
        "category": "beauty",
        "stock": 70
    },
    {
        "name": "Face Mask 5-Pack",
        "slug": "face-mask-5-pack",
        "description": "Sheet mask 5-pack with green tea and aloe. Hydrating and soothing for all skin types.",
        "price": Decimal("599"),
        "discount_percent": Decimal("0.00"),
        "image_url": "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=600",
        "is_featured": False,
        "category": "beauty",
        "stock": 180
    },
]


async def seed_database():
    """Seed the database with sample data"""
    async with async_session_maker() as session:
        # Check if data already exists
        result = await session.execute(select(Category).limit(1))
        if result.scalar_one_or_none():
            print("Database already has data. Skipping seed.")
            return
        
        print("Seeding database...")
        
        # Create categories
        category_map = {}
        for cat_data in CATEGORIES:
            category = Category(**cat_data)
            session.add(category)
            category_map[cat_data["slug"]] = category
        
        await session.flush()  # Get IDs
        
        # Create products with inventory
        for prod_data in PRODUCTS:
            cat_slug = prod_data.pop("category")
            stock = prod_data.pop("stock")
            
            product = Product(**prod_data)
            session.add(product)
            await session.flush()  # Get product ID
            
            # Link to category
            category = category_map[cat_slug]
            product_category = ProductCategory(
                product_id=product.id,
                category_id=category.id
            )
            session.add(product_category)
            
            # Create inventory
            inventory = Inventory(
                product_id=product.id,
                quantity=stock,
                reserved=0,
                low_stock_threshold=10
            )
            session.add(inventory)
        
        await session.commit()
        print(f"✓ Created {len(CATEGORIES)} categories")
        print(f"✓ Created {len(PRODUCTS)} products with inventory")
        print("Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
