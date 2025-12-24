

def build_filters(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}