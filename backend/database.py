from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Emplacement du fichier de base de données SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:////app/data/sourcing.db"

# L'engine gère la connexion physique au fichier SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Chaque instance de SessionLocal sera une session de base de données active
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base de classe pour nos futurs modèles (tables)
Base = declarative_base()

# Fonction utilitaire pour ouvrir/fermer la connexion à chaque requête API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
