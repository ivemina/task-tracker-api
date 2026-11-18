import models  # noqa: F401  (importing registers the table with Base)
from database import Base, engine

Base.metadata.create_all(engine)
print("Tables created")