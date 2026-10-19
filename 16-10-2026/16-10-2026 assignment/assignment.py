import json

from pydantic import BaseModel, ValidationError, Field
import logging
from typing import Literal


# Configure logging
logging.basicConfig(
    filename='registrations.log',
    filemode='a',
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)


class Registration(BaseModel):
    registration_id: str
    name: str
    email: str
    age: int = Field(gt=18)
    ticket_type: Literal["Standard", "Premium", "VIP"] = "Standard"
    amount: float = Field(gt=0)

try:
    with open('registrations.json', 'r') as f:
        try:
            data = json.load(f)
        except FileNotFoundError:
            logging.error("Invalid registrations.json file")
except FileNotFoundError:
    data = {}
    logging.info("registrations.json not found")

valid_registrations = []

for index, row in enumerate(data):
    try:
        reg = Registration(**row)
        valid_registrations.append(reg)
        logging.info(f"Registration {reg.registration_id} validated successfully")
    except ValidationError as e:
        print(e)
        logging.error(f"Validation failed for registration id:  {row["registration_id"]}")
    finally:
        if row["ticket_type"] == "VIP":
            logging.warning("Ticket type is VIP")

print(valid_registrations)

reg_dict = valid_registrations[0].model_dump()
print(reg_dict)

reg_json = valid_registrations[1].model_dump_json(indent=4)
print(reg_json)

json_to_save = [reg_dict, reg_json]

with open('valid_registrations.json', 'w') as f:
    json.dump(json_to_save, f, indent=4)
    logging.info("json saved")

print("Total records: ", len(data))
print("Valid records: ", len(valid_registrations))
print("Invalid records: ", len(data) - len(valid_registrations))
