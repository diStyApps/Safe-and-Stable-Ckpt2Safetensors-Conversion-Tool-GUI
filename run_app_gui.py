import PySimpleGUI as sg
import os
import torch 
from threading import Thread
from datetime import datetime as dt
from safetensors.torch import save_file
from safetensors.torch import load_file
from util.ui_flattener import flatten_ui_elements
from util.file_hash import get_file_hash
import util.progress_bar_custom as cpbar
import util.file_explorer_component as file_explorer
import util.colors as color
import util.support as support
from CONSTANTS import *

__version__ = '0.1.1'
APP_TITLE = f"Safe & Stable - Ckpt2Safetensors Conversion Tool-GUI - Ver {__version__}"
sg.theme('Dark Gray 15')

format_file={
    "ckpt2safetensors": "ck2st",
    "safetensors2ckpt": "st2ck",
}

def main():
    idx=0
    input_directory_path_list = []
    start_time = dt.today().timestamp()

    #region layout

    top_column = [
        [
            sg.Frame('',[
                [support.buttons_layout()],
                [
                    sg.Radio(FILE_LBL,TYPE_SELECTOR_INP_RAD_KEY,default=False,k=FILE_RAD_KEY,enable_events=True,visible=False),
                    sg.Radio(DIRECTORY_LBL,TYPE_SELECTOR_INP_RAD_KEY,default=True,k=DIRECTORY_RAD_KEY,enable_events=True,visible=False),
                ],                
            ],expand_x=True,expand_y=False,relief=sg.RELIEF_SOLID,border_width=1,visible=True,background_color=color.GRAY_9900)
        ],    
        [
            file_explorer.folder_inp_browse_layout(True),    
        ],
        # [
        #     sg.Frame('',[       
        #         [  
        #             sg.Checkbox('If not checked will save to same folder', key='-save_output_checkbox-',default=False,text_color="white",background_color=COLOR.GRAY_9900),    
        #             sg.Input(key='-save_output-',expand_x=True,expand_y=True,size=(10,20)),sg.FolderBrowse('Save location',k=f'-save_output_FileBrowse-')                     
        #         ], 
        #     ],expand_x=True,border_width=0,relief=sg.RELIEF_FLAT,element_justification='c',background_color=COLOR.GRAY_9900)
        # ],        
    ]

    mid_column = [
        [
            sg.Frame('',[       
                        [
                            sg.Button(CONVERT_FILE_BTN_LBL,k=CONVERT_FILE_BTN_KEY,font=FONT,expand_x=True,size=(30,2),mouseover_colors=(color.GRAY_9900,color.DARK_GREEN)),
                            sg.Checkbox(ADD_SUFFIX_CHKBOX_LBL, key=ADD_SUFFIX_CHKBOX_KEY,default=False,background_color=color.GRAY_9900,font=FONT,
                            tooltip="if suffix will not be added to file name file will be overwritten"),
                            sg.Combo(list(format_file.keys()),default_value=list(format_file.keys())[0],disabled=False,key=FORMAT_SELECTOR_COMBO_KEY,readonly=True,text_color=color.TERMINAL_BLUE,background_color=color.GRAY_9900,expand_x=True,enable_events=True,font=FONT),
                            sg.Button(CONVERT_DIRECTORY_BTN_LBL,k=CONVERT_DIRECTORY_BTN_KEY,font=FONT,expand_x=True,size=(30,2),mouseover_colors=(color.GRAY_9900,color.DARK_GREEN)),
                        ],                     
                    [
                        file_explorer.layout(),     
                        sg.MLine(GREET_MSG,k=CONSOLE_ML_KEY,visible=True,text_color=color.TERMINAL_GREEN2,background_color=color.GRAY_1111,border_width=0,sbar_width=20,sbar_trough_color=0,
                        reroute_stdout=True,write_only=False,reroute_cprint=True, autoscroll=True, auto_refresh=True,size=(80,20),expand_x=True,expand_y=True,font=CONSOLE_FONT),
                    ], 
            ],expand_x=True,expand_y=True,border_width=0,relief=sg.RELIEF_FLAT,element_justification="c",background_color=color.GRAY_9900)
        ],  
    ]
  
    bottom_column = [
        [
            sg.Frame('',[       
                    [
                        cpbar.progress_bar_custom_layout(PBAR_KEY,visible=True,it_name="file")
                    ],
            ],expand_x=True,border_width=0,relief=sg.RELIEF_FLAT,element_justification='c')
        ],    
    ]

    layout = [[
            top_column,       
            mid_column,      
            bottom_column,
        ]
    ]

    #endregion layout

    window = sg.Window(APP_TITLE,layout,finalize=True, resizable=True,enable_close_attempted_event=False,background_color=color.GRAY_9900)

    convert_file_btn_elem:sg.Button = window[CONVERT_FILE_BTN_KEY]
    convert_file_directory_btn_elem:sg.Button = window[CONVERT_DIRECTORY_BTN_KEY]
    console_ml_elem:sg.Multiline = window[CONSOLE_ML_KEY] 
    folder_browse_inp_elem,file_explorer_lstbox_key_elem = file_explorer.setup(window)

    flatten_ui_elements(window)

    def convert_button_disable():
        convert_file_btn_elem.update(CONVERTING_TXT)
        convert_file_btn_elem.update(disabled_button_color=(color.DARK_GREEN,color.GRAY_9900))
        convert_file_btn_elem.update(disabled=True) 

        convert_file_directory_btn_elem.update(CONVERTING_TXT)
        convert_file_directory_btn_elem.update(disabled_button_color=(color.DARK_GREEN,color.GRAY_9900))
        convert_file_directory_btn_elem.update(disabled=True)
   
    def convert_button_enable():
        convert_file_btn_elem.update(disabled=False)
        convert_file_btn_elem.update(CONVERT_FILE_BTN_LBL) 

        convert_file_directory_btn_elem.update(disabled=False)
        convert_file_directory_btn_elem.update(CONVERT_DIRECTORY_BTN_LBL)

    def process_file(file_path,type_format,suffix):
        if type_format == SAFETENSORS_STR:
            convert_to_st(file_path,suffix)
        if type_format == CKPT_STR:
            convert_to_ckpt(file_path,suffix)

        cpbar.progress_bar_custom(0,1,start_time,window,PBAR_KEY,"file")

        file_explorer_lstbox_key_elem.update(file_explorer.get_system_files(file_explorer.CurrentDirectory.path, sort="ASC"))
        folder_browse_inp_elem.update(file_explorer.CurrentDirectory.path)
        convert_button_enable()

        file_explorer.SelectedFileSystem.path = None

    def process_directory(path,idx,type_format,suffix):
        if type_format == CKPT_STR:
            _file_extensions = PYTORCH_FILE_EXTENSIONS
        if type_format == SAFETENSORS_STR:
            _file_extensions = SAFETENSORS_FILE_EXTENSIONS

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

            if type_format == CKPT_STR:
                for file_name in input_directory_path_list:
                    idx = (idx+1)
                    convert_to_st(file_name,suffix)
                    cpbar.progress_bar_custom(idx-1,len(input_directory_path_list),start_time,window,PBAR_KEY,"file")

            if type_format == SAFETENSORS_STR:
                for file_name in input_directory_path_list:
                    idx = (idx+1)
                    convert_to_ckpt(file_name,suffix)
                    cpbar.progress_bar_custom(idx-1,len(input_directory_path_list),start_time,window,PBAR_KEY,"file")
            
        file_explorer_lstbox_key_elem.update(file_explorer.get_system_files(file_explorer.CurrentDirectory.path, sort="ASC"))
        folder_browse_inp_elem.update(file_explorer.CurrentDirectory.path)
        convert_button_enable()

    def convert_to_st(checkpoint_path,suffix):
        model_hash = get_file_hash(checkpoint_path)
        weights = load_weights(checkpoint_path)
        file_name = f"{os.path.splitext(checkpoint_path)[0]}-cnvrtd.{SAFETENSORS_STR}" if suffix else f"{os.path.splitext(checkpoint_path)[0]}.{SAFETENSORS_STR}"
        save_file(weights, file_name)
        print(f'{CONVERTING_TXT} {checkpoint_path} [{model_hash}] to {SAFETENSORS_STR}.')
        print(f'Saving {file_name} [{get_file_hash(file_name)}].')
    
    def convert_to_ckpt(filename,suffix):
        model_hash = get_file_hash(filename)
        device = "cpu"
        weights = load_file(filename, device=device)

        try:
           weights = load_file(filename, device=device)
        except Exception as e:
            print(f'Error: {e}')

        try:
            print(f'{CONVERTING_TXT} {filename} [{model_hash}] to {CKPT_STR}.')
            weights = load_file(filename, device=device)
            weights["state_dict"] = weights
            checkpoint_filename = f"{os.path.splitext(filename)[0]}-cnvrtd.{CKPT_STR}" if suffix else f"{os.path.splitext(filename)[0]}.{CKPT_STR}"
            save_checkpoint(weights, checkpoint_filename)
            print(f'Saving {checkpoint_filename} [{get_file_hash(checkpoint_filename)}].')
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
                sg.cprint(" FAIL TO LOAD CHECKPOINT: Corrupted file",text_color="white", background_color=color.RED_ORANGE)
            elif isinstance(e, FileNotFoundError):
                sg.cprint(" File Not Found", text_color=color.RED_ORANGE)
            elif isinstance(e, (AttributeError, KeyError)):
                sg.cprint(" FILE NOT SUPPORTED", text_color=color.RED_ORANGE)
            else:
                print(f'Error: {e}')   
  
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break
  
        if event == CONVERT_FILE_BTN_KEY: 
            console_ml_elem.update(value='')
            selected_path = file_explorer.SelectedFileSystem.path
            if selected_path:
                suffix = values[ADD_SUFFIX_CHKBOX_KEY]                
                start_time = dt.today().timestamp()
                cpbar.progress_bar_reset(window,PBAR_KEY,"file")      
                convert_button_disable()                  
             
                if selected_path.endswith(f".{CKPT_STR}") :
                    print(f"{CONVERTING_TXT} to .{SAFETENSORS_STR}")
                    type_format = SAFETENSORS_STR
                elif selected_path.endswith(f".{SAFETENSORS_STR}"):
                    print(f"{CONVERTING_TXT} to .{CKPT_STR}")
                    type_format = CKPT_STR

                Thread(target=process_file, args=(selected_path,type_format,suffix), daemon=True).start()    
  
        if event == CONVERT_DIRECTORY_BTN_KEY:
            console_ml_elem.update(value='')
            selected_path = file_explorer.CurrentDirectory.path
            format_selector_values = values[FORMAT_SELECTOR_COMBO_KEY]
            suffix = values[ADD_SUFFIX_CHKBOX_KEY]                
            idx = 0
            input_directory_path_list = []
            start_time = dt.today().timestamp()
            cpbar.progress_bar_reset(window,PBAR_KEY,"file")      
            convert_button_disable()                 

            if file_explorer.SelectedFolder.path:
                selected_path = file_explorer.SelectedFolder.path
            else:
                selected_path = file_explorer.CurrentDirectory.path

            print("selected_path",selected_path)

            if format_selector_values =="ckpt2safetensors":
                print(f"{CONVERTING_TXT} to .{SAFETENSORS_STR}")
                type_format = CKPT_STR

            if format_selector_values =="safetensors2ckpt":
                print(f"{CONVERTING_TXT} to .{CKPT_STR}")
                type_format = SAFETENSORS_STR

            Thread(target=process_directory, args=(selected_path,idx,type_format,suffix), daemon=True).start()
       
        file_explorer.mouse_clicks_events(event, values,folder_browse_inp_elem,file_explorer_lstbox_key_elem)
        file_explorer.folder_inp_browse_events(event, values,folder_browse_inp_elem,file_explorer_lstbox_key_elem)
        support.buttons(event)

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


