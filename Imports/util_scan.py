#!/usr/bin/env python
#=============================================================================#
#                                                                             #
# NAME:     util_scan.py                                                      #
#                                                                             #
# PURPOSE:  Routines for processing a model array captured via webcam.        #
#                                                                             #
# REQUIRED: Requires numpy, scipy, matplotlib and PIL/PILLOW                  #
#                                                                             #
# CREDITS:  Cormac R. Purcell (cormac.purcell at mq.edu.au)                   #
#           Roy Truelove      (Macquarie University)                          #
#                                                                             #
#=============================================================================#
#                                                                             #
# The MIT License (MIT)                                                       #
#                                                                             #
# Copyright (c) 2017 Cormac R. Purcell and Roy Truelove                       #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the "Software"),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER      #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
#                                                                             #
#=============================================================================#

import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from PIL import Image

#-----------------------------------------------------------------------------#
def get_available_cameras(max_tested=4):
    """Probe system video capture devices and return list of available camera labels."""
    try:
        import cv2
        cams = []
        for i in range(max_tested):
            cap = cv2.VideoCapture()
            if cap.open(i):
                cams.append("Camera %d" % i)
                cap.release()
        if not cams:
            cams = ["Camera 0"]
        return cams
    except Exception:
        return ["Camera 0"]

#-----------------------------------------------------------------------------#
def scan_to_pixcoords(imgName, eSize=41, threshold_sigma=3.0, minPix=100,
                      cropX=640, cropY=480, flatImgName=None, ax=None,
                      scan_mode="foil", cmap="gray"):
    
    # Open the image, convert to luminance greyscale and then a numpy array
    imgPIL = Image.open(imgName).convert("L")
    rawArr = np.asarray(imgPIL, dtype=float)

    # Determine inversion based on mode:
    # "foil": Aluminum foil dishes on illuminated lightbox (specular reflections, no inversion)
    # "dots": Dark ink dots on white paper (inverts 255 - rawArr)
    # "auto": Auto-detect based on median brightness
    if scan_mode == "dots":
        imgArr = 255.0 - rawArr
    elif scan_mode == "auto":
        if np.median(rawArr) > 128:
            imgArr = rawArr
        else:
            imgArr = rawArr
    else:
        # Default: "foil" mode for illuminated lightbox with aluminum foil dishes
        imgArr = rawArr

    # Subtract the flat image
    if flatImgName:
        flatPIL = Image.open(flatImgName).convert("L")
        flatArr = np.asarray(flatPIL, dtype=float)
        if scan_mode == "dots":
            flatArr = 255.0 - flatArr
        imgArr = imgArr - flatArr
        
    # Crop the image
    Ny, Nx = imgArr.shape
    cropX1 = min([cropX, Nx])
    cropY1 = min([cropY, Ny])
    dx = max(0, Nx - cropX1)
    dy = max(0, Ny - cropY1)
    imgArr = imgArr[dy//2:Ny-dy//2, dx//2:Nx-dx//2]
    rawCrop = rawArr[dy//2:Ny-dy//2, dx//2:Nx-dx//2]
    
    # Remove large-scale background using morphological opening (White Top-Hat filter)
    if eSize >= 3:
        foot = generate_footprint(int(eSize))
        imgErode = ndimage.grey_erosion(imgArr, footprint=foot)
        imgOpen = ndimage.grey_dilation(imgErode, footprint=foot)
        imgBgArr = imgArr - imgOpen
    else:
        imgBgArr = imgArr.copy()

    # Determine the finding threshold
    rms = np.std(imgBgArr)
    zMed = np.median(imgBgArr)
    threshold = zMed + rms * threshold_sigma
    
    # Convert to a binary mask
    imgMskArr = np.copy(imgBgArr)
    imgMskArr[imgBgArr < threshold] = 0
    imgMskArr[imgMskArr >= threshold] = 1
    
    # Find the objects and extract subimages
    imgLabeled, Nobjects = ndimage.label(imgMskArr)
    islands = ndimage.find_objects(imgLabeled)

    # Find the centroids of the islands in pixels
    X_pix = []
    Y_pix = []
    for island in islands:
        if np.sum(imgMskArr[island]) > minPix:
            dy_i, dx_i = island
            x, y = dx_i.start, dy_i.start
            cx, cy = centroid(imgMskArr[island])
            X_pix.append(x + cx)
            Y_pix.append(y + cy)

    # Plot the detected antenna positions
    if ax is not None:
        ax.cla()
        ax.imshow(rawCrop, interpolation="nearest", cmap=cmap, origin='lower')

        # Annotate the detected antennae
        for x, y in zip(X_pix, Y_pix):
            ax.plot(x, y, 'x', ms=19, color="magenta", markeredgewidth=3)
        
        # Format labels and legend
        ax.set_aspect('equal')
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.margins(0.02)
        plt.setp(ax.get_yticklabels(), visible=False)
        plt.setp(ax.get_xticklabels(), visible=False)

    return np.array(X_pix), np.array(Y_pix), imgArr.shape

        
#-----------------------------------------------------------------------------#
def centroid(data):
    h,w = np.shape(data)   
    x = np.arange(0,w)
    y = np.arange(0,h)

    X,Y = np.meshgrid(x,y)

    cx = np.sum(X*data)/np.sum(data)
    cy = np.sum(Y*data)/np.sum(data)

    return cx, cy


#-----------------------------------------------------------------------------#
def generate_footprint(size):
    f = np.ones((size, size))
    yi, xi =np.indices(f.shape, dtype='float')
    d = np.sqrt((yi-size/2.0+0.5)**2.0 + (xi-size/2.0+0.5)**2.0)
    b = np.where(d<(size/2.0), 1, 0)
    return b


#-----------------------------------------------------------------------------#
def write_arrayfile(fileName, X_m, Y_m, Nx, Ny, scale_m, telescope,
                    config, latitude_deg=-20.0, diameter_m=22.0):

    # Convert from pixels to metres
    pixScale_m = scale_m/float(Nx)
    E_m = (X_m - Nx/2.0) * pixScale_m
    N_m = (Ny/2.0 - Y_m) * pixScale_m

    # Write an array definition file
    FH = open(fileName, "w")
    FH.write("telescope = %s\n" % telescope)
    FH.write("config =  %s\n" % config)
    FH.write("latitude_deg = %f\n" % latitude_deg)
    FH.write("diameter_m = %f\n" % diameter_m)
    for i in range(len(E_m)):
        FH.write("%f, %f\n" % (E_m[i], N_m[i]))
    FH.close()

