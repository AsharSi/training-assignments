from pydantic import BaseModel, ValidationError, Field
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)

# Pydantic model
class Employee(BaseModel):
    name: str
    age: int = Field(gt=18)
    email: str
    salary: float = Field(gt=0)

data = {
    "name": "Naveen",
    "age": 18,
    "email": "naveen18@gmail.com",
    "salary": 45000,
}