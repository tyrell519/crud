from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import Base, get_db, engine
from models import User, Product, Category

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()
