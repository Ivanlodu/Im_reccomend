from database import engine, Base
from User import User

Base.metadata.create_all(bind=engine)
print("Tables created successfully.")