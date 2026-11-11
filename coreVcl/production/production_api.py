from flask import Blueprint
from production.product_controller import ProductionController

from modules.api_response import ApiResponse


def create_production_api(
    production: ProductionController, name: str = "production"
) -> Blueprint:
    production_bp = Blueprint(name, __name__, url_prefix=f"/{name}")

    @production_bp.route("/home", method=["GET", "POST"])
    def home():
        return ApiResponse(success=True, message="", data=None).to_response(), 200

    return production_bp
