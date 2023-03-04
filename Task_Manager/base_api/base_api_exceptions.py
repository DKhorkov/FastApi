class InvalidTypeException(Exception):
    """Raises, when FastAPi Query value can not be transferred from string to necessary type"""

    def __init__(self, type_to_transfer):
        self.message = f'Query value can not be transferred to {type_to_transfer} type!'
        super().__init__(self.message)
