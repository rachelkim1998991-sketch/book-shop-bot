import asyncio

from database.models import Book
from database.session import async_session,init_db

BOOKS=[
    {"title": "Atomic Habits", "author": "James Clear", "description": "Kichik odatlar, katta natijalar.",
     "price": 85000, "stock": 12},
    {"title": "Sariq devni minib", "author": "Xudoyberdi To'xtaboyev",
     "description": "O'zbek bolalar adabiyotining sara asari.", "price": 45000, "stock": 20},
    {"title": "O'tkan kunlar", "author": "Abdulla Qodiriy", "description": "O'zbek mumtoz romani.", "price": 60000,
     "stock": 15},
    {"title": "Rich Dad Poor Dad", "author": "Robert Kiyosaki", "description": "Moliyaviy savodxonlik haqida.",
     "price": 70000, "stock": 8},
    {"title": "1984", "author": "George Orwell", "description": "Distopik roman.", "price": 55000, "stock": 10},
    {"title": "Sapiens", "author": "Yuval Noah Harari", "description": "Insoniyat qisqacha tarixi.", "price": 90000,
     "stock": 5},
    {"title": "Mehrobdan chayon", "author": "Abdulla Qodiriy", "description": "Tarixiy roman.", "price": 50000,
     "stock": 0},
]

async def seed():
    await init_db()
    async with async_session() as session:
        for data in BOOKS:
            session.add(Book(**data))
        await session.commit()
    print(f"{len(BOOKS)} ta kitob qo'shildi.")

if __name__=="__main__":
    asyncio.run(seed())