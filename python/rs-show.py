# ==============================================================================
#   img2histpdf.py: Compute and plot histogram as well as pdf of an image.------
# ==============================================================================
'''
 img2histpdf.py: Compute and plot histogram as well as pdf of an image.
'''

#   import ---------------------------------------------------------------------
# ==============================================================================

import click
from multimethod import multimethod

import os
import subprocess
from struct import Struct

import tifffile as tiff
import numpy as np
import cv2


#   definitions ----------------------------------------------------------------
# ==============================================================================

#   global variables -----------------------------------------------------------
LABELS = {}
LABELS_COLOR = {}
FILES = []
TASKS = ['height', 'label', 'msi', 'rgb']

# @uri[reference][bands-world-view-2]: https://dg-cms-uploads-production.s3.amazonaws.com/uploads/document/file/35/DG-8SPECTRAL-WP_0.pdf
# @uri[reference][bands-world-view-3]: http://content.satimagingcorp.com.s3.amazonaws.com/media/pdf/WorldView-3-PDF-Download.pdf
MSI_BAND_FLAG = True
MSI_BAND_IDX = 0
# MSI_BAND_X = []
MSI_BANDS_IDX = 0
MSI_BANDS = [[1, 2, 3], [7, 6, 5], [1, 4, 7], [6, 1, 2], [0, 7, 3], [5, 6, 7]]

#    files and folders ---------------------------------------------------------
FILE_CLOUD_TEMP = os.environ.get('TEMP') + r'\sci-lib\file_cloud_temp.ply'
CCVIEWER = r'C:\Program Files\ccViewer\ccViewer.exe'

#   functions ------------------------------------------------------------------
# ==============================================================================
@multimethod
def show_height(file_path: str):
    img = tiff.imread(file_path)
    img = img/np.max(img[~np.isnan(img)])

    return img

@multimethod
def show_label(file_path: str):
    img = cv2.imread(file_path)
    for label in LABELS_COLOR:
        img[np.where((img == LABELS_COLOR[label][0]).all(axis=2))] = LABELS_COLOR[label][1]
    return img

@multimethod
def show_rgb(file_path: str):
    img = cv2.imread(file_path)

    return img

@multimethod
def show_msi(file_path: str):   
    img = tiff.imread(file_path).astype(float) 
    # img = img / np.max(img[~np.isnan(img)])
    for i in range(0, img.shape[2]):
        img_band = img[:, :, i]
        img[:, :, i] = img_band / np.max(img_band[~np.isnan(img_band)])
    
    if MSI_BAND_FLAG:
        img_bands = img[:, :, MSI_BAND_IDX]
        print('Band: ', MSI_BAND_IDX)
    else:  
        img_bands = img[:, :, MSI_BANDS[MSI_BANDS_IDX]]
        print('Bands: ', MSI_BANDS[MSI_BANDS_IDX])

    return img_bands 

@multimethod
def rs_show(file_idx: int, task: str):

    if task == 'height':
        img = show_height(FILES[LABELS[task]][file_idx])
    elif task == 'label':
        img = show_label(FILES[LABELS[task]][file_idx])
    elif task == 'rgb':
        img = show_rgb(FILES[LABELS[task]][file_idx])
    elif task == 'msi':
        img = show_msi(FILES[LABELS[task]][file_idx])
    else:
        return 1

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.imshow('image', img)

            # cv2.setMouseCallback('overview', click_and_crop)
    return 1

@multimethod
def show_cloud(file_idx: int, task: str):
    if task == 'label':
        img = show_label(FILES[LABELS['label']][file_idx]).astype(float)/256.0
    else:
        img = show_rgb(FILES[LABELS['rgb']][file_idx]).astype(float)/256.0
    
    if 'height' in LABELS:
        height = show_height(FILES[LABELS['height']][file_idx])
        height = height * img.shape[0] / 8
    else:
        height = np.zeros(shape=[img.shape[0], img.shape[1]], dtype=float)       

    write_cloud(img, height, FILE_CLOUD_TEMP)

    subprocess.Popen([CCVIEWER, FILE_CLOUD_TEMP])

    return 1
    
