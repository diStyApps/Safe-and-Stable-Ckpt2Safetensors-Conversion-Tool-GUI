import pandas as pd
from datetime import datetime  as dt
import datetime
import PySimpleGUI as sg

COLOR_GREEN = '#43CD80'
COLOR_DARK_GREEN2 = '#78BA04'
COLOR_DARK_GREEN = '#74a549'
COLOR_BLUE = '#69b1ef'
COLOR_RED = '#E74555'
COLOR_RED_ORANGE = '#C13515'
COLOR_GRAY_9900 = '#0A0A0A'
COLOR_ORANGE ='#FE7639'
COLOR_PURPLE = '#a501e8'
COLOR_DARK_GRAY = '#1F1F1F'
COLOR_DARK_BLUE = '#4974a5'

def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    step_unit = 1000.0 #1024 bad the size

    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < step_unit:
            return "%3.1f %s" % (num, x)
        num /= step_unit

def progress_bar_custom_layout(pbar_progress_bar_key_,visible=True,it_name="it"):
    # layout = sg.Text('0/0',k='-pbar_index_range_video_face_swap-',expand_x=True,size=(3, 1),visible=True),



    pbar_progress_bar_key = f'-pbar_progress_bar_{pbar_progress_bar_key_}-'
    pbar_index_range_key = f'-pbar_index_range_{pbar_progress_bar_key_}-'
    pbar_estimated_time_key = f'-pbar_estimated_time_{pbar_progress_bar_key_}-'
    pbar_iteration_per_sec_key = f'-pbar_it_per_sec_{pbar_progress_bar_key_}-'
    pbar_percentage_key = f'-pbar_percentage_{pbar_progress_bar_key_}-'

    # print(pbar_progress_bar_key)
    # print(pbar_index_range_key)
    # print(pbar_estimated_time_key)
    # print(pbar_iteration_per_sec_key)
    # print(pbar_percentage_key)



    layout = sg.Frame('',[
        [
            sg.Text('0%',k=pbar_percentage_key,size=(5, 1)),
            sg.ProgressBar(12, orientation='h', size=(15, 15),expand_x=True, key=pbar_progress_bar_key,bar_color=(COLOR_DARK_GREEN,None)),
            sg.Text('0/0',k=pbar_index_range_key,expand_x=True,size=(3, 1),visible=True),
            sg.Text(f'0.0 {it_name}/s',k=pbar_iteration_per_sec_key,expand_x=False,size=(10, 1),visible=True),
            sg.Text('00:00:00 / 00:00:00 < 00:00:00',k=pbar_estimated_time_key,expand_x=False),
        ],
        ],expand_x=True,expand_y=True,relief=sg.RELIEF_FLAT,border_width=0,visible=visible) #,element_justification='c',background_color=COLOR_GRAY_9900,title_color=COLOR_DARK_BLUE                         

    return layout

def progress_bar_reset(window,pbar_progress_bar_key_,it_name="it"):

    pbar_progress_bar_key = f'-pbar_progress_bar_{pbar_progress_bar_key_}-'
    pbar_index_range_key = f'-pbar_index_range_{pbar_progress_bar_key_}-'
    pbar_estimated_time_key = f'-pbar_estimated_time_{pbar_progress_bar_key_}-'
    pbar_iteration_per_sec_key = f'-pbar_it_per_sec_{pbar_progress_bar_key_}-'
    pbar_percentage_key = f'-pbar_percentage_{pbar_progress_bar_key_}-'

    window[pbar_progress_bar_key].UpdateBar(0, 0)

    window[pbar_percentage_key].update('0%')
    window[pbar_index_range_key].update('0/0')
    # window[pbar_iteration_per_sec_key].update(f'0.0 {it_name}/s')
    window[pbar_iteration_per_sec_key].update(f'Calculating...')

    
    window[pbar_estimated_time_key].update('00:00:00 / 00:00:00 < 00:00:00')          

def progress_bar_custom(index,range,start_time,window,pbar_progress_bar_key_,it_name="it"):

    pbar_progress_bar_key = f'-pbar_progress_bar_{pbar_progress_bar_key_}-'
    pbar_index_range_key = f'-pbar_index_range_{pbar_progress_bar_key_}-'
    pbar_estimated_time_key = f'-pbar_estimated_time_{pbar_progress_bar_key_}-'
    pbar_iteration_per_sec_key = f'-pbar_it_per_sec_{pbar_progress_bar_key_}-'
    pbar_percentage_key = f'-pbar_percentage_{pbar_progress_bar_key_}-'

    # print(pbar_progress_bar_key)
    # print(pbar_index_range_key)
    # print(pbar_estimated_time_key)
    # print(pbar_iteration_per_sec_key)
    # print(pbar_percentage_key)
    if index == 0:
        index = 1
    else:
        index = (index+1)

    # print('progress_bar_custom_new',index,range)

    window[pbar_progress_bar_key].UpdateBar(index, range)
    
    def format_sec(sec):
        sec = round(sec,2)
        formated_sec_step_1 = str(datetime.timedelta(seconds=sec))
        formated_sec = pd.to_datetime(formated_sec_step_1).strftime('%H:%M:%S')
        return formated_sec

    try:
        time_diff = dt.today().timestamp() - start_time
        it_per_sec = index/time_diff

        time_left = format_sec((range/it_per_sec)-(time_diff))
        avg_time = format_sec((range/it_per_sec))

        time_left_no_format =(range/it_per_sec)-(time_diff)
        avg_time_no_format = (range/it_per_sec)


        estimated_time_format = format_sec(avg_time_no_format-time_left_no_format)
        # elapsed_time = (f'{estimated_time_format}')

        percentage = f'{round(((index)/range*100))}%'
        index_range = f'{index}/{range}'
        iteration_per_sec = f'{round(it_per_sec,2)} {it_name}/s'
        estimated_time = (f'{avg_time} / {estimated_time_format} < {time_left}')



        # full = (f'{index+1}/{range} {round(it_per_sec,2)} it/s {avg_time} / {estimated_time_format} < {time_left}')

        window[pbar_percentage_key].update(percentage)
        window[pbar_index_range_key].update(index_range)
        window[pbar_iteration_per_sec_key].update(iteration_per_sec)
        window[pbar_estimated_time_key].update(estimated_time)          
    except ZeroDivisionError:
        pass 





