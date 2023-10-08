import os

# only allow set DEBUG in env
if os.getenv("DEBUG", "") != "True":
    DEBUG = False
