# REFACTOR: extract magic numbers and add docstrings
from core.types import User

    
def send_welcome(user):
    timeout = 30
    retries = 3
    body = "Hello " + user.name + ", welcome!"
    return {"to": user.email, "body": body, "timeout": timeout, "retries": retries}