@multimethod
def write_cloud(img: np.ndarray, height: np.ndarray, file_path: str):
    
    point_number = img.shape[0]*img.shape[1]

    file_object = open(file_path, 'w')
    file_object.write('ply\n')
    file_object.write('format binary_little_endian 1.0\n')
    string_object = 'element vertex %i\n' % point_number
    file_object.write(string_object)
    file_object.write('property float x\n')
    file_object.write('property float y\n')
    file_object.write('property float z\n')
    file_object.write('property float blue\n')
    file_object.write('property float green\n')
    file_object.write('property float red\n')
    file_object.write('end_header\n')
    file_object.close()

    idx = 0
    indices = np.zeros((point_number, 2))
    for row in range(0, img.shape[0]):
        for col in range(0, img.shape[1]):
            indices[idx, 0] = row
            indices[idx, 1] = col
            idx = idx + 1

    point_objects = np.concatenate((indices, np.reshape(height, (point_number, 1), order='F'), np.reshape(img, (point_number, 3), order='F')), axis=1)

    point_objects_struct = Struct('6f')
    with open(file_path, 'ab') as file_object:
        for point_object in point_objects.tolist():
            file_object.write(point_objects_struct.pack(*point_object))

    return 1

@multimethod
def prepare_labels_color(file_path: str):

    file_object = open(file_path, 'r')
    labels_color_temp = file_object.read().splitlines()
    file_object.close()

    for i in labels_color_temp:
        labels_config = i.split()

        label_color_old = [int(labels_config[1]), int(labels_config[1]), int(labels_config[1])]
        label_color_new = [int(labels_config[2][1:3], 16), int(labels_config[2][3:5], 16), int(labels_config[2][5:7], 16)]
        LABELS_COLOR[labels_config[0]] = [label_color_old, label_color_new]

    return 1 

@multimethod
def prepare_data_structures(file_path: str, label: str):

    LABELS[label] = len(LABELS)

    file_object = open(file_path, 'r')
    FILES.append(file_object.read().splitlines())
    file_object.close()
    return 1 

#   main -----------------------------------------------------------------------
# ==============================================================================
@click.command()

@click.option('--rgb', default="", type=str, help='RGB')
@click.option('--label', default="", type=str, help='Label')
@click.option('--height', default="", type=str, help='Height')
@click.option('--msi', default="", type=str, help='Msi')

@click.option('--labels_color', default="", type=str, help='Label conversion')
def main(rgb, label, height, msi, labels_color):
    
    global MSI_BAND_IDX, MSI_BANDS_IDX, MSI_BAND_FLAG

    if rgb:
        prepare_data_structures(rgb, 'rgb')
    if label:
        prepare_data_structures(label, 'label')
    if labels_color:
        prepare_labels_color(labels_color)
    if height:
        prepare_data_structures(height, 'height')
    if msi:
        prepare_data_structures(msi, 'msi')        
    labels = [k for k in LABELS]

    idx = 0
    task = 'rgb'
    rs_show(idx, task)

    while True:
        key = cv2.waitKeyEx(1) & 0xFF
        # if key != 255:
        #     print(key)
        if key == ord("q"):
            print('exit')
            cv2.destroyAllWindows()
            return 1
        elif key == ord("d") or key == 32:
            if idx != len(FILES[0]) - 1:
                idx = idx + 1
            rs_show(idx, task)
        elif key == ord("a"):
            if idx != 0:
                idx = idx - 1
            rs_show(idx, task)
        elif key == ord("1"):
            task = labels[0]
            rs_show(idx, task)
        elif key == ord("2"):
            if len(LABELS) > 1:
                task = labels[1]
                rs_show(idx, task)
        elif key == ord("3"):
            if len(LABELS) > 2:
                task = labels[2]
                rs_show(idx, task)
        elif key == ord("4"):
            if len(LABELS) > 3:
                task = labels[3]
                rs_show(idx, task)
        elif key == ord("y"):
            if msi:
                if MSI_BAND_FLAG:
                    if MSI_BAND_IDX > 0:
                        MSI_BAND_IDX = MSI_BAND_IDX - 1
                else:                    
                    if MSI_BANDS_IDX > 0:
                        MSI_BANDS_IDX = MSI_BANDS_IDX - 1
                task = 'msi'
                rs_show(idx, task)
        elif key == ord("x"):
            if msi:
                if MSI_BAND_FLAG:
                    if MSI_BAND_IDX < 6:
                        MSI_BAND_IDX = MSI_BAND_IDX + 1
                else:                    
                    if MSI_BANDS_IDX < len(MSI_BANDS) - 1:
                        MSI_BANDS_IDX = MSI_BANDS_IDX + 1
                task = 'msi'
                rs_show(idx, task)       
        elif key == ord("c"):
            show_cloud(idx, task)
        elif key == 60:
            if msi:            
                if MSI_BAND_FLAG:
                    MSI_BAND_FLAG = False
                else:
                    MSI_BAND_FLAG = True
                task = 'msi'
                rs_show(idx, task)    
        elif key == 32:
            print('Iterate')
                                       
    return 1

if __name__ == '__main__':
    main()
