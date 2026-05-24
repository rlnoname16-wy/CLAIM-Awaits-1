import json
import os


CLASS_BASE_STATS = {
    "Warrior": {"health": 120, "attack": 12, "defense": 8},
    "Mage": {"health": 80, "attack": 18, "defense": 3},
    "Rogue": {"health": 90, "attack": 14, "defense": 5},
    "Paladin": {"health": 130, "attack": 10, "defense": 10},
    "Berserker": {"health": 110, "attack": 20, "defense": 2},
    "Ranger": {"health": 95, "attack": 15, "defense": 6},
}


def new_player(name: str, player_class: str) -> dict:
    stats = CLASS_BASE_STATS.get(player_class, CLASS_BASE_STATS["Warrior"])
    return {
        "name": name or "Claimant",
        "class": player_class if player_class in CLASS_BASE_STATS else "Warrior",
        "level": 1,
        "exp": 0,
        "health": stats["health"],
        "max_health": stats["health"],
        "attack": stats["attack"],
        "defense": stats["defense"],
        "gold": 50,
        "inventory": [],
        "location": "Grasslands",
        "skill_points": 0,
        # Track which biome bosses are defeated
        "bosses_defeated": [],
    }


def load_game(save_path: str) -> dict | None:
    if not os.path.exists(save_path):
        return None
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            player = json.load(f)
    except Exception:
        return None

    # Ensure fields exist
    player.setdefault("name", "Claimant")
    player.setdefault("class", "Warrior")
    player.setdefault("level", 1)
    player.setdefault("exp", 0)
    player.setdefault("health", 1)
    player.setdefault("max_health", max(1, int(player.get("max_health", 1))))
    player.setdefault("attack", 1)
    player.setdefault("defense", 0)
    player.setdefault("gold", 0)
    player.setdefault("inventory", [])
    player.setdefault("location", "Grasslands")
    player.setdefault("skill_points", 0)
    player.setdefault("bosses_defeated", [])
    # Keep HP sane
    player["health"] = max(0, min(player["health"], player["max_health"]))
    return player


def save_game(player: dict, save_path: str) -> None:
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(player, f, indent=2)

