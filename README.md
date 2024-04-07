# Introduction
This repository contains source code for the paper ***Uncertainty-Aware Ship Location Estimation using
Multiple Cameras in Coastal Areas*** to appear in the conference MDM'2024.

In this paper, we propose an algorithm called ***PixelToRegion*** that maps a pixel position in an image to a spatial polygon in lon/lat, and ***PixelToRegion*** extends the classical pinhole imaging model.

Based on ***PixelToRegion***, we propose an algorithm called ***MCbSLE*** that estimates real-world ship locations by taking a set of pixel sets as input. 

# Code Structure

There are 16 folders corresponding to the 16 multi-camera settings in our paper. 

In the folder name, ***2c*** means two cameras and ***3c*** means three cameras. After that, ***1km*** means cameras are located 1 km from each other, and ***2km*** means cameras are located 2 km from each other. ***30d*** means there is a difference of 30 degrees in camera headings. If ***30d*** is missing, then all cameras have the same heading.

Under each folder, there is a file called ***params.csv*** containing the camera configurations. Each row represents one camera.

The proposed algorithms ***PixelToRegion*** and ***MCbSLE*** are implemented in the file ***mcbsle.py***. A simple demo of how to use ***mcbsle.py*** is provided in ***tutorial.ipynb***.

# Contact

[Song WU](https://songwu0001.github.io/) (song.wu.cs@gmail.com)

Feel free to contact me if there are any issues. 

# Experimental Results

Our experimental results are available at [Zenodo](https://zenodo.org/records/10932211).

# Acknowledgement

This publication has been developed under the framework of the ******[Data Engineering for Data Science](https://deds.ulb.ac.be/)****** (DEDS) project that has received funding from the European Union’s Horizon 2020 programme (call identified: H2020-MSCA-ITN-EJD- 2020) under grant agreement No 955895.

# Citation

You are welcome to use our code for research purposes, and do not forget to cite our paper :).

