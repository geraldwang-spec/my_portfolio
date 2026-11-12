from modules.services import Services


class ProductionController:
    def __init__(self, user_id: int, services: Services) -> None:
        self._user_id = user_id
        self._services = services
