import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

# "Aujourd'hui" simulé : rend les tests déterministes
TODAY = date.fromisoformat(os.getenv("SIMULATED_TODAY", "2026-11-03"))

HUMAN_THRESHOLD = 100.0     # au-dessus : validation humaine obligatoire
MAX_ITERATIONS = 6          # garde-fou anti-boucle du superviseur
MAX_TOOL_STEPS = 5          # garde-fou anti-boucle dans un agent
