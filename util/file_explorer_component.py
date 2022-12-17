import util.colors as color
import PySimpleGUI as sg
from dataclasses import dataclass
from util.file_hash import get_file_hash
import os
import re

FILE_ICON = "📑"
DIRECTORY_ICON = "📂"
UP_DIRECTORY_TXT = "_____UP_____"
SYSTEM_DRIVE_ICON = "💻"
FILE_EXPLORER_LSTBOX_KEY = "-file_explorer_lstbox-"
FOLDER_INP_KEY = '-folder_inp_browse-'
FONT = 'Arial 12'


# "-browser_lb-dclick-"
_file_extensions = {".ckpt",".safetensors"}

@dataclass
class CurrentDirectory:
  path: str

@dataclass
class SelectedFileSystem:
  path: str=None

@dataclass
class SelectedFolder:
  path: str=None    

def setup(window):
    folder_browse_inp_elem:sg.Input = window[FOLDER_INP_KEY]
    file_explorer_lstbox_key_elem:sg.Listbox = window[FILE_EXPLORER_LSTBOX_KEY]
    file_explorer_lstbox_key_elem.bind('<Double-Button-1>',"dclick-")
    folder_browse_inp_elem.update(CurrentDirectory.path)
    return folder_browse_inp_elem,file_explorer_lstbox_key_elem

def get_system_files(folder_path, sort="ASC"):
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
        new_item = f'[{FILE_ICON}] [{item}] [{get_file_hash(full_path)}]'
        filtered_items.append(new_item)
    else:
      new_item = f'[{DIRECTORY_ICON}] [{item}]'
      filtered_items.append(new_item)

  if sort == "ASC":
    filtered_items = sorted(filtered_items, key=lambda x: x.lower())
  elif sort == "DESC":
    filtered_items = sorted(filtered_items, key=lambda x: x.lower(), reverse=True)
  else:
    print("Error: Invalid sort order. Must be 'ASC' or 'DESC'.")
    return

  filtered_items.insert(0,UP_DIRECTORY_TXT)
  return filtered_items

def get_system_files_list():
    """
    Returns list of filenames or directories to display in the listbox
    :return: List of filenames or directories
    :rtype: List[str]
    """
    return get_system_files(os.path.join(os.getenv("SystemDrive"), "\\"))

def layout():

    layout = sg.Frame('',[                           
            [
                sg.Listbox(key=FILE_EXPLORER_LSTBOX_KEY,values=get_system_files_list(),text_color=color.TERMINAL_BLUE,background_color=color.GRAY_1111,
                select_mode=sg.SELECT_MODE_BROWSE,expand_x=True,expand_y=True, size=(70,25),bind_return_key=True,
                enable_events=True,sbar_relief=sg.RELIEF_FLAT,sbar_trough_color=0,sbar_width=20,font="Ariel 11 ",),      
            ], 
    ],expand_x=True,expand_y=True,border_width=0,relief=sg.RELIEF_FLAT,element_justification="c",background_color=color.GRAY_9900)


    return layout

def get_system_drives():
    return [f"[{SYSTEM_DRIVE_ICON}] [{chr(drive)}:/]" for drive in range(ord("C"), ord("Z") + 1) if os.path.exists(f"{chr(drive)}:/")]    

def mouse_clicks_events(event, values,input_files_directory_widget,file_explorer_lstbox_key_elem):
        if event == FILE_EXPLORER_LSTBOX_KEY:
            # get the selected item from the widget
            system_file_values_list = values[FILE_EXPLORER_LSTBOX_KEY]
            # dedect if is root drive like C:\ or D:\ or E:\ etc
            if system_file_values_list[0][1:] == ":/" : 
                # print("root drive")
                pass
            elif system_file_values_list:
                system_file_values = system_file_values_list[0]
                if system_file_values == UP_DIRECTORY_TXT:
                    SelectedFolder.path = None
                    SelectedFileSystem.path = None

                else:
                    system_file_list = re.findall("\[([^\]]+)\]", system_file_values)
                    icon = system_file_list[0]
                    system_file = system_file_list[1]
                    system_file_fullpath = os.path.normpath(os.path.join(CurrentDirectory.path, system_file))

                    if icon == DIRECTORY_ICON:
                        SelectedFolder.path = system_file_fullpath
                        SelectedFileSystem.path = None
                    elif icon == FILE_ICON:
                        SelectedFileSystem.path = system_file_fullpath
                        SelectedFolder.path = None

        if event == f"{FILE_EXPLORER_LSTBOX_KEY}dclick-":
            system_file_values_list = values[FILE_EXPLORER_LSTBOX_KEY]
            if system_file_values_list:
                system_file_values = system_file_values_list[0]
                back_path = input_files_directory_widget.get()
                if system_file_values == UP_DIRECTORY_TXT:
                        # go back to the previous directory
                    if back_path[1:] == ":\\" or back_path[1:] == ":/": # if is root drive
                        # print("root drive")
                        input_files_directory_widget.update("")
                        file_explorer_lstbox_key_elem.update(get_system_drives())                        
                    else:
                        # print("not root drive")
                        try:
                            back_path = os.path.split(input_files_directory_widget.get())[0]
                            file_explorer_lstbox_key_elem.update(get_system_files(f"{back_path}", sort="ASC"))
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
                        file_explorer_lstbox_key_elem.update(get_system_files(system_file_fullpath, sort="ASC"))
                    if icon == DIRECTORY_ICON:
                        try:
                            listing_ = get_system_files(system_file_fullpath, sort="ASC")
                            file_explorer_lstbox_key_elem.update(listing_)
                            input_files_directory_widget.update(system_file_fullpath)
                        except:
                            pass

def folder_inp_browse_layout(visible_,disabled=False):        
    layout = sg.Frame('',[
                            [
                                sg.Input(key=FOLDER_INP_KEY,readonly=True,disabled_readonly_background_color=color.DARK_GRAY,enable_events=True,
                                expand_x=True,expand_y=True,font=FONT,background_color=color.DARK_GRAY),
                                sg.FolderBrowse(disabled=disabled,size=(10,2))
                            ],
                        ],expand_x=True,visible=visible_,relief=sg.RELIEF_SOLID,border_width=1,background_color=color.GRAY_9900)
    return layout

def folder_inp_browse_events(event,values,folder_browse_inp_elem,file_explorer_lstbox_key_elem):
    if event == FOLDER_INP_KEY:
        folder_browse_inp_elem.update(values[FOLDER_INP_KEY])
        file_explorer_lstbox_key_elem.update(get_system_files(values[FOLDER_INP_KEY], sort="ASC"))