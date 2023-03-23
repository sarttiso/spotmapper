import numpy as np
from scipy.spatial import distance_matrix
from scipy.optimize import minimize
import xml.etree.ElementTree as ET
from PIL import Image
from pathlib import Path
import os
import ipywidgets as widgets


class GrainMap:
    """
    Any raster representation of grains.
    """

    def __init__(self, img, extent=[]):
        """
        Parameters:
        -----------
        img : PIL.Image
            image object of raster

        extent : 1d array like
            if known, extent of the raster in the coordinate system of the laser
        """
        self.img = img
        self.extent = extent
        return

    def fit_spots(self, spots):
        """
        Fits spot coordinates to grain centroids detected in raster and resets extents.
        Assumes affine coordinate transformation.

        Paramters:
        ----------
        spots : 2d nd.array
            x, y coordinates of spots as reported from laser software and output by Iolite
        """
        # compute grain centroids
        self.detect_grains()

        def grains2spots(M):
            """
            cost function for mapping from grain coordinate system to spot coordinate system
            """
            A = M[0:4].reshape(2, 2)
            b = M[4:6].reshape(-1, 1)

            spot_coords = np.matmul(A, self.grains) + b

            # take mimimum of pairwise distances between resulting coordinates and provided spots
            # sum the mimimum distances
            min_dists = np.min(distance_matrix(
                spot_coords, spots))  # what is pdist in python
            cost = np.sum(min_dists)
            return cost

        res = minimize(grains2spots,
                       np.array([1, 0, 0, 1, 0,
                                 0]))  # need to find right optimizer

    def detect_grains(self):
        """
        Detects grains within self.img and saves centroids in numpy image coordinates
        """
        self.grains = grain_centroids


def samplespots(img, sample_name):
    """user clicks spots on image, returns spot coordinates

    :param img: _description_
    :type img: _type_
    :param sample_name: _description_
    :type sample_name: _type_
    """
    return


def px2um(xml_path):
    """This function accepts a path to an xml file generated by the mapping tool from
    the xT microscope control program and returns the pixels per micron for each image
    in the xml file.

    Assumes that all images have the same dimensions, and just uses the first one found.
    Alo assumes that the image files are in the same directory as the xml file.

    Args:
        xmlpath (_type_): _description_
    """
    # deal with xml
    xml_tree = ET.parse(xml_path)
    xml_root = xml_tree.getroot()

    # get first image file name
    img_file = xml_root.findall('Images/anyType/FileName')[0].text

    # get first image vertical field height
    height_m = float(xml_root.findall('Images/anyType/VerticalFieldHeight')[0].text)

    # get first image in xml
    img_path = os.path.join(os.path.split(xml_path)[0], img_file)
    # image dimensions
    image = Image.open(img_path)
    width_px, height_px = image.size

    # finally get conversion factor for microns to pixels (just using arbitrarily one of
    # the image dimensions)
    return (height_px/height_m)*1e-6


def xml_widget_generator(xml_path):
    xml_paths = [path for path in Path(xml_path).rglob('*.xml')]
    xml_files = [os.path.basename(path) for path in xml_paths]
    dropdown_widget = widgets.Dropdown(options=list(zip(xml_files, xml_paths)))
    return dropdown_widget


def px2um_widget_generator(xml_root_path):
    """barebones widget for selecting an xml file and returning the pixels per micron
    for user specified micron amounts

    Args:
        xml_root_path (str): base path containing all xml files of interest
    """
    # select xml of interest
    xml_selector_widget = xml_widget_generator(xml_root_path)

    # micron amount to convert to pixels
    micron_widget = widgets.BoundedFloatText(value=20, 
                                             min=0, 
                                             step=1,
                                             description='microns')

    def px2um2(xml_path, micron):
        print(f'pixels per {micron} micron: {micron*px2um(xml_path):1.2f}')

    # output widget
    out_widget = widgets.interactive_output(px2um2,
                                     {'xml_path': xml_selector_widget,
                                      'micron': micron_widget})

    # set up interface
    interactive_widget = widgets.VBox([widgets.HBox([xml_selector_widget, micron_widget]),
                  out_widget])

    return interactive_widget