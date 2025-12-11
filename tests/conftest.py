import os
import sys

# Añadir la carpeta del proyecto al sys.path para que los imports relativos funcionen en tests
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

