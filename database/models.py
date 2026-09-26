from datetime import datetime

from sqlalchemy import String, Text, BigInteger, func, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__="users"

    id:Mapped[int]=mapped_column(primary_key=True)
    tg_id:Mapped[int]=mapped_column(BigInteger,unique=True,index=True)
    full_name:Mapped[str]=mapped_column(String(255))
    username:Mapped[str | None]=mapped_column(String(255))
    created_at:Mapped[datetime]=mapped_column(DateTime, server_default=func.now())

class Book(Base):
    __tablename__="books"

    id:Mapped[int]=mapped_column(primary_key=True)
    title:Mapped[str]=mapped_column(String(255), index=True)
    author:Mapped[str]=mapped_column(String(255))
    description:Mapped[str | None]=mapped_column(Text)
    price:Mapped[float]=mapped_column(Numeric(12,2))
    stock:Mapped[int]=mapped_column(Integer,default=0)
    is_active:Mapped[bool]=mapped_column(default=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())

class Order(Base):
    __tablename__="orders"

    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    status:Mapped[str]=mapped_column(String(20),default="new")
    total:Mapped[float]=mapped_column(Numeric(12,2),default=0)
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())

    items:Mapped[list["OrderItem"]] = relationship(back_populates="order")

class OrderItem(Base):
    __tablename__="order_items"

    id:Mapped[int]=mapped_column(primary_key=True)
    order_id:Mapped[int]=mapped_column(ForeignKey("orders.id"))
    book_id:Mapped[int]=mapped_column(ForeignKey("books.id"))
    quantity:Mapped[int]=mapped_column(Integer)
    price:Mapped[float]=mapped_column(Numeric(12,2))

    order:Mapped["Order"]=relationship(back_populates="items")
    book:Mapped["Book"]=relationship()

class SearchLog(Base):
    __tablename__="search_logs"

    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"))
    query:Mapped[str]=mapped_column(String(255),index=True)
    found_count:Mapped[int]=mapped_column(Integer,default=0)
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())

