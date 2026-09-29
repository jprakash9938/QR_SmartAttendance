"""Delete the admin record from DB so seed_initial_admin re-creates it with correct bcrypt hash."""
import asyncio
import aiomysql


async def fix():
    conn = await aiomysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="Satya@123",
        db="attendance1",
    )
    async with conn.cursor() as cur:
        await cur.execute(
            "DELETE FROM users WHERE email = %s",
            ("gyanaranjan7591@gmail.com",),
        )
        await conn.commit()
        print(f"Deleted {cur.rowcount} admin user(s). Will be re-seeded correctly on next startup.")
    conn.close()


asyncio.run(fix())
