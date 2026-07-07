from .database import engine, Base
from .models import User, Track, Artist, ListenEvent

Base.metadata.create_all(bind=engine)
print("Tables created successfully.")