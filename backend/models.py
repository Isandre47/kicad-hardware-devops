from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relation : un projet a plusieurs lignes de BOM
    lines = relationship("BomLine", back_populates="project")

class BomLine(Base):
    __tablename__ = "bom_lines"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    reference = Column(String, index=True) # ex: C10, R1
    value_kicad = Column(String)           # ex: 22uF
    selected_mpn = Column(String, nullable=True) # Référence Mouser choisie au final

    project = relationship("Project", back_populates="lines")

class ComponentStat(Base):
    __tablename__ = "components_stats"

    mpn = Column(String, primary_key=True, index=True) # Référence fabricant unique
    manufacturer = Column(String)
    usage_count = Column(Integer, default=0)           # Compteur d'utilisation au BE
    is_preferred = Column(Boolean, default=False)      # Favori du Bureau d'Études
