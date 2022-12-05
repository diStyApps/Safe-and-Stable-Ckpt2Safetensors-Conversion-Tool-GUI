import PySimpleGUI as sg
import util.icons as ic
import util.progress_bar_custom as cpbar
import os
import torch 
import webbrowser
from threading import Thread
from datetime import datetime as dt
from safetensors.torch import save_file
import hashlib
COLOR_DARK_GREEN = '#78BA04'
COLOR_DARK_BLUE = '#4974a5'
COLOR_RED_ORANGE = '#C13515'
COLOR_GRAY_9900 = '#0A0A0A'
COLOR_DARK_GRAY = '#1F1F1F'
COLOR_GREEN = '#43CD80'
COLOR_DARK_GREEN2 = '#78BA04'

HASH_START = 0x100000
HASH_LENGTH = 0x10000

_pytorch_file_extensions = {".ckpt"}

file_ext = {("Stable Diffusion", "*.ckpt")}

def main():
    ver = '0.0.2'
    sg.theme('Dark Gray 15')
    app_title = f"Safe & Stable - Ckpt2Safetensors Conversion Tool-GUI - Ver {ver}"
    pbar_progress_bar_key = 'progress_bar'
    input_directory_path_list = []
    idx=0
    start_time = dt.today().timestamp()

    #region layout
    def browse_layout(type_,visible_,disabled=False):        
        if type_ == 'file':
            browse_type = sg.FileBrowse(k=f'-{type_}_FileBrowse-',file_types=(file_ext),disabled=disabled,size=(10,2)) 
        if type_ == 'directory':
            browse_type = sg.FolderBrowse(k=f'-{type_}_FolderBrowse-',disabled=disabled,size=(10,2))

        layout = sg.Frame('',[
                                [
                                    sg.Input(key=f'-input_files_{type_}-',readonly=True,disabled_readonly_background_color=COLOR_DARK_GRAY,enable_events=True,expand_x=True,expand_y=True,font='Ariel 11',background_color=COLOR_DARK_GRAY),
                                    browse_type
                                ],
                            ],expand_x=True,k=f'-frame_{type_}-',visible=visible_,relief=sg.RELIEF_SOLID,border_width=1,background_color=COLOR_GRAY_9900)
        return layout

        
    top_column = [
        [
            sg.Frame('',[
                [
                    sg.Radio('File','-type_selector_input_radio-',default=True,k='-file_radio-',enable_events=True),
                    sg.Radio('Directory','-type_selector_input_radio-',default=False,k='-directory_radio-',enable_events=True),
                        sg.Frame('',[
                            [
                                sg.Button(image_data=ic.patreon,expand_x=False,visible=True,enable_events=True,key="-patreon-",button_color=(COLOR_GRAY_9900,COLOR_GRAY_9900)),
                                sg.Button(image_data=ic.supportme,expand_x=False,visible=False,enable_events=True,key="-supportme-",button_color=(COLOR_GRAY_9900,COLOR_GRAY_9900)),
                                sg.Button(image_data=ic.github,expand_x=False,visible=True,enable_events=True,key="-github-",button_color=(COLOR_GRAY_9900,COLOR_GRAY_9900))
                            ],
                        ],expand_x=True,expand_y=False,relief=sg.RELIEF_SOLID,border_width=1,visible=True,background_color=COLOR_GRAY_9900,element_justification="r")

                ],                
            ],expand_x=True,expand_y=False,relief=sg.RELIEF_SOLID,border_width=1,visible=True,background_color=COLOR_GRAY_9900)
        ],    
        [
            browse_layout('file',True),    
            browse_layout('directory',False),    
        ],
    ]

    console_column = [
        [
            sg.Frame('',[         
                    [              
                        sg.Button('CONVERT',k='-convert_button-',font='Ariel 12 ',expand_x=True,size=(10,2),mouseover_colors=(COLOR_GRAY_9900,COLOR_DARK_GREEN)),
                    ], 

                    [
                        sg.MLine(k='-console_ml-',reroute_stdout=True,write_only=False,reroute_cprint=True, autoscroll=True, text_color='white', auto_refresh=True,size=(100,20),expand_x=True,expand_y=True),
                    ], 
            ],expand_x=True,expand_y=True,border_width=0,relief=sg.RELIEF_FLAT)
        ],  
    ]
  
    bottom_column = [
        [
            sg.Frame('',[                    
            
                    [
                        cpbar.progress_bar_custom_layout(pbar_progress_bar_key,visible=True,it_name="ckpt")
                    ],
            ],expand_x=True,border_width=0,relief=sg.RELIEF_FLAT,element_justification='c')
        ],    
    ]

    layout = [[
             top_column,       
            [
                sg.Column(console_column, key='-console_column-', element_justification='r', expand_x=True,expand_y=True,visible=True),
            ],        
             bottom_column,
        ]
    ]

    #endregion layout

    window = sg.Window(app_title,layout,finalize=True, resizable=True,enable_close_attempted_event=False,background_color=COLOR_GRAY_9900)
    window.hide    

    #region widget and flating

    convert_button_widget = window["-convert_button-"]
    file_FileBrowse_widget = window["-file_FileBrowse-"]
    directory_FolderBrowse_widget = window["-directory_FolderBrowse-"]
    input_files_file_widget = window["-input_files_file-"]
    input_files_directory_widget = window["-input_files_directory-"]
    console_ml_widget = window["-console_ml-"]
    patreon_widget = window["-patreon-"]
    supportme_widget = window["-supportme-"]
    github_widget = window["-github-"]


    widgets = {
        convert_button_widget,
        file_FileBrowse_widget,
        directory_FolderBrowse_widget,
        input_files_file_widget,
        input_files_directory_widget,
        patreon_widget,
        github_widget,
        supportme_widget,
    }

    for widget in widgets:
        widget.Widget.config(relief='flat')  
    #endregion 
        
    def convert_button_disable():
        convert_button_widget.update('CONVERTING')
        convert_button_widget.update(disabled_button_color=(COLOR_DARK_GREEN,COLOR_GRAY_9900))
        convert_button_widget.update(disabled=True) 
   
    def convert_button_enable():
        convert_button_widget.update(disabled=False)
        convert_button_widget.update('CONVERT') 


    def process_file(file_path):
        convert_to_st(file_path)
        cpbar.progress_bar_custom(0,1,start_time,window,pbar_progress_bar_key,"ckpt")
        convert_button_enable()

    def process_directory(path,idx):
        for base_path, _, file_names in os.walk(path):
            for file_name in file_names:
                file_ext = os.path.splitext(file_name)[1]
                if (
                    file_ext not in _pytorch_file_extensions
                ):
                    continue
                file_path = os.path.join(base_path, file_name)
                input_directory_path_list.append(file_path)
                print(f' {file_name}')

      
        for file_name in input_directory_path_list:
            idx = (idx+1)
            convert_to_st(file_name)
            cpbar.progress_bar_custom(idx-1,len(input_directory_path_list),start_time,window,pbar_progress_bar_key,"ckpt")
        convert_button_enable()

    def convert_to_st(checkpoint_path):
        modelhash = model_hash(checkpoint_path)
        try:
            with torch.no_grad():
                weights = torch.load(checkpoint_path, map_location=torch.device('cpu'))
                if "state_dict" in weights:
                    weights = weights["state_dict"]
                    if "state_dict" in weights:
                        weights.pop("state_dict")
                file_name = f"{os.path.splitext(checkpoint_path)[0]}.safetensors"

                print(f'Converting {checkpoint_path} [{modelhash}] to safetensors.')
                save_file(weights, file_name)
                print(f'Saving {file_name} [{model_hash(file_name)}].')

        except Exception as e:
            if isinstance(e, (RuntimeError, EOFError)):
                sg.cprint(" FAIL TO LOAD CHECKPOINT: Corrupted file",text_color="white", background_color=COLOR_RED_ORANGE)
            elif isinstance(e, FileNotFoundError):
                sg.cprint(" File Not Found", text_color=COLOR_RED_ORANGE)
            elif isinstance(e, (AttributeError, KeyError)):
                sg.cprint(" FILE NOT SUPPORTED", text_color=COLOR_RED_ORANGE)
            else:
                print(f'Error: {e}')
                

    def model_hash(filename):
        with open(filename, "rb") as file:
            m = hashlib.sha256()
            file.seek(HASH_START)
            m.update(file.read(HASH_LENGTH))
            return m.hexdigest()[0:8]

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break
        
        if event == '-convert_button-': 
            console_ml_widget.update(value='')
            if values['-file_radio-']:
                path = values['-input_files_file-']    
                if path:
                    start_time = dt.today().timestamp()
                    cpbar.progress_bar_reset(window,pbar_progress_bar_key,"ckpt")      
                    convert_button_disable()                  
                    Thread(target=process_file, args=(path,), daemon=True).start()    
                else:
                    print("No path selected")


            if values['-directory_radio-']:
                path = values['-input_files_directory-']
                if path:
                    idx = 0
                    input_directory_path_list = []
                    start_time = dt.today().timestamp()
                    cpbar.progress_bar_reset(window,pbar_progress_bar_key,"ckpt")
                    convert_button_disable()                    
                    Thread(target=process_directory, args=(path,idx), daemon=True).start()                   
                else:
                    print("No path selected")

        if event == '-file_radio-':
                window['-frame_file-'].update(visible=True)  
                window['-frame_directory-'].update(visible=False)  
        if event == '-directory_radio-':
                window['-frame_file-'].update(visible=False)  
                window['-frame_directory-'].update(visible=True)    
    

        if event == "-patreon-":
            webbrowser.open("https://www.patreon.com/distyx")      
        if event == "-github-":
            webbrowser.open("https://github.com/diStyApps/Safe-and-Stable-Ckpt2Safetensors-Conversion-Tool-GUI")  
        if event == "-supportme-":
            webbrowser.open("https://coindrop.to/disty")  
  
                
if __name__ == '__main__':
    main() 

