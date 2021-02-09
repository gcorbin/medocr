import cv2
import numpy as np
import os
from pdf2image import convert_from_path
import  argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    args = parser.parse_args()

    outname, ext = os.path.splitext(args.file)
    images = convert_from_path(args.file, dpi=200, fmt='jpg', grayscale=False, output_folder='work')
    cv_image = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)

    for angle in [0., 1., 2., 5., 10., 15., 20]:
        w = cv_image.shape[1]
        h = cv_image.shape[0]
        hn = int(h * np.cos(np.pi *angle/180.) + w * np.sin(np.pi *angle/180.))
        wn = int(w * np.cos(np.pi *angle/180.) + h * np.sin(np.pi *angle/180.))
        hs = (hn - h)//2
        ws = (wn - w)//2
        img = 255*np.ones((hn, wn, 3))
        img[hs:h+hs, ws:w+ws, :] = cv_image
        M = cv2.getRotationMatrix2D((wn // 2, hn // 2), angle, 1.0)
        rotated = cv2.warpAffine(img, M, (wn, hn), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        cv2.imwrite('{}_{:02.0f}.jpg'.format(outname, angle),rotated)
