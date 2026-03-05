import asyncio
import os
import asyncpg

async def fix_alembic():
    conn = await asyncpg.connect("postgresql://postgres:Password%401548@localhost:5432/interview_db")
    await conn.execute("UPDATE alembic_version SET version_num = 'b2c3d4e5f6a7'")
    await conn.close()
    print("Alembic version fixed!")

if __name__ == "__main__":
    asyncio.run(fix_alembic())
