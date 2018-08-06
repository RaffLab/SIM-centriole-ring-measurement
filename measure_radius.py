"""
Created on 5 August 2018
@author: Isaac Wong
@email: isaacwongsiushing@gmail.com

The script and all the code within is licensed under MIT License
"""
import os
import argparse
from tqdm import tqdm
from math import ceil

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

from utils.utils import *

eccentricity = 1.2 # Predefined eccentricity

min_radius_red = 0.5 # Predefined lower bound radius (red)
max_radius_red = 2.5 # Predefined upper bound radius (red)

min_radius_green = 3.5 # Predefined lower bound radius (green)
max_radius_green = 4.5 # Predefined upper bound radius (green)

# List for storing information after calculation
channel_red_ma = []
channel_red_mi = []
channel_red_width = []

channel_green_ma = []
channel_green_mi = []
channel_green_width = []

# Initialize mgrid array for the use of later modelling
global xx
global yy

xx, yy = np.mgrid[:28, :28]

if __name__ == "__main__":

    # Parse the argument from the command line and store them in several variables
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', dest='directory', help='directory of files', type=str, required=True)
    parser.add_argument('-rn', dest='channel_red_name', help='name of red channel', type=str, required=True)
    parser.add_argument('-gn', dest='channel_green_name', help='name of green channel', type=str, required=True)
    parser.add_argument('-e', dest='eccentricity', help='eccentricity', type=float, required=False)
    parser.add_argument('-rmin', dest='min_radius_red', help='lower bound of radius in red channel', type=float, required=False)
    parser.add_argument('-rmax', dest='max_radius_red', help='upper bound of radius in red channel', type=float, required=False)
    parser.add_argument('-gmin', dest='min_radius_green', help='lower bound of radius in green channel', type=float, required=False)
    parser.add_argument('-gmax', dest='max_radius_green', help='upper bound of radius in green channel', type=float, required=False)

    arg = parser.parse_args()

    root_path = arg.directory # The path which contain the image information
    channel_red_name = arg.channel_red_name # The name of the protein stain with red color
    channel_green_name = arg.channel_green_name # The name of protein stain with green color

    if arg.eccentricity:
        eccentricity = arg.eccentricity # Eccentricity
    if arg.min_radius_red:
        min_radius_red = arg.min_radius_red # Lower bound radius (red)
    if arg.max_radius_red:
        max_radius_red = arg.max_radius_red # Upper bound radius (red)
    if arg.min_radius_green:
        min_radius_green = arg.min_radius_green # Lower bound radius (green)
    if arg.max_radius_green:
        max_radius_green = arg.max_radius_green # Upper bound radius (green)

    fnames = [os.path.join(root_path, f) for f in os.listdir(root_path) if f.split(".")[-1] == "tif"] # List to store all file

    # Create result path in the directory
    results_path = os.path.join(root_path, "Results")
    if "Results" not in os.listdir(root_path):
        os.mkdir(results_path)

    # Calculate the number of box in all images and to adjust the montage length and depth
    num_boxes = 0
    for i in range(len(fnames)):
        img = read_rgb(fnames[i])
        img_vis = img.copy()
        boxes = detect_boxes(img, color=[0,0,255])
        if not boxes.any():
            print "{} has problems. ".format(fnames[i])
        num_boxes += len(boxes)



    n_col = 20 # Number of centriole in a row
    n_row = int(ceil(num_boxes*2/20.)) # Calculate the number of row required

    # Handling the size of montage and initialize an empty monatge array
    window_size = 28
    montage_size = 30
    montages_red = np.zeros((n_row*montage_size, n_col*montage_size))
    montages_green = np.zeros((n_row*montage_size, n_col*montage_size))

    counter = tick(20) # Initialize a counter object with the limit of 20 i.e. 20 centrioles per row

    for i in tqdm(range(len(fnames))): # Loop over all images

        img = read_rgb(fnames[i])

        img_vis = img.copy()
        boxes = detect_boxes(img, color=[0,0,255]) # Detect blue bounding boxes in an image

        if not boxes.any():
            continue # Skip the current loop if no bounding box is found

        img_vis[:,:,2] = 0 # Remove blue bounding boxes from the copy of the image       
        img_red = img_vis[:,:,0] # Grayscale image with the intensity value as the original red channel
        img_green = img_vis[:,:,1] # Grayscale image with the intensity value as the original green channel
    
        for box in boxes: # Loop over all bounding boxes from an imagees

            x,y = counter.get_ij() # Get the current position in the montage array

            xmin, ymin, xmax, ymax = box # Get the coordinates of the corner of the bounding boxes
            patch_red = img_red[ymin:ymax, xmin:xmax] # Get the patch of the image in red channel
            montages_red[y*montage_size:y*montage_size + montage_size, x*montage_size:x*montage_size + montage_size][1:29,1:29] = patch_red # Append the patch to the montage
            
            # The same logic as the above block of codes
            patch_green = img_green[ymin:ymax, xmin:xmax]
            montages_green[y*montage_size:y*montage_size + montage_size, x*montage_size:x*montage_size + montage_size][1:29,1:29] = patch_green

            counter.increase() # Progress the position in the montage

            #===================================================================================================================================
            #   Ring Gaussian Modelling
            #===================================================================================================================================
            x,y = counter.get_ij()

            # Ring Gaussian modelling of the patch and append the model to the montage
            RG = ring_gaussian(patch_red, xx, yy, (13., 13., 2., 2., 0.01, 2., 300., 100.))
            montages_red[y*montage_size:y*montage_size + montage_size, x*montage_size:x*montage_size + montage_size][1:29,1:29] = RG(xx,yy)

            # Get the radius and thickness from the modellng in the red channel
            channel_red_ma.append(max(RG.ma.value, RG.mi.value)) 
            channel_red_mi.append(min(RG.ma.value, RG.mi.value))
            channel_red_width.append(RG.width.value)
            
            # The same logic as the above block of codes
            RG = ring_gaussian(patch_green, xx, yy, (14., 14., 5., 5., 0.01, 4., 300., 100.))
            montages_green[y*montage_size:y*montage_size + montage_size, x*montage_size:x*montage_size + montage_size][1:29,1:29] = RG(xx,yy)

            channel_green_ma.append(max(RG.ma.value, RG.mi.value))
            channel_green_mi.append(min(RG.ma.value, RG.mi.value))
            channel_green_width.append(RG.width.value)

            counter.increase()
        
    del counter # Delete the counter object

    # Create dataframe from data from modelling
    df = pd.DataFrame({
                   "{} Major Radius".format(channel_red_name): channel_red_ma, \
                   "{} Minor Radius".format(channel_red_name): channel_red_mi, \
                   "{} Ring Width".format(channel_red_name): channel_red_width,\
                   "{} Major Radius".format(channel_green_name): channel_green_ma, \
                   "{} Minor Radius".format(channel_green_name): channel_green_mi, \
                   "{} Ring Width".format(channel_green_name): channel_green_width})

    # Calculate eccentricity and average radius
    df["{} Eccentricity".format(channel_red_name)] = df["{} Major Radius".format(channel_red_name)]/df["{} Minor Radius".format(channel_red_name)]
    df["{} Eccentricity".format(channel_green_name)] = df["{} Major Radius".format(channel_green_name)]/df["{} Minor Radius".format(channel_green_name)]
    df["{} Average Radius".format(channel_red_name)] = (df["{} Major Radius".format(channel_red_name)] + df["{} Minor Radius".format(channel_red_name)])/2.0
    df["{} Average Radius".format(channel_green_name)] = (df["{} Major Radius".format(channel_green_name)] + df["{} Minor Radius".format(channel_green_name)])/2.0

    # Filter away centriole that does not fit the criteria set in the argument
    df = df[(df["{} Eccentricity".format(channel_red_name)] < eccentricity) & \
         (df["{} Eccentricity".format(channel_green_name)] < eccentricity)]
    df = df[(df["{} Average Radius".format(channel_red_name)] > min_radius_red) & (df["{} Average Radius".format(channel_red_name)] < max_radius_red)]
    df = df[(df["{} Average Radius".format(channel_green_name)] > min_radius_green) & (df["{} Average Radius".format(channel_green_name)] < max_radius_green)]

    # Save the data
    df.to_csv(os.path.join(results_path, "raw_data.csv"))
    df.describe().to_csv(os.path.join(results_path, "summary.csv"))

    # Save the parameters tried in this modelling and the results
    with open(os.path.join(results_path, 'Parameters_results.txt'), 'w') as text:
        text.write('Parameters\n')
        text.write('The name of red channel: {0}, The name of green channel: {1}\n'.format(channel_red_name, channel_green_name))
        text.write('The eccentricity threshold: {}\n'.format(eccentricity))
        text.write('The lower bound of radius(red): {0}, The upper bound of radius(red): {1}\n'.format(min_radius_red, max_radius_red))
        text.write('The lower bound of radius(green): {0}, The upper bound of radius(green): {1}\n'.format(min_radius_green, max_radius_green))
        text.write('The number of tif images analyzed: {}\n'.format(len(fnames)))
        text.write('\n\n')
        text.write('Results\n')
        text.write('The mean radius of {0}: {1} px\n'.format(channel_red_name, df["{} Average Radius".format(channel_red_name)].mean()))
        text.write('The mean radius of {0}: {1} px\n'.format(channel_green_name, df["{} Average Radius".format(channel_green_name)].mean()))
    text.close()

    #===================================================================================================================================
    #   Label the centriole that fit the criteria
    #===================================================================================================================================
    filtered = set(df.index)
    rr = montages_red.copy()
    gg = montages_green.copy()

    for i in filtered:
        col = i%10
        row = i//10
        
        rr[row*30: row*30 + 30, col*60: col*60 + 60][0, 0:60] = 255
        rr[row*30: row*30 + 30, col*60: col*60 + 60][0:30,59] = 255
        rr[row*30: row*30 + 30, col*60: col*60 + 60][29,0:60] = 255
        rr[row*30: row*30 + 30, col*60: col*60 + 60][0:30,0] = 255
        
        gg[row*30: row*30 + 30, col*60: col*60 + 60][0, 0:60] = 255
        gg[row*30: row*30 + 30, col*60: col*60 + 60][0:30,59] = 255
        gg[row*30: row*30 + 30, col*60: col*60 + 60][29,0:60] = 255
        gg[row*30: row*30 + 30, col*60: col*60 + 60][0:30,0] = 255

    # Save the montage in the result directory
    plt.imsave(os.path.join(results_path, "{}_montages.png".format(channel_red_name)), rr)
    plt.imsave(os.path.join(results_path,"{}_montages.png".format(channel_green_name)), gg)

    # Create a preview figure to see the distribution of the size of centriole
    fig, (ax1, ax2) = plt.subplots(1, 2)

    sns.boxplot(y="{} Average Radius".format(channel_red_name), data=df, color="white", ax=ax1)
    sns.swarmplot(y="{} Average Radius".format(channel_red_name), data=df, color="black", ax=ax1)

    sns.boxplot(y="{} Average Radius".format(channel_green_name), data=df, color="white", ax=ax2)
    sns.swarmplot(y="{} Average Radius".format(channel_green_name), data=df, color="black", ax=ax2)

    fig.savefig(os.path.join(results_path, 'radius_profile.png'))
    plt.close(fig)
                       





















