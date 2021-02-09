import cv2
import os
import os_utils
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--outfolder', '-o', default='.')
    parser.add_argument('--number', '-n', type=int, default=10)
    parser.add_argument('--resolution', '-r', type=int, default=100)
    args = parser.parse_args()

    if args.number <= 0 or args.number > 50:
        raise RuntimeError('We use the aruco predefined dictionary 4x4_50 which has only 50 markers.'
                           ' You cannot have {} markers'.format(args.number))
    os_utils.mkdir_if_nonexistent(args.outfolder)
    markers = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    # markers are patterns on a 6x6 grid (4x4 marker + borders)
    # resolution should be a multiple of 6 to avoid alias
    if args.resolution < 6:
        raise  RuntimeError('The resolution {} is too small (should be at least 6 pixels)'.format(args.resolution))
    resolution = (args.resolution // 6) * 6
    for id in range(args.number):
        marker = cv2.aruco.drawMarker(markers, id, resolution)
        cv2.imwrite(os.path.join(args.outfolder, 'aruco_4x4_50_{:02d}.png'.format(id)), marker)