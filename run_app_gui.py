import PySimpleGUI as sg
import os
import torch 
import webbrowser
import hashlib
import re
from threading import Thread
from datetime import datetime as dt
from dataclasses import dataclass
from safetensors.torch import save_file
from safetensors.torch import load_file
import util.icons as ic
import util.progress_bar_custom as cpbar

__version__ = '0.1.0'
APP_TITLE = f"Safe & Stable - Ckpt2Safetensors Conversion Tool-GUI - Ver {__version__}"
sg.theme('Dark Gray 15')

#region constants

COLOR_DARK_GREEN = '#78BA04'
COLOR_DARK_BLUE = '#4974a5'
COLOR_RED_ORANGE = '#C13515'
COLOR_GRAY_9900 = '#0A0A0A'
COLOR_DARK_GRAY = '#1F1F1F'
COLOR_GREEN = '#43CD80'
COLOR_DARK_GREEN2 = '#78BA04'
COLOR_BLUE_TERMINAL = '#0099ff'
COLOR_GRAY_1111 = '#111111'

HASH_START = 0x100000
HASH_LENGTH = 0x10000

FILEICON = "📑"
DIRECTORYICON = "📂"
UPTEXT = "_____UP_____"
SYSTEM_DRIVE_ICON = "💻"

SAFETENSORS_STRING = "safetensors"
CKPT_STRING = "ckpt"
PBAR_KEY = 'progress_bar'

#endregion

#region extensions variables
_pytorch_file_extensions = {".ckpt"}
_safetensors_file_extensions = {".safetensors"}
_file_extensions = {".ckpt",".safetensors"}

file_ext = {
    ("All", "*.ckpt"),
    ("All", "*.safetensors"),
    ("All", "*.pt"),
}

format_file={
    "ckpt2safetensors": "ck2st",
    "safetensors2ckpt": "st2ck",
}

#endregion

#region dataclasses
@dataclass
class CurrentDirectory:
  path: str

@dataclass
class SelectedFileSystem:
  path: str=None

@dataclass
class SelectedFolder:
  path: str=None    

#endregion

#region functions
def system_file_listings(folder_path, sort="ASC"):
  CurrentDirectory.path = folder_path

  if not os.path.isdir(folder_path):
    print("Error: Invalid folder path.")
    return

  items = os.listdir(folder_path)

  filtered_items = []

  for item in items:

    full_path = os.path.join(folder_path, item)

    if os.path.isfile(full_path):
      if any(item.endswith(ext) for ext in _file_extensions):
        new_item = f'[{FILEICON}] [{item}] [{file_hash(full_path)}]'
        filtered_items.append(new_item)
    else:
      new_item = f'[{DIRECTORYICON}] [{item}]'
      filtered_items.append(new_item)

  if sort == "ASC":
    filtered_items = sorted(filtered_items, key=lambda x: x.lower())
  elif sort == "DESC":
    filtered_items = sorted(filtered_items, key=lambda x: x.lower(), reverse=True)
  else:
    print("Error: Invalid sort order. Must be 'ASC' or 'DESC'.")
    return

  filtered_items.insert(0,UPTEXT)
  return filtered_items

def get_file_list():
    """
    Returns list of filenames or directories to display in the listbox
    :return: List of filenames or directories
    :rtype: List[str]
    """
    return system_file_listings(os.path.join(os.getenv("SystemDrive"), "\\"))

def list_system_drives():
    return [f"[{SYSTEM_DRIVE_ICON}] [{chr(drive)}:/]" for drive in range(ord("C"), ord("Z") + 1) if os.path.exists(f"{chr(drive)}:/")]    

def file_hash(filename):
    with open(filename, "rb") as file:
        m = hashlib.sha256()
        file.seek(HASH_START)
        m.update(file.read(HASH_LENGTH))
        return m.hexdigest()[0:8]

#endregion

