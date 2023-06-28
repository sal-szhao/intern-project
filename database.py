from sqlalchemy.orm import registry
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

mapper_registry = registry()

engine = create_engine("sqlite://", echo=True)

Session = sessionmaker(bind=engine, future=True)