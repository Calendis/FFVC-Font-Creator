import sys
from os import path
from PyQt5 import QtCore, QtGui, QtWidgets
from ui_main import *

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QMainWindow()
ui = Ui_FVCFontCreator()
ui.setupUi(window)


'''
    Sorry for the liberal use of globals, maybe I'll clean it up at some point.
    Probably not, as the tool does what I needed it to do...
    
    Fun Virtual Computer Font Creator
    Bert Myroon
    19 Nov., 2020
    Writes fonts to the BGT format. Specification can be found in the FVC repo (github.com/Calendis/FFVC)
'''
# Globals
current_file = None
filepath = None
current_glyph = 0
button_map = [
        [ui.px1, ui.px2, ui.px3, ui.px4, ui.px5, ui.px6, ui.px7, ui.px8],
        [ui.px9, ui.px10, ui.px11, ui.px12, ui.px13, ui.px14, ui.px15, ui.px16],
        [ui.px17, ui.px18, ui.px19, ui.px20, ui.px21, ui.px22, ui.px23, ui.px24],
        [ui.px25, ui.px26, ui.px27, ui.px28, ui.px29, ui.px30, ui.px31, ui.px32],
        [ui.px33, ui.px34, ui.px35, ui.px36, ui.px37, ui.px38, ui.px39, ui.px40],
        [ui.px41, ui.px42, ui.px43, ui.px44, ui.px45, ui.px46, ui.px47, ui.px48],
        [ui.px49, ui.px50, ui.px51, ui.px52, ui.px53, ui.px54, ui.px55, ui.px56],
        [ui.px57, ui.px58, ui.px59, ui.px60, ui.px61, ui.px62, ui.px63, ui.px64]
    ]
fontmap = None
glyphs = 0

# Define application functionality
def open_file_path():
    global filepath
    
    # Defines some strings based on the file we opened
    opened_file_path = QtWidgets.QFileDialog.getOpenFileName()[0]
    opened_file_path_rel = opened_file_path.split("/")[-1] # Relative version of the file path
    filepath = opened_file_path
        
    # Make sure the file exists
    if not path.isfile(opened_file_path):
        print("No such file")
        return
    
    global current_file
    current_file = open(opened_file_path, 'rb').read()
    header = current_file[:4]
    
    # Make sure header indictes the file is a BGT font
    # In ASCII, the BGT header reads "5:G"
    if header[:3] != b"5:G":
        print("Invalid header", header[:3])
        return
    
    # Set the info about the supported glyphs
    global glyphs
    glyphs = header[-1]
    ui.glyph_count_label.setText(str(glyphs))
    
    # Refresh the current glyph
    assemble_fontmap()
    global current_glyph
    get_glyph_bytes(current_glyph)
    
    enable_buttons()
    
    
def get_glyph_bytes(glyph):
    # Define the byte range for the current glyph within the current file
    header_length = 4
    glyph_length = 9
    start_byte = header_length + glyph_length*glyph
    end_byte = start_byte + glyph_length
    
    global fontmap
    try:
        glyph_data = fontmap[glyph]
        
    except KeyError:
        glyph_data = fontmap[0]
    
    # Assemble bitstrings
    glyph_bitstrings = []
    for byte in glyph_data:
        bitstring = format(byte, 'b')
        prefix = '0'*(8 - len(bitstring))
        bitstring = prefix + bitstring
        
        glyph_bitstrings.append(bitstring)
    
    # Set the button press states for display            
    for i in range(8):
        for j in range(8):
            button_map[i][j].setChecked(int(glyph_bitstrings[i][j]))
            
    global current_glyph
    current_glyph = glyph
    ui.glyph_id_label.setText(str(glyph))
            
    return glyph_data

def set_glyph_bytes():
    global button_map, fontmap, current_glyph, glyphs, current_file
    # Assemble bitstrings from buttons
    button_bitstrings = []
    for i in range(8):
        button_bitstring = ''
        for j in range(8):
            button_bitstring += str(int(button_map[i][j].isChecked()))
        
        button_bitstrings.append(button_bitstring)
    
    # Assemble bytes from bitstrings
    button_bytes = bytearray(8)
    for i in range(8):
        button_num = int(button_bitstrings[i], 2)
        button_bytes[i] = button_num
    
    # Make the file in memory mutable
    current_file = bytearray(current_file)
    
    # Adding a new glyph
    if current_glyph not in fontmap.keys():
        glyphs += 1
        new_glyph = bytearray(9)
        new_glyph[0] = current_glyph
        new_glyph[1:] = button_bytes
        new_glyph = bytes(new_glyph)
        
        current_file += new_glyph
        
        # Update the number of glyphs data
        ui.glyph_count_label.setText(str(glyphs))
    
    # Modifying an old glyph
    else:
        new_glyph = bytearray(9)
        new_glyph[0] = current_glyph
        new_glyph[1:] = button_bytes
        new_glyph = bytes(new_glyph)
        
        #font_keys = [current_file[i+4] for i in range(0, len(current_file)-4, 9)]
        #font_glyphs = [current_file[i+1 : i+9] for i in range(4, len(current_file)-1, 9)]
        
        # First iterate through all the glyphs, since they aren't necessarily ordered
        for i in range(4, len(current_file)-4, 9):
            key = current_file[i]
            
            # If the keys match, overwrite the glyph in memory
            if key == current_glyph:
                current_file[i:i+9] = new_glyph
    
    # Update the glyph count
    current_file[3] = glyphs
    
    # Make the file in memory immutable again
    current_file = bytes(current_file)
    
    # Refresh
    fontmap[current_glyph] = bytes(button_bytes)
    get_glyph_bytes(current_glyph)

def cycle_glyph(amount):
    global current_glyph
    current_glyph += amount
    current_glyph = current_glyph % 256
    
    get_glyph_bytes(current_glyph)

def next_glyph():
    cycle_glyph(1)
    
def prev_glyph():
    cycle_glyph(-1)

def reload_glyph():
    cycle_glyph(0)
    
def assemble_fontmap():
    # Assemble the key-glyph font mapping
    global fontmap, current_file
    
    font_keys = [current_file[i+4] for i in range(0, len(current_file)-4, 9)]
    font_glyphs = [current_file[i+1 : i+9] for i in range(4, len(current_file)-1, 9)]
    
    fontmap = {}
    for i in range(len(font_keys)):
        k = font_keys[i]
        fontmap[k] = font_glyphs[i]
        
    # Ensure the fontmap always contains a null glyph for fallback
    fontmap[0x00] = bytes(8)
    
def new_font():
    global current_file, current_glyph, filepath, glyphs
    filepath = None
    current_glyph = 0
    glyphs = 0
    ui.glyph_count_label.setText(str(glyphs))
    current_file = b"5:G" + bytes(10)  # 1 byte for the glyph count, and for the 0x00 glyph
    assemble_fontmap()
    get_glyph_bytes(current_glyph)
    enable_buttons()
    

def save_font(save_as=False):
    global filepath, current_file
    
    if filepath is None or save_as == True:
        save_file_path = QtWidgets.QFileDialog.getSaveFileName()[0]
        filepath = save_file_path
    
    new_file = open(filepath, 'w+b')
    new_file.write(current_file)
    new_file.close()

def save_font_as():
    save_font(True)
    
def enable_buttons():
    ui.next_button.setEnabled(True)
    ui.prev_button.setEnabled(True)
    ui.reload_button.setEnabled(True)
    ui.actionSave.setEnabled(True)
    ui.actionSave_As.setEnabled(True)
    ui.write_button.setEnabled(True)
    ui.save_button.setEnabled(True)
    

# Link buttons to custom functions
ui.load_button.clicked.connect(open_file_path)
ui.actionOpen.triggered.connect(open_file_path)
ui.next_button.clicked.connect(next_glyph)
ui.prev_button.clicked.connect(prev_glyph)
ui.reload_button.clicked.connect(reload_glyph)
ui.save_button.clicked.connect(set_glyph_bytes)
ui.actionNew.triggered.connect(new_font)
ui.actionSave.triggered.connect(save_font)
ui.write_button.clicked.connect(save_font)
ui.actionSave_As.triggered.connect(save_font_as)

window.show()
sys.exit(app.exec())
