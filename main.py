from __future__ import annotations

import os
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from biomes import biomes
from guardians import claimguardians
from player_core import CLASS_BASE_STATS, load_game, new_player, save_game


def get_save_path() -> str:
    # On Android: App.user_data_dir is the right place (no permissions needed).
    app = App.get_running_app()
    if app:
        return os.path.join(app.user_data_dir, "claim_save.json")
    # Desktop/dev fallback
    return os.path.join(os.path.dirname(__file__), "claim_save.json")


class GameRoot(BoxLayout):
    status_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8), padding=dp(10), **kwargs)
        Window.clearcolor = (0.12, 0.12, 0.12, 1)

        # --- STATE ---
        self.player: dict | None = None
        self.current_enemy: dict | None = None
        self.cooldowns = {"ability": 0}
        self.status_effects = {"burn": 0}

        self.shop_items = {
            "Small Potion": {"price": 20, "heal": 30},
            "Big Potion": {"price": 50, "heal": 70},
        }

        # --- UI: STATUS ---
        self.status = Label(text="", size_hint_y=None, height=dp(42), color=(1, 1, 1, 1))
        self.add_widget(self.status)

        # --- UI: LOG ---
        self.log_label = Label(
            text="",
            markup=True,
            size_hint_y=None,
            valign="top",
            halign="left",
            color=(1, 1, 1, 1),
        )
        self.log_label.bind(
            width=lambda *_: setattr(self.log_label, "text_size", (self.log_label.width, None))
        )

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.log_label)
        self.add_widget(scroll)

        # --- UI: BUTTONS (touch-friendly) ---
        btn_row1 = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        btn_row2 = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        btn_row3 = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))

        def mkbtn(text, fn):
            return Button(text=text, on_release=lambda *_: fn(), font_size="18sp")

        btn_row1.add_widget(mkbtn("Explore", self.explore))
        btn_row1.add_widget(mkbtn("Boss", self.boss_fight))
        btn_row1.add_widget(mkbtn("Move", self.move))

        btn_row2.add_widget(mkbtn("Attack", self.attack))
        btn_row2.add_widget(mkbtn("Ability", self.ability))
        btn_row2.add_widget(mkbtn("Rest", self.rest))

        btn_row3.add_widget(mkbtn("Inventory", self.inventory))
        btn_row3.add_widget(mkbtn("Shop", self.shop))
        btn_row3.add_widget(mkbtn("Skills", self.skill_tree))

        self.add_widget(btn_row1)
        self.add_widget(btn_row2)
        self.add_widget(btn_row3)

        # Load/create player after UI exists (so Popups work)
        Clock.schedule_once(lambda *_: self.bootstrap(), 0)

    # ----------------------------
    # Boot / Save
    # ----------------------------
    def bootstrap(self):
        self.write("[b]🌌 CLAIM: Awaits 🌌[/b]\n")
        save_path = get_save_path()
        player = load_game(save_path)
        if player:
            self.ask_load_or_new(player)
        else:
            self.open_create_player()

    def ask_load_or_new(self, loaded_player: dict):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=f"Load saved game for {loaded_player.get('name','Claimant')}?"))
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

        pop = Popup(title="Load Game", content=content, size_hint=(0.9, 0.35))

        def do_load():
            pop.dismiss()
            self.player = loaded_player
            self.player.setdefault("bosses_defeated", [])
            self.write(f"📂 Loaded: {self.player['name']} the {self.player['class']}\n")
            self.update_status()

        def do_new():
            pop.dismiss()
            self.open_create_player()

        btns.add_widget(Button(text="Load", on_release=lambda *_: do_load()))
        btns.add_widget(Button(text="New", on_release=lambda *_: do_new()))
        content.add_widget(btns)
        pop.open()

    def save(self):
        if not self.player:
            return
        save_game(self.player, get_save_path())
        self.write("💾 Game Saved!\n")

    # ----------------------------
    # UI helpers
    # ----------------------------
    def write(self, text: str):
        # append and keep log size reasonable
        current = self.log_label.text or ""
        new_text = current + text
        if len(new_text) > 12000:
            new_text = new_text[-12000:]
        self.log_label.text = new_text

    def update_status(self):
        if not self.player:
            self.status.text = ""
            return
        p = self.player
        self.status.text = (
            f"{p['name']} | {p['class']} | HP {p['health']}/{p['max_health']} | "
            f"LV {p['level']} | Gold {p['gold']} | SP {p['skill_points']} | {p['location']}"
        )

    # ----------------------------
    # Player creation (Kivy)
    # ----------------------------
    def open_create_player(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        name_input = TextInput(hint_text="Enter your name", multiline=False, size_hint_y=None, height=dp(44))
        content.add_widget(name_input)

        classes = list(CLASS_BASE_STATS.keys())
        class_spinner = Spinner(text="Choose class", values=classes, size_hint_y=None, height=dp(44))
        content.add_widget(class_spinner)

        info = Label(
            text="Tip: Mage can burn enemies. Paladin can heal.\nAbilities have cooldown.",
            size_hint_y=None,
            height=dp(48),
        )
        content.add_widget(info)

        btn = Button(text="Start", size_hint_y=None, height=dp(48))
        content.add_widget(btn)

        pop = Popup(title="Create Player", content=content, size_hint=(0.92, 0.5))

        def start(*_):
            name = (name_input.text or "").strip() or "Claimant"
            chosen = class_spinner.text if class_spinner.text in classes else "Warrior"
            self.player = new_player(name=name, player_class=chosen)
            self.write(f"🎭 You are now a {chosen}!\n")
            pop.dismiss()
            self.update_status()
            self.save()

        btn.bind(on_release=start)
        pop.open()

    # ----------------------------
    # Gameplay
    # ----------------------------
    def explore(self):
        if not self.player:
            return
        biome = self.player["location"]
        enemy = random.choice(biomes[biome]["monsters"])
        self.start_combat(enemy)

    def boss_fight(self):
        if not self.player:
            return
        biome = self.player["location"]

        if biome in self.player.get("bosses_defeated", []):
            self.write("Boss already defeated.\n")
            return

        boss = claimguardians.get(biome)
        if not boss:
            self.write("No boss here.\n")
            return

        self.write(f"👑 BOSS: {boss['name']}\n")
        self.start_combat(boss)

    def start_combat(self, enemy: dict):
        self.current_enemy = enemy.copy()
        self.current_enemy["max_health"] = enemy["health"]
        self.cooldowns["ability"] = 0
        self.status_effects["burn"] = 0
        self.write(f"\n⚔️ {enemy['name']} appeared! (HP {enemy['health']}, ATK {enemy['attack']})\n")

    def attack(self):
        if not self.player or not self.current_enemy:
            return

        crit = random.randint(1, 100) <= 15
        dmg = self.player["attack"] * (2 if crit else 1)
        self.current_enemy["health"] -= dmg
        self.write(f"{'💥 CRIT! ' if crit else ''}You deal {dmg}\n")

        if self.current_enemy["health"] <= 0:
            self.win()
            return

        self.enemy_turn()

    def ability(self):
        if not self.player or not self.current_enemy:
            return

        if self.cooldowns["ability"] > 0:
            self.write(f"⏳ Cooldown: {self.cooldowns['ability']}\n")
            return

        cls = self.player["class"]
        dmg = 0

        if cls == "Mage":
            dmg = int(self.player["attack"] * 2)
            self.status_effects["burn"] = 3
            self.write("🔥 Fireball! Burn applied!\n")
        elif cls == "Paladin":
            heal = 40
            self.player["health"] = min(self.player["max_health"], self.player["health"] + heal)
            self.write(f"✨ Heal +{heal}\n")
            self.update_status()
            self.save()
            return
        else:
            dmg = int(self.player["attack"] * 1.5)
            self.write("⚡ Ability strike!\n")

        self.current_enemy["health"] -= dmg
        self.cooldowns["ability"] = 2

        if self.current_enemy["health"] <= 0:
            self.win()
            return

        self.enemy_turn()

    def enemy_turn(self):
        if not self.player or not self.current_enemy:
            return

        # Burn tick
        if self.status_effects["burn"] > 0:
            self.current_enemy["health"] -= 5
            self.status_effects["burn"] -= 1
            self.write("🔥 Burn damage 5\n")
            if self.current_enemy["health"] <= 0:
                self.win()
                return

        # Special ability chance
        if "ability" in self.current_enemy and random.randint(1, 100) <= 30:
            ability = self.current_enemy["ability"]
            if ability == "Smash":
                self.player["health"] -= self.current_enemy["attack"] * 2
                self.write("💥 Smash!\n")
            elif ability == "Fire Breath":
                self.player["health"] -= self.current_enemy["attack"] + 10
                self.write("🔥 Fire Breath!\n")
            else:
                self.player["health"] -= self.current_enemy["attack"]
                self.write(f"{self.current_enemy['name']} hits\n")
        else:
            dodge = 10 + self.player["level"] * 2
            if random.randint(1, 100) <= dodge:
                self.write("💨 Dodged!\n")
            else:
                self.player["health"] -= self.current_enemy["attack"]
                self.write(f"{self.current_enemy['name']} hits {self.current_enemy['attack']}\n")

        self.cooldowns["ability"] = max(0, self.cooldowns["ability"] - 1)
        self.update_status()

        if self.player["health"] <= 0:
            self.write("\n[b]You died![/b]\n")
            self.game_over()

    def win(self):
        if not self.player or not self.current_enemy:
            return

        enemy = self.current_enemy
        self.write(f"✅ Defeated {enemy['name']}\n")

        self.player["exp"] += enemy.get("exp", 0)
        self.player["gold"] += enemy.get("gold", 0)

        if self.player["exp"] >= 100:
            self.player["exp"] = 0
            self.player["level"] += 1
            self.player["skill_points"] += 2
            self.write("⭐ Level Up! +2 Skill Points\n")

        # Boss defeat check + loot
        for biome, boss in claimguardians.items():
            if boss["name"] == enemy["name"]:
                defeated = self.player.setdefault("bosses_defeated", [])
                if biome not in defeated:
                    defeated.append(biome)
                    self.write(f"🏆 Boss of {biome} defeated!\n")
                    for item in boss.get("loot", []):
                        self.player["inventory"].append(item)
                        self.write(f"🎁 Loot: {item}\n")

        self.current_enemy = None
        self.update_status()
        self.save()

    def game_over(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text="You died! Start a new run or load your save."))

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        content.add_widget(btns)

        pop = Popup(title="Game Over", content=content, size_hint=(0.9, 0.35))

        def new_run():
            pop.dismiss()
            self.open_create_player()

        def close():
            pop.dismiss()
            App.get_running_app().stop()

        btns.add_widget(Button(text="New", on_release=lambda *_: new_run()))
        btns.add_widget(Button(text="Quit", on_release=lambda *_: close()))
        pop.open()

    def rest(self):
        if not self.player:
            return
        self.player["health"] = min(self.player["max_health"], self.player["health"] + 25)
        self.write("Rested +25 HP\n")
        self.update_status()
        self.save()

    # ----------------------------
    # Inventory / Shop / Skills / Move
    # ----------------------------
    def inventory(self):
        if not self.player:
            return

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        inv = list(self.player["inventory"])

        if not inv:
            content.add_widget(Label(text="(Inventory empty)"))
            pop = Popup(title="Inventory", content=content, size_hint=(0.9, 0.6))
            pop.open()
            return

        def use(item, pop):
            if "Potion" in item:
                self.player["inventory"].remove(item)
                self.player["health"] = min(self.player["max_health"], self.player["health"] + 30)
                self.write(f"Used {item} (+30 HP)\n")
                self.update_status()
                self.save()
            else:
                self.write(f"Can't use {item} right now.\n")
            pop.dismiss()

        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        box.bind(minimum_height=box.setter("height"))
        for item in inv:
            b = Button(text=item, size_hint_y=None, height=dp(48))
            box.add_widget(b)
        scroll.add_widget(box)
        content.add_widget(scroll)

        pop = Popup(title="Inventory (tap item)", content=content, size_hint=(0.9, 0.75))
        # bind after pop exists
        for btn, item in zip(box.children[::-1], inv):
            btn.bind(on_release=lambda _, it=item: use(it, pop))
        pop.open()

    def shop(self):
        if not self.player:
            return

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))

        pop = Popup(title="Shop", content=content, size_hint=(0.9, 0.5))

        def buy(item):
            data = self.shop_items[item]
            if self.player["gold"] >= data["price"]:
                self.player["gold"] -= data["price"]
                self.player["inventory"].append(item)
                self.write(f"🛒 Bought {item}\n")
                self.update_status()
                self.save()
            else:
                self.write("❌ Not enough gold!\n")
            pop.dismiss()

        for item, data in self.shop_items.items():
            btn = Button(text=f"{item} - {data['price']}G", size_hint_y=None, height=dp(52))
            btn.bind(on_release=lambda _, it=item: buy(it))
            content.add_widget(btn)
        pop.open()

    def skill_tree(self):
        if not self.player:
            return

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        sp_label = Label(text=f"Skill Points: {self.player['skill_points']}")
        content.add_widget(sp_label)

        def refresh():
            sp_label.text = f"Skill Points: {self.player['skill_points']}"
            self.update_status()

        def upgrade(stat, pop):
            if self.player["skill_points"] <= 0:
                self.write("No skill points!\n")
                pop.dismiss()
                return

            if stat == "attack":
                self.player["attack"] += 2
            elif stat == "defense":
                self.player["defense"] += 2
            elif stat == "health":
                self.player["max_health"] += 20
                self.player["health"] += 20

            self.player["skill_points"] -= 1
            self.write(f"⬆️ Upgraded {stat}\n")
            self.save()
            refresh()
            pop.dismiss()

        pop = Popup(title="Skill Tree", content=content, size_hint=(0.9, 0.5))
        for label, stat in (("Attack +2", "attack"), ("Defense +2", "defense"), ("Max HP +20", "health")):
            btn = Button(text=label, size_hint_y=None, height=dp(52))
            btn.bind(on_release=lambda _, s=stat: upgrade(s, pop))
            content.add_widget(btn)
        pop.open()

    def move(self):
        if not self.player:
            return

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        box.bind(minimum_height=box.setter("height"))

        biome_names = list(biomes.keys())

        pop = Popup(title="Move (choose biome)", content=content, size_hint=(0.9, 0.8))

        def select(biome, pop):
            self.player["location"] = biome
            self.write(f"Moved to {biome}\n")
            self.update_status()
            self.save()
            pop.dismiss()

        for biome in biome_names:
            btn = Button(text=biome, size_hint_y=None, height=dp(52))
            btn.bind(on_release=lambda _, b=biome: select(b, pop))
            box.add_widget(btn)

        scroll.add_widget(box)
        content.add_widget(scroll)
        pop.open()


class ClaimAwaitsApp(App):
    def build(self):
        return GameRoot()


if __name__ == "__main__":
    ClaimAwaitsApp().run()
