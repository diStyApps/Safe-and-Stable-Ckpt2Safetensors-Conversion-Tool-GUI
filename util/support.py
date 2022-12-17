import webbrowser
import PySimpleGUI as sg
import util.colors as color
import util.icons as ic
PATREON_BTN_KEY = '-patreon_btn-'
BUY_ME_A_COFFEE_BTN_KEY = '-buy_me_a_coffee_btn-'
GITHUB_BTN_KEY = '-github_btn-'

def buttons_layout():
    layout = sg.Frame('',[
            [
                sg.Button(image_data=ic.patreon,key=PATREON_BTN_KEY,button_color=(color.GRAY_9900)),
                sg.Button(image_data=ic.buymeacoffee,key=BUY_ME_A_COFFEE_BTN_KEY,button_color=(color.GRAY_9900)),
                sg.Button(image_data=ic.github,key=GITHUB_BTN_KEY,button_color=(color.GRAY_9900))
            ],
        ],expand_x=True,relief=sg.RELIEF_SOLID,border_width=1,background_color=color.GRAY_9900,element_justification="r")
    return layout

def buttons(event):
    if event == PATREON_BTN_KEY:
        webbrowser.open("https://www.patreon.com/distyx")      
    if event == BUY_ME_A_COFFEE_BTN_KEY:
        webbrowser.open("https://www.buymeacoffee.com/disty")  
    if event == GITHUB_BTN_KEY:
        webbrowser.open("https://github.com/diStyApps/Safe-and-Stable-Ckpt2Safetensors-Conversion-Tool-GUI")  