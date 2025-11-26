from sqlmodel import create_engine, SQLModel, Session

db_filename = "database.db"
sqlite_url = f"sqlite:///{db_filename}"

engine = create_engine(sqlite_url, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def init_session():
    with Session(engine) as session:
        yield session