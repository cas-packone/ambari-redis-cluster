from resource_management import *
from resource_management.libraries.script.script import Script

config = Script.get_config()
db_path=config['configurations']['redis']['db_path']
port=config['configurations']['redis']['port']