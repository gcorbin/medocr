import cv2
import numpy as np


# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


# noise removal
def remove_noise(image):
    return cv2.medianBlur(image, 5)


# thresholding
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


# skew correction
def deskew(image):
    bw = thresholding(get_grayscale(image))
    coords = np.column_stack(np.where(bw < 255))
    center, dimensions, angle= cv2.minAreaRect(coords)
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    im_center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(im_center, angle, 1.0)
    crop_border = 5
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    crop_h = slice(max(int(np.floor(center[0]-dimensions[0]/2.-crop_border)), 0),
                   min(int(np.ceil (center[0]+dimensions[0]/2.+crop_border)), h-1))
    crop_w = slice(max(int(np.floor(center[1]-dimensions[1]/2.-crop_border)), 0),
                   min(int(np.ceil (center[1]+dimensions[1]/2.+crop_border)), w-1))
    cropped = rotated[crop_h, crop_w]
    return cropped
