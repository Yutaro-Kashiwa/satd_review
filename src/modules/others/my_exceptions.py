class KnowUnknownJsonError(Exception):
    pass

class QueryFileNotFoundError(FileNotFoundError):
    pass

class DetailFileNotFoundError(FileNotFoundError):
    pass

class DiffFileNotFoundError(FileNotFoundError):
    pass

class DiffLineFileNotFoundError(FileNotFoundError):
    pass

