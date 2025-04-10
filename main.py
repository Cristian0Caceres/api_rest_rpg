from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session

# Configuración de la base de datos
DATABASE_URL = "sqlite:///./sqlite.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

# Modelos SQLAlchemy
class PersonajeDB(Base):
    __tablename__ = "personajes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    clase = Column(String)
    nivel = Column(Integer, default=1)
    experiencia = Column(Integer, default=0)
    misiones = relationship("MisionDB", back_populates="personaje", cascade="all, delete-orphan")

class MisionDB(Base):
    __tablename__ = "misiones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    descripcion = Column(String)
    estado = Column(String, default="Incompleta")
    experiencia = Column(Integer, default=50)
    personaje_id = Column(Integer, ForeignKey("personajes.id"))

    personaje = relationship("PersonajeDB", back_populates="misiones")

# Crear tablas
Base.metadata.create_all(bind=engine)

# Pydantic
class MisionCreate(BaseModel):
    nombre: str
    descripcion: str
    experiencia: int = 50

class MisionOut(MisionCreate):
    estado: str = "Incompleta"

    class Config:
        orm_mode = True

class PersonajeCreate(BaseModel):
    nombre: str
    clase: str

class PersonajeOut(BaseModel):
    id: int
    nombre: str
    clase: str
    nivel: int
    experiencia: int
    misiones: List[MisionOut] = []

    class Config:
        orm_mode = True

# Dependencia para obtener la sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI
app = FastAPI()
clases_posibles = ["Paladin", "picaro", "sacerdote", "barbaro"]

def xp_para_subir(nivel: int):
    return 100 * nivel

# Endpoints
@app.post("/personajes", response_model=PersonajeOut)
def crear_personaje(data: PersonajeCreate, db: Session = Depends(get_db)):
    if data.clase not in clases_posibles:
        raise HTTPException(status_code=400, detail="Clase no válida")

    if db.query(PersonajeDB).filter_by(nombre=data.nombre).first():
        raise HTTPException(status_code=400, detail="El personaje ya existe")

    personaje = PersonajeDB(nombre=data.nombre, clase=data.clase)
    db.add(personaje)
    db.commit()
    db.refresh(personaje)
    return personaje

@app.get("/personajes/{id}", response_model=PersonajeOut)
def obtener_personaje(id: int, db: Session = Depends(get_db)):
    personaje = db.query(PersonajeDB).filter_by(id=id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    return personaje

@app.post("/misiones")
def crear_mision(data: MisionCreate, db: Session = Depends(get_db)):
    return {"mensaje": "Usa el endpoint /personajes/{id}/misiones/{nombre_mision} para asignarla a un personaje."}

@app.post("/personajes/{id}/misiones/{nombre_m}")
def aceptar_mision(id: int, nombre_m: str, data: MisionCreate, db: Session = Depends(get_db)):
    personaje = db.query(PersonajeDB).filter_by(id=id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    # Verificar duplicado
    for m in personaje.misiones:
        if m.nombre.lower() == nombre_m.lower():
            raise HTTPException(status_code=400, detail="La misión ya fue aceptada")

    mision = MisionDB(nombre=nombre_m, descripcion=data.descripcion, experiencia=data.experiencia, personaje=personaje)
    db.add(mision)
    db.commit()
    return {"mensaje": f"Misión '{nombre_m}' aceptada por {personaje.nombre}"}

@app.post("/personajes/{id}/completar")
def completar_mision(id: int, db: Session = Depends(get_db)):
    personaje = db.query(PersonajeDB).filter_by(id=id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    if not personaje.misiones:
        raise HTTPException(status_code=400, detail="No hay misiones")

    mision = personaje.misiones[0]
    personaje.experiencia += mision.experiencia
    db.delete(mision)

    subidas = 0
    while personaje.experiencia >= xp_para_subir(personaje.nivel):
        personaje.experiencia -= xp_para_subir(personaje.nivel)
        personaje.nivel += 1
        subidas += 1

    db.commit()
    mensaje = f"Misión completada y ganó {mision.experiencia} XP."
    if subidas:
        mensaje += f" Subió {subidas} nivel(es)."

    return {"mensaje": mensaje}

@app.get("/personajes/{id}/misiones", response_model=List[MisionOut])
def listar_misiones(id: int, db: Session = Depends(get_db)):
    personaje = db.query(PersonajeDB).filter_by(id=id).first()
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    return personaje.misiones
