# users/skills_config.py

"""
Statyczna konfiguracja dostępnych umiejętności w grze.
Możesz ją bezpiecznie rozbudowywać z czasem.
"""

AVAILABLE_SKILLS = {
    "botany": {
        "name": "Botanika",
        "max_level": 5,
        "cost_per_level": 1,
        "description": "Zwiększa szansę na znalezienie rzadkich roślin."
    },
    "alchemy": {
        "name": "Alchemia",
        "max_level": 3,
        "cost_per_level": 2,
        "description": "Pozwala na tworzenie zaawansowanych mikstur."
    },
    "tracking": {
        "name": "Tropienie",
        "max_level": 5,
        "cost_per_level": 1,
        "description": "Ułatwia odnajdywanie ukrytych celów na mapie."
    }
}