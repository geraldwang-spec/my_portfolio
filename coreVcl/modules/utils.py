
class UtilsTools:
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def try_parse_int(val:str)->tuple[bool, int]:
        try:
            return True, int(val)
        except(ValueError, TypeError):
            return False, 0


