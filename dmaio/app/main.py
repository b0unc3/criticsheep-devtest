from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, func, text
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime

DATABASE_URL = "sqlite:///./elevator.db" 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Database Models
class Elevator(Base):
    """
    The Elevator class represents an elevator entity in a building.
    Attributes:
        id (int): The unique identifier for the elevator.
        name (str): The name of the elevator.
        location (str): The location of the elevator within the building.
    """
    __tablename__ = "elevators"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)

class Movement(Base):
    """
    The Movement class represents the movement of an elevator between floors.
    Attributes:
        id (int): The unique identifier for the movement.
        elevator_id (int): The identifier of the elevator involved in the movement.
        start_floor (int): The floor where the movement started.
        end_floor (int): The floor where the movement ended.
        arrival_time (datetime): The time when the elevator arrived at the end floor.
        departure_time (datetime): The time when the elevator departed from the start floor.
    """
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    elevator_id = Column(Integer, ForeignKey("elevators.id"), nullable=False)
    start_floor = Column(Integer, nullable=False)
    end_floor = Column(Integer, nullable=False)
    arrival_time = Column(DateTime, nullable=False, default=func.now())
    departure_time = Column(DateTime, nullable=True)


# Pydantic Schemas 
class ElevatorCreate(BaseModel):
    name: str
    location: str

class MovementCreate(BaseModel):
    elevator_id: int
    start_floor: int
    end_floor: int
    departure_time: datetime | None = None
    

# Dependency for DB Session
def get_db():
    """
    Provides a database session for use in a context manager.
    Yields:
        db (SessionLocal): A database session object.
    Ensures that the database session is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/elevators", summary="Get all elevators", description="Get all elevators from the database")
def get_elevators(db: Session = Depends(get_db)):
    """
    Retrieves a list of all elevators from the database.
    Args:
        db (Session): The database session dependency.
    Returns:
        List[Elevator]: A list of all elevator records.
    """
    return db.query(Elevator).all()

@app.post("/elevators/", summary="Create a new elevator", description="Create a new elevator record in the database")
def create_elevator(elevator: ElevatorCreate, db: Session = Depends(get_db)):
    """
    Creates a new elevator record in the database.
        Args:
            elevator (ElevatorCreate): The elevator data to create.
            db (Session): The database session dependency.
        Returns:
            Elevator: The created elevator record.    
    """
    db_elevator = Elevator(**elevator.model_dump())
    db.add(db_elevator)
    db.commit()
    db.refresh(db_elevator)
    return db_elevator

@app.post("/movements/", summary="Log a movement", description="Log a new movement record in the database")
def log_movement(movement: MovementCreate, db: Session = Depends(get_db)):
    """
    Logs a new movement record in the database.
        Args:
            movement (MovementCreate): The movement data to log.
            db (Session): The database session dependency.
        Returns:
            Movement: The logged movement record.
    """
    db_movement = Movement(**movement.model_dump())
    # check if there is a movement record with the same elevator_id that has no departure_time
    db_movement_match = db.query(Movement).filter(Movement.elevator_id == db_movement.elevator_id).where(Movement.departure_time == None).first()
    if db_movement_match is not None:
        # if there is a match, update the departure_time of the match    
        db_movement_match.departure_time = datetime.now()
        db.commit()
        db.refresh(db_movement_match)
        
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement

@app.get("/movements/", description="Get all movements", summary="Get all movements from the database")
def get_movements(db: Session = Depends(get_db)):
    """
    Retrieves a list of all movements from the database.
    Args:
        db (Session): The database session dependency.
    Returns:
        List[Movement]: A list of all movement records.
    """
    return db.query(Movement).all()

@app.get("/movements/{elevator_id}", description="Get all movements for a specific elevator", summary="Get all movements for a specific elevator")
def get_movements(eid: int, db: Session = Depends(get_db)):
    """
    Retrieves a list of all movements from the database.
    Args:
        db (Session): The database session dependency.
    Returns:
        List[Movement]: A list of all movement records.
    """
    return db.query(Movement).where(Movement.elevator_id == eid).all()

@app.get("/resting_elevators", description="Get all resting elevators", summary="Get all resting elevators from the database")
def get_resting_elevators(db: Session = Depends(get_db)):
    """
    Retrieves a list of all resting elevators from the database.
    A resting elevator, is an elevator that is in idle at a floor (meaning it dosen't have a recorded departure_time)
    There coould be added a bussiness rule:
        If an elevator arrives at a floor and stays there for more than 5 minutes, that can be calculate from the difference between arrival_time and current time, then the elevator is considered resting.
    Args:
        db (Session): The database session dependency.
    Returns:
        List[Movement]: A list of all resting elevator records.
    """
    return db.query(Movement).where(Movement.departure_time == None).all()

@app.get("/ml_data/", description="Get data for AI training", summary="Extract data for AI training")
def get_ml_data(db: Session = Depends(get_db)):
    """
    Extracts data for AI training.
        Args:
            db (Session): The database session dependency.
        Returns:
            dict: A dictionary containing formatted demand data.    
    """
    # Get demand data (requested floor, destination floor, number of calls)
    # query to return how many times an elevator has been called to a floor
    demand_data = db.query(
        Movement.start_floor,
        Movement.end_floor,
        Movement.arrival_time,
        Movement.departure_time,
        #func.datediff(Movement.departure_time, Movement.arrival_time),
        func.count(Movement.elevator_id),
        Movement.elevator_id,
    ).group_by(
        Movement.start_floor, Movement.end_floor
    ).where(Movement.departure_time != None).all()

    # Convert tuples to dictionaries
    formatted_demand_data = [
        {"requested_floor": d[0], "destination_floor": d[1], "count": d[4]}
        for d in demand_data
    ]
    elapsed_data = [
        {"start_floor": d[0], "end_floor": d[1], "elevator_id": d[5], "elapsed_time (secs)": (d[3]-d[2])}
        for d in demand_data
    ]

    return {"training_data": formatted_demand_data, "elapsed_data": elapsed_data} #, "resting_data": formatted_resting_data}
