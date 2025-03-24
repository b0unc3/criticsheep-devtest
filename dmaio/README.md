# Solution for the devtest at CriticSheep
## Elevator Management System

###
The solution implements a database model using SQLAlchemy, I've also add some Pydantic schemas for request validation.
There are different endpoints implemented with FastAPI.
Some simple test is created using unittest.

## Run the project
### Install required packages
``pip install -r requirements.txt``

### Init DB
``sqlite3 elevator.db < database/db-schema.sql``

### Run the app
``uvicorn app.main:app``

### URL
``http://127.0.0.1:8000/docs``

### Endpoints
![alt text](image.png)