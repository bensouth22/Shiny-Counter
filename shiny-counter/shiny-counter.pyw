from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import QtCore
import requests
import pathlib

# utility functions

# load in dex from txt as a dict
# TODO: make sure dex is up to date
def load_pokedex(filename="pokedex.txt"):
    pokedex = {}
    with open(filename, "r") as f:
        for line in f:
            val, key = line.strip().split(" ", 1)
            pokedex[key.lower()] = val
    return pokedex

# calculate odds that a shiny would have been found after a given amount of encounters i.e.:
# x = 1 - (1 - P) ** n
# where P is the odds for a single encounter and n is the total number of encounters
def calc_shiny_probability(encounters, odds = False):
    if odds:
        return round(100 * (1 - (1 - 1 / 4096) ** encounters), 3)
    else:
        return round(100 * (1 - (1 - 1 / 8192) ** encounters), 3)

# fetch sprite png from showdown
# sprites are 96 x 96 by default
# defaults to gen 4 and 5 sprites 
# TODO: add option to select generation in preferences
def fetch_shiny_sprite(pokemon, pokedex):
    if pokemon not in pokedex:
        return "unknown.png"

    trans = str.maketrans({" ":"", "'":"", ".":"",":":""})
    shiny_filename = pokemon.translate(trans) + ".png"
    path = pathlib.Path(shiny_filename)

    if not path.exists():
        poke_id = int(pokedex[pokemon])
        if poke_id < 494:
            gen_folder = "gen4-shiny/"
        elif poke_id < 650:
            gen_folder = "gen5-shiny/"
        else:
            gen_folder = "dex-shiny/"
        url = f"https://play.pokemonshowdown.com/sprites/{gen_folder}{shiny_filename}"
        response = requests.get(url)
        with open(shiny_filename, "wb") as f:
            f.write(response.content)

    return shiny_filename

# load user preferences from txt
def load_preferences(filename="preferences.txt"):
    try:
        with open(filename, "r") as f:
            lines = [line.strip() for line in f.readlines()]
            return lines if lines else ["0", "unknown", "False", "False", "False"]
    except FileNotFoundError:
        return ["0", "unknown", "False", "False", "False"]

# save user preferences in a txt
def save_preferences(values, filename="preferences.txt"):
    with open(filename, "w") as f:
        for value in values:
            f.write(str(value) + "\n")



app = QApplication([])

# widgets
count_label = QLabel("0")
bi_prob = QLabel("0")
encounters_box = QLineEdit()
pokemon_box = QLineEdit()
odds_box = QCheckBox("Improved shiny odds (Gen 6+)")
top_box = QCheckBox("Always on top")
title_box = QCheckBox("Remove title bar")
image_label = QLabel()

# grab dex and preferences
pokedex = load_pokedex()
preferences = load_preferences()

encounters = int(preferences[0]) if preferences[0].isdigit() else 0
pokemon = preferences[1].lower()
shiny_odds = preferences[2] == "True"
always_on_top = preferences[3] == "True"
no_title = preferences[4] == "True"

# initial values
count_label.setText(str(encounters))
bi_prob.setText(f"{calc_shiny_probability(encounters)}%")
pokemon_box.setText(preferences[1])
odds_box.setChecked(shiny_odds)
top_box.setChecked(always_on_top)
title_box.setChecked(no_title)

# load sprite
sprite_file = fetch_shiny_sprite(pokemon, pokedex)
pixmap = QPixmap(sprite_file).scaled(192, 192, QtCore.Qt.KeepAspectRatio)
image_label.setPixmap(pixmap)

# icons
shine_pixmap = QPixmap("shine.png")
gear_icon = QPixmap("settings.png").scaled(96, 96, QtCore.Qt.KeepAspectRatio)

# settings window
settings = QWidget()
settings.setWindowTitle("Settings")
settings.setWindowIcon(QIcon(gear_icon))
settings_layout = QFormLayout()
settings_layout.addRow("Encounters:", encounters_box)
settings_layout.addRow("Pokemon:", pokemon_box)
settings_layout.addRow(QLabel("Please specify regional forms e.g. 'Darumaka-Galar'"))
settings_layout.addRow(odds_box)
settings_layout.addRow(top_box)
settings_layout.addRow(title_box)

# callbacks

# update probability calc
def update_ui():
    n = int(count_label.text())
    bi_prob.setText(f"{calc_shiny_probability(n, odds_box.isChecked())}%")

# update sprite to mon specified in preferences
def update_sprite():
    global pokemon
    pokemon = pokemon_box.text().lower()
    sprite_file = fetch_shiny_sprite(pokemon, pokedex)
    pixmap = QPixmap(sprite_file).scaled(192, 192, QtCore.Qt.KeepAspectRatio)
    image_label.setPixmap(pixmap)

# update window properties (i.e. frameless and always on top)
def apply_window_flags():
    flags = QtCore.Qt.Widget
    if top_box.isChecked():
        flags |= QtCore.Qt.WindowStaysOnTopHint
    if title_box.isChecked():
        flags |= QtCore.Qt.FramelessWindowHint
    window.setWindowFlags(flags)
    settings.setWindowFlags(flags)
    window.show()

# take user input in preferences and saves them
# calls save_preferences to write to preferences to txt
def on_save_clicked():
    values = [
        encounters_box.text(),
        pokemon_box.text(),
        str(odds_box.isChecked()),
        str(top_box.isChecked()),
        str(title_box.isChecked())
    ]
    save_preferences(values)
    count_label.setText(encounters_box.text())
    update_ui()
    update_sprite()
    apply_window_flags()
    settings.hide()

# show the settings menu
def on_settings_clicked():
    encounters_box.setText(count_label.text())
    settings.show()

# increase total encounters by 1
def increment_count():
    count = int(count_label.text()) + 1
    count_label.setText(str(count))
    update_ui()

# decrease total encounters by 1
def decrement_count():
    count = int(count_label.text())
    if count > 0:
        count_label.setText(str(count - 1))
        update_ui()

# save preferences on exit
def on_exit():
    preferences = load_preferences()
    preferences[0] = count_label.text()
    save_preferences(preferences)



# buttons
save_button = QPushButton("Save changes")
save_button.clicked.connect(on_save_clicked)
settings_layout.addRow(save_button)
settings.setLayout(settings_layout)

settings_button = QPushButton()
settings_button.setIcon(QIcon(gear_icon))
settings_button.clicked.connect(on_settings_clicked)

up_button = QPushButton("+ 1")
up_button.clicked.connect(increment_count)

down_button = QPushButton("- 1")
down_button.clicked.connect(decrement_count)



# window
layout = QHBoxLayout()
layout.addWidget(image_label)
layout.addWidget(count_label)
layout.addWidget(bi_prob)
layout.addWidget(up_button)
layout.addWidget(down_button)
layout.addWidget(settings_button)

window = QWidget()
window.setWindowTitle("Counter")
window.setWindowIcon(QIcon(shine_pixmap))
window.setFixedSize(500, 150)
window.setLayout(layout)
apply_window_flags()
window.show()

app.aboutToQuit.connect(on_exit)
app.exec_()