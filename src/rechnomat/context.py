from rechnomat.model import Context

def create(debug: bool) -> Context:
    return Context(
        debug=debug,
    )
