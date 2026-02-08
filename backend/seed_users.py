
import asyncio
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.user import User, UserRole
from app.core.security import get_password_hash

async def seed_users():
    async with async_session_maker() as session:
        # 1. Admin
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(admin)
            print("Created Admin: admin@example.com / admin123")
        
        # 2. Driver
        result = await session.execute(select(User).where(User.email == "driver@example.com"))
        if not result.scalar_one_or_none():
            driver = User(
                email="driver@example.com",
                hashed_password=get_password_hash("driver123"),
                full_name="Driver User",
                role=UserRole.DRIVER,
                is_active=True
            )
            session.add(driver)
            print("Created Driver: driver@example.com / driver123")

        # 3. Customer
        result = await session.execute(select(User).where(User.email == "customer@example.com"))
        if not result.scalar_one_or_none():
            customer = User(
                email="customer@example.com",
                hashed_password=get_password_hash("customer123"),
                full_name="Customer User",
                role=UserRole.CUSTOMER,
                is_active=True
            )
            session.add(customer)
            print("Created Customer: customer@example.com / customer123")
            
        await session.commit()
        print("User seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_users())
