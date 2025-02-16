from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL Database URL
DATABASE_URL = "mysql+pymysql://root:@localhost/storage_db"

# Create the MySQL engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Function to initialize the database
def init_db():
    Base.metadata.create_all(bind=engine)