def main():
    idx=0
    input_directory_path_list = []
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
                    sg.Radio('File','-type_selector_input_radio-',default=False,k='-file_radio-',enable_events=True,visible=False),
                    sg.Radio('Directory','-type_selector_input_radio-',default=True,k='-directory_radio-',enable_events=True,visible=False),
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
            browse_layout('file',False),    
            browse_layout('directory',True),    
        ],
    ]

    console_column = [
        [
            sg.Frame('',[       
                        [
                            sg.Button('CONVERT FILE',k='-convert_file_button-',font='Ariel 12 ',expand_x=True,size=(30,2),mouseover_colors=(COLOR_GRAY_9900,COLOR_DARK_GREEN)),
                            sg.Checkbox('Add suffix', key='-add_suffix-',default=False,text_color="white",background_color=COLOR_GRAY_9900,font="Ariel 12 ",tooltip="if suffix will not be added to file name file will be overwritten"),
                            sg.Combo(list(format_file.keys()),disabled=False,default_value='ckpt2safetensors',key='-format_selector-',readonly=True,text_color=COLOR_BLUE_TERMINAL,background_color=COLOR_GRAY_9900,expand_x=True,enable_events=True,font="Ariel 12 "),
                            sg.Button('CONVERT DIRECTORY',k='-convert_directory_button-',font='Ariel 12 ',expand_x=True,size=(30,2),mouseover_colors=(COLOR_GRAY_9900,COLOR_DARK_GREEN)),
                        ],                     
                    [
                        sg.Listbox(values=get_file_list(),text_color=COLOR_BLUE_TERMINAL,background_color=COLOR_GRAY_1111,select_mode=sg.SELECT_MODE_BROWSE,expand_x=True,expand_y=True, size=(70,25),bind_return_key=True, key='-browser_lb-',
                        enable_events=True,sbar_relief=sg.RELIEF_FLAT,sbar_trough_color=0,sbar_width=20,font="Ariel 11 ",),      
                        sg.MLine(GREET_MSG,k='-console_ml-',visible=True,text_color='#00cc00',background_color=COLOR_GRAY_1111,border_width=0,sbar_width=20,sbar_trough_color=0,
                        reroute_stdout=True,write_only=False,reroute_cprint=True, autoscroll=True, auto_refresh=True,size=(80,20),expand_x=True,expand_y=True,font="Ariel 11 "),
                    ], 
            ],expand_x=True,expand_y=True,border_width=0,relief=sg.RELIEF_FLAT,element_justification="c",background_color=COLOR_GRAY_9900)
        ],  
    ]
  
    bottom_column = [
        [
            sg.Frame('',[       
                    # [
                    #     sg.HorizontalSeparator(color=COLOR_GRAY_1111),
                    # ],                
                    [  
                        sg.Checkbox('If not checked will save to same folder', key='-save_output_checkbox-',default=False,text_color="white",background_color=COLOR_GRAY_9900,visible=False),    
                        sg.Input(key='-save_output-',expand_x=True,visible=False),sg.FolderBrowse('Save location',k=f'-save_output_FileBrowse-',disabled=False,visible=False)                     
                    ],                  
                    # [
                    #     sg.HorizontalSeparator(color=COLOR_GRAY_1111),
                    # ],
                    [
                        cpbar.progress_bar_custom_layout(PBAR_KEY,visible=True,it_name="file")
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

    window = sg.Window(APP_TITLE,layout,finalize=True, resizable=True,enable_close_attempted_event=False,background_color=COLOR_GRAY_9900)
    window.hide    

    #region widget and flating

    convert_file_button_widget = window["-convert_file_button-"]
    convert_file_directory_widget = window["-convert_directory_button-"]
    save_output_filebrowse_widget = window["-save_output_FileBrowse-"]

    file_FileBrowse_widget = window["-file_FileBrowse-"]
    directory_FolderBrowse_widget = window["-directory_FolderBrowse-"]
    input_files_file_widget = window["-input_files_file-"]
    input_files_directory_widget = window["-input_files_directory-"]
    save_output_widget = window["-save_output-"]
    console_ml_widget = window["-console_ml-"] 
    browser_lb_widget = window["-browser_lb-"]

    patreon_widget = window["-patreon-"]
    supportme_widget = window["-supportme-"]
    github_widget = window["-github-"]

    widgets = {
        convert_file_button_widget,
        convert_file_directory_widget,
        file_FileBrowse_widget,
        directory_FolderBrowse_widget,
        input_files_file_widget,
        input_files_directory_widget,
        patreon_widget,
        github_widget,
        supportme_widget,
        browser_lb_widget,
        save_output_filebrowse_widget,
        save_output_widget,
    }

    for widget in widgets:
        widget.Widget.config(relief='flat')  

    #endregion 

    browser_lb_widget.bind('<Double-Button-1>' , "dclick-")
    input_files_directory_widget.update(CurrentDirectory.path)

    def convert_button_disable():
        convert_file_button_widget.update('CONVERTING')
        convert_file_button_widget.update(disabled_button_color=(COLOR_DARK_GREEN,COLOR_GRAY_9900))
        convert_file_button_widget.update(disabled=True) 

        convert_file_directory_widget.update('CONVERTING')
        convert_file_directory_widget.update(disabled_button_color=(COLOR_DARK_GREEN,COLOR_GRAY_9900))
        convert_file_directory_widget.update(disabled=True)
   
    def convert_button_enable():
        convert_file_button_widget.update(disabled=False)
        convert_file_button_widget.update('CONVERT FILE') 

        convert_file_directory_widget.update(disabled=False)
        convert_file_directory_widget.update('CONVERT DIRECTORY')

    def process_file(file_path,type_format,suffix):
        if type_format == SAFETENSORS_STRING:
            convert_to_st(file_path,suffix)
        if type_format == CKPT_STRING:
            convert_to_ckpt(file_path,suffix)

        cpbar.progress_bar_custom(0,1,start_time,window,PBAR_KEY,"file")
        convert_button_enable()
        browser_lb_widget.update(system_file_listings(CurrentDirectory.path, sort="ASC"))
        input_files_directory_widget.update(CurrentDirectory.path)
        SelectedFileSystem.path = None

    def process_directory(path,idx,type_format,suffix):
        if type_format == CKPT_STRING:
            _file_extensions = _pytorch_file_extensions
        if type_format == SAFETENSORS_STRING:
            _file_extensions = _safetensors_file_extensions

        for base_path, _, file_names in os.walk(path):
            for file_name in file_names:
                file_ext = os.path.splitext(file_name)[1]
                if (
                    file_ext not in _file_extensions
                ):
                    continue
                file_path = os.path.join(base_path, file_name)
                input_directory_path_list.append(file_path)
                print(f' {file_name}')

            if type_format == CKPT_STRING:
                for file_name in input_directory_path_list:
                    idx = (idx+1)
                    convert_to_st(file_name,suffix)
                    cpbar.progress_bar_custom(idx-1,len(input_directory_path_list),start_time,window,PBAR_KEY,"file")

            if type_format == SAFETENSORS_STRING:
                for file_name in input_directory_path_list:
                    idx = (idx+1)
                    convert_to_ckpt(file_name,suffix)
                    cpbar.progress_bar_custom(idx-1,len(input_directory_path_list),start_time,window,PBAR_KEY,"file")
            
        browser_lb_widget.update(system_file_listings(CurrentDirectory.path, sort="ASC"))
        input_files_directory_widget.update(CurrentDirectory.path)
        convert_button_enable()

    def convert_to_st(checkpoint_path,suffix):
        # Compute the hash of the checkpoint file
        modelhash = file_hash(checkpoint_path)

        # Load the weights of the model from the checkpoint file
        weights = load_weights(checkpoint_path)

        # Generate the file name for the safetensors file
        if suffix:
            file_name = f"{os.path.splitext(checkpoint_path)[0]}-cnvrtd.{SAFETENSORS_STRING}"
        else:
            file_name = f"{os.path.splitext(checkpoint_path)[0]}.{SAFETENSORS_STRING}"

        # file_name = f"{os.path.splitext(checkpoint_path)[0]}-cnvrtd.safetensors"

        # Save the weights to the safetensors file
        # save_file(weights, file_name)
        save_file(weights, file_name)


        # Print a message indicating the conversion was successful
        print(f'Converting {checkpoint_path} [{modelhash}] to {SAFETENSORS_STRING}.')
        print(f'Saving {file_name} [{file_hash(file_name)}].')
    
    def convert_to_ckpt(filename,suffix):
        modelhash = file_hash(filename)
        weights = load_file(filename, device="cpu")

        try:
           weights = load_file(filename, device="cpu")
        except Exception as e:
            print(f'Error: {e}')
        try:
            print(f'Converting {filename} [{modelhash}] to {CKPT_STRING}.')
            weights = load_file(filename, device="cpu")

            if suffix:
                checkpoint_filename = f"{os.path.splitext(filename)[0]}-cnvrtd.{CKPT_STRING}"
            else:
                checkpoint_filename = f"{os.path.splitext(filename)[0]}.{CKPT_STRING}"

            save_checkpoint(weights, checkpoint_filename)
            print(f'Saving {checkpoint_filename} [{file_hash(checkpoint_filename)}].')
                
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                print(" File Not Found")
            else:
                print(f'Error: {e}')
        
    def save_checkpoint(weights, filename):
        with open(filename, "wb") as f:
            torch.save(weights, f)
 
    def load_weights(checkpoint_path):
        try:
            # Load the weights from the checkpoint file, without computing gradients
            with torch.no_grad():
                weights = torch.load(checkpoint_path, map_location=torch.device('cpu'))
                # Check if the weights are contained in a "state_dict" key
                if "state_dict" in weights:
                    weights = weights["state_dict"]
                    # If the weights are nested in another "state_dict" key, remove it
                    if "state_dict" in weights:
                        weights.pop("state_dict")
                return weights
        except Exception as e:
            if isinstance(e, (RuntimeError, EOFError)):
                sg.cprint(" FAIL TO LOAD CHECKPOINT: Corrupted file",text_color="white", background_color=COLOR_RED_ORANGE)
            elif isinstance(e, FileNotFoundError):
                sg.cprint(" File Not Found", text_color=COLOR_RED_ORANGE)
            elif isinstance(e, (AttributeError, KeyError)):
                sg.cprint(" FILE NOT SUPPORTED", text_color=COLOR_RED_ORANGE)
            else:
                print(f'Error: {e}')   
  
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break
  
        if event == "-input_files_directory-":
            input_files_directory_widget.update(values["-input_files_directory-"])
            browser_lb_widget.update(system_file_listings(values["-input_files_directory-"], sort="ASC"))

        if event == "-browser_lb-":
            # get the selected item from the widget
            system_file_values_list = values["-browser_lb-"]
            # dedect if is root drive like C:\ or D:\ or E:\ etc
            if system_file_values_list[0][1:] == ":/" : 
                # print("root drive")
                pass
            elif system_file_values_list:
                system_file_values = system_file_values_list[0]
                if system_file_values == UPTEXT:
                    SelectedFolder.path = None
                    SelectedFileSystem.path = None

                else:
                    system_file_list = re.findall("\[([^\]]+)\]", system_file_values)
                    icon = system_file_list[0]
                    system_file = system_file_list[1]
                    system_file_fullpath = os.path.normpath(os.path.join(CurrentDirectory.path, system_file))

                    if icon == DIRECTORYICON:
                        SelectedFolder.path = system_file_fullpath
                        SelectedFileSystem.path = None
                    elif icon == FILEICON:
                        SelectedFileSystem.path = system_file_fullpath
                        SelectedFolder.path = None

        if event == "-browser_lb-dclick-":
            system_file_values_list = values["-browser_lb-"]
            if system_file_values_list:
                system_file_values = system_file_values_list[0]
                back_path = input_files_directory_widget.get()
                if system_file_values == UPTEXT:
                        # go back to the previous directory
                    if back_path[1:] == ":\\" or back_path[1:] == ":/": # if is root drive
                        # print("root drive")
                        input_files_directory_widget.update("")
                        browser_lb_widget.update(list_system_drives())                        
                    else:
                        # print("not root drive")
                        try:
                            back_path = os.path.split(input_files_directory_widget.get())[0]
                            browser_lb_widget.update(system_file_listings(f"{back_path}", sort="ASC"))
                            input_files_directory_widget.update(f"{back_path}")
                        except Exception as e:
                            # print(e)
                            pass
                else:
                    system_file_list = re.findall("\[([^\]]+)\]", system_file_values)
                    icon = system_file_list[0]
                    system_file = system_file_list[1]
                    system_file_fullpath = os.path.normpath(os.path.join(CurrentDirectory.path, system_file))                        

                    if icon == SYSTEM_DRIVE_ICON:
                        input_files_directory_widget.update(system_file_fullpath)
                        browser_lb_widget.update(system_file_listings(system_file_fullpath, sort="ASC"))
                    if icon == DIRECTORYICON:
                        try:
                            listing_ = system_file_listings(system_file_fullpath, sort="ASC")
                            browser_lb_widget.update(listing_)
                            input_files_directory_widget.update(system_file_fullpath)
                        except:
                            pass

        if event == '-convert_file_button-': 
            # print("Selected: ", SelectedFileSystem.path)
            console_ml_widget.update(value='')
            selected_path = SelectedFileSystem.path
            if selected_path:
                suffix = values['-add_suffix-']                
                start_time = dt.today().timestamp()
                cpbar.progress_bar_reset(window,PBAR_KEY,"file")      
                convert_button_disable()                  
             
                if selected_path.endswith(".ckpt") :
                    print("convert to .safetensors")
                    type_format = SAFETENSORS_STRING
                elif selected_path.endswith(".safetensors"):
                    print("convert to .ckpt")
                    type_format = CKPT_STRING

                Thread(target=process_file, args=(selected_path,type_format,suffix), daemon=True).start()    
  
        if event == '-convert_directory_button-':
            print("Selected: ", CurrentDirectory.path)
            console_ml_widget.update(value='')
            selected_path = CurrentDirectory.path
            format_selector_values = values['-format_selector-']
            suffix = values['-add_suffix-']                
            idx = 0
            input_directory_path_list = []
            start_time = dt.today().timestamp()
            cpbar.progress_bar_reset(window,PBAR_KEY,"file")      
            convert_button_disable()                 

            # print("format_selector_values",format_selector_values,SelectedFolder.path)

            if SelectedFolder.path:
                selected_path = SelectedFolder.path
            else:
                selected_path = CurrentDirectory.path

            print("selected_path",selected_path)

            if format_selector_values =="ckpt2safetensors":
                print(f"convert to .{SAFETENSORS_STRING}")
                type_format = CKPT_STRING

            if format_selector_values =="safetensors2ckpt":
                print("convert to .ckpt")    
                type_format = SAFETENSORS_STRING

            Thread(target=process_directory, args=(selected_path,idx,type_format,suffix), daemon=True).start()
       
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

    GREET_MSG=f"""
        Greetings!

        You are using {APP_TITLE}

        This tool is designed to convert Stable Diffusion .ckpt files to safetensors files
        and vice versa.
        More formats will be added in the future.

        Please consider donating to the project if you find it useful,
        so that I can maintain and improve this tool and other projects.

        Instructions:

        Select a file or directory to convert.

        To convert a single file, select the file then click the convert file button.
        If ckpt file selected, the output will be a safetensors file and vice versa.

        To convert a directory, select the directory then select format to convert to. 
        Then click the convert directory button.
        You can convert directory by selecting a directory or by entering a directory.

        To add suffix to output file, check the add suffix checkbox.
        If dont add suffix, the output file will be named the same as the input file.
        And files will be overwritten if they already exist.

        """    
 
    main() 


