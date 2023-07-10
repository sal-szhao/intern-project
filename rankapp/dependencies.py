from .database import Session

# Session dependency.
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()