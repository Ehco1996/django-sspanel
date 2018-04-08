import os
from configs.default import *

DATABASES['default']['PASSWORD'] = os.getenv('MYSQL_PASS')