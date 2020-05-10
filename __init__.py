#__init__.py
#Importing our script class
from .OhmOne import OhmOne

def create_instance(c_instance):
	return OhmOne(c_instance)