"""
Created on 5 August 2018
@author: Isaac Wong
@email: isaacwongsiushing@gmail.com

The script and all the code within is licensed under MIT License
"""
import numpy as np
import cv2
from skimage.measure import label, regionprops
from astropy.modeling import Fittable2DModel, Parameter, fitting


#===================================================================================
# Ring Gaussian Class to model centriole using 3DSIM imaging
#===================================================================================
class EllipseRingGaussian(Fittable2DModel):
    # declare parameters that are subject to change and fit into data
    x0 = Parameter(default=13.) # x coordinate of center
    y0 = Parameter(default=13.) # y coordinate of center
    ma = Parameter(default=6.5) # major radius of ellipse
    mi = Parameter(default=6.5) # minor radius of ellipse
    angle = Parameter(default=0.01) # rotation relative to major axis
    width = Parameter(default=4.0) # width of the ring
    amplitude = Parameter(default=2000.) # amplitude of the Gaussian
    background = Parameter(default=50.) # background
    
    # Define the equation of ring Gaussian modelling
    @staticmethod
    def evaluate(x, y, x0, y0, ma, mi, angle, width, amplitude, background):
    	""" method required by Astropy to evaluate the model
    	"""
        theta = np.arctan2(y-y0,x-x0)
        z = background + amplitude * np.exp(-((np.sqrt((x - x0)**2. + (y - y0)**2.) - \
ma * mi / np.sqrt(ma**2 * np.sin(theta + angle)**2. + mi**2 * np.cos(theta + angle)**2.)) / width)**2.)
        return z


#===================================================================================
# Counter that start again when it reaches certain limit
#===================================================================================
class tick():
    def __init__(self, limit = 20):
    	""" initialization method
    	"""
        self.i = 0
        self.j = 0
        self.limit = limit
        
    def increase(self):
        self.i += 1  
        if self.i % self.limit == 0:
            self.i = 0
            self.j += 1
            
    def get_ij(self):
        return self.i, self.j


#===================================================================================
# Counter that start again when it reaches certain limit
#===================================================================================
def read_rgb(imgfile):
    """ Read image file into RGB format
    Args:
    	imgfile: str of the path-to-file name
    Returns:
    	3D np.array of each the last dimension is in the order of RGB
    """
    img = cv2.imread(imgfile)
    return img[:,:,::-1] #Reverse the color channel because OpenCV read rgb as bgr


#===================================================================================
# Counter that start again when it reaches certain limit
#===================================================================================
def detect_boxes(img, color=[255,0,0], window_size=(28,28)):
    """ Detect bounding box of a particular color

    Take in an annotated image and return the coordinates of bounding 
    boxes with certain size

    Args:
        img: 3D np.array of a RGB image
        color: list of [R, G, B] intensity value
        window_size: tuple of the size of a window

    Returns:
        np.array of the shape (n, 4) which n is the number of bounding boxes
        and 4 is the four corners of the window
    """

    # Create mask of each channel
    mask_r = img[:,:,0] == color[0]
    mask_g = img[:,:,1] == color[1]
    mask_b = img[:,:,2] == color[2]
    
    max_dim = img.shape[0]
    
    # mask contain information where we draw the boundary 
    mask = np.logical_and(mask_r, np.logical_and(mask_g, mask_b))
    labelled_mask = label(mask)
    regions = regionprops(labelled_mask)   
    bboxes = []   
    for reg in regions:
        
        y, x = reg.centroid
        y = int(y)
        x = int(x)     
        xmin = x - window_size[1]/2
        xmax = xmin + window_size[1] 
        ymin = y - window_size[0] / 2
        ymax = ymin + window_size[0]
        
        if max_dim > xmin > 0 and max_dim > ymin > 0 and max_dim > xmax > 0 and max_dim > ymax > 0:
            bboxes.append([xmin, ymin, xmax, ymax])
        # stack the array vertically

    if len(bboxes) == 1:
        return np.array(bboxes)
    
    if len(bboxes) == 0:
        return np.array([])
    
    return np.vstack(bboxes)

#===================================================================================
# Ring Gaussian Model fitting
#===================================================================================
def ring_gaussian(patch, xx, yy, parameters):
    """ Create a Ring Gaussian model based on the given parameters

    Args:
        patch: 2D np.array of a grayscale image
        xx: np.mgrid array
        yy: np.mgrid array
        parameters: tuple of (x0, y0, ma, mi, angle, width, amplitute, background)

    Returns:
        EllipseRingGaussian fitting object
    """
    x0, y0, ma, mi, angle, width, amplitude, background = parameters
    p_init = EllipseRingGaussian(x0=x0, y0=y0, ma=ma, mi=mi, \
                             angle=angle, width=width, amplitude=amplitude,\
                             background=background)
    fit_p = fitting.LevMarLSQFitter()
    p = fit_p(p_init, xx, yy, patch)
    return p