from generalize import main as generalize
from specification import main as specification
from specification import final
from idk import *

generalize.__name__ = 'generalize'
specification.__name__ = 'specification'

if __name__ == "__main__":
    easy_run(generalize,specification,final)