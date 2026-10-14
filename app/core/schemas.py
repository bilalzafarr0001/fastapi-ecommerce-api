"""
Base classes for all Pydantic schemas (DTOs).

- RequestSchema  -> data coming IN  (request bodies)
- ResponseSchema -> data going OUT  (responses built from database objects)
"""
from pydantic import BaseModel, ConfigDict


class RequestSchema(BaseModel):
    # Unknown fields are rejected with a 422 error. This protects us from
    # "mass assignment", e.g. a customer sending {"role": "admin"} on register.
    model_config = ConfigDict(extra="forbid")


class ResponseSchema(BaseModel):
    # Lets Pydantic read data from object attributes (user.email) and not only
    # from dicts (user["email"]), so routes can return SQLAlchemy objects directly.
    model_config = ConfigDict(from_attributes=True)
