from resource_management import *
from resource_management.libraries.script.script import Script
from resource_management.libraries.functions.default import default

config = Script.get_config()
port=default('configurations/redis/port', '7000')
db_path=default('configurations/redis/db_path', '/data/redis')