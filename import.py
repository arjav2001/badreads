import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    b = open("books.csv")
    reader = csv.reader(b)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, author, title, year) VALUES (:isbn, :author, :title, :year)",
            {"isbn": isbn, "title": title, "author": author, "year": year})
        print("Added {title} by {author} published in {year} with ISBN {isbn}.")
    db.commit()

if __name__ == "__main__":
    main()
