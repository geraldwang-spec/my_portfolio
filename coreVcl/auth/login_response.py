from typing import Any
from flask import Response, jsonify
from pydantic import BaseModel

class loginResponse(BaseModel):
    success:bool
    message:str
    data:Any

    def to_response(self)-> Response:
        return jsonify(self.model_dump())
