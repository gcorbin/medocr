import numpy as np
import cv2
import argparse


class MarkerException(Exception):
    def __init__(self, message):
        super().__init__(message)


def angle_from_three_points(origin, a, b):
    da = a - origin
    db = b - origin
    return np.arccos(np.dot(da, db) / np.linalg.norm(da, 2) / np.linalg.norm(db, 2))


def check_marker_is_square(marker_corners):
    # markers are listed clockwise, starting from the top left
    # check that all lengths are equal
    lengths = np.array([np.linalg.norm(marker_corners[i, :] - marker_corners[np.mod(i+1, 4)], 2) for i in range(4)])
    mean_length = np.sum(lengths)/4.
    relative_length_deviation = np.max(np.abs(lengths - mean_length))/mean_length

    # check all angles are 90 degrees
    angles = np.array([angle_from_three_points(marker_corners[i, :], marker_corners[np.mod(i-1, 4)], marker_corners[np.mod(i+1, 4)]) for i in range(4)])
    max_angle_deviation = np.max(np.abs(angles - np.pi/2.))
    if relative_length_deviation > 0.05 or max_angle_deviation > 5.*180./np.pi:
        raise MarkerException('The marker is not a square, which indicates that the picture was not scanned correctly.')


def extract_ocr_fields(image, left_marker, right_marker):
    pos = left_marker[0, :]

    dx = right_marker[1, :] - left_marker[0, :]
    dy = left_marker[3, :] - left_marker[0, :]
    ref_length = 1./9. * np.linalg.norm(dx)

    angle = np.arctan2(dx[1], dx[0]) * 180. / np.pi  # arctan2 takes y coordinate first
    pos_h = np.matrix([[pos[0]], [pos[1]], [1.]])
    M = cv2.getRotationMatrix2D((image.shape[0]//2, image.shape[1]//2), angle, 1.0)
    pos_h_rot = np.matrix(M) * pos_h
    pos_rot = pos_h_rot[:2]
    rotated = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_CONSTANT)
    ocr_area = rotated[int(pos_rot[1]):int(pos_rot[1] + ref_length), int(pos_rot[0]):int(pos_rot[0] + 9. * ref_length), :]
    eps = 5

    '''cv2.rectangle(ocr_area, (int(1.5 * ref_length+eps), 0+eps), (int(3.5 * ref_length-eps), int(ref_length-eps)), (255, 0, 0), 1)
    cv2.rectangle(ocr_area, (int(3.5 * ref_length+eps), 0+eps), (int(5.5 * ref_length-eps), int(ref_length-eps)), (0, 255, 0), 1)
    cv2.rectangle(ocr_area, (int(5.5 * ref_length+eps), 0+eps), (int(7.5 * ref_length-eps), int(ref_length-eps)), (0, 0, 255), 1)'''
    '''cv2.rectangle(rotated, (int(pos_rot[0]), int(pos_rot[1])), (int(pos_rot[0] + 9. * ref_length), int(pos_rot[1] + ref_length)),
                  (255, 0, 0), 3)'''

    ocr_fields = [ocr_area[eps:-eps, int(1.5 * ref_length + eps):int(3.5 * ref_length - eps), :],
                  ocr_area[eps:-eps, int(3.5 * ref_length + eps):int(5.5 * ref_length - eps), :],
                  ocr_area[eps:-eps, int(5.5 * ref_length + eps):int(7.5 * ref_length - eps), :]
                  ]
    return ocr_fields


def find_markers(img):
    markers = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    corners, ids, rejected = cv2.aruco.detectMarkers(img, markers)
    if ids is None:
        raise MarkerException('There need to be exactly 2 markers, found 0')
    if len(ids) != 2:
        raise MarkerException('There need to be exactly 2 markers, found {}'.format(len(ids)))
    for i in range(len(ids)):
        check_marker_is_square(corners[i][0,:,:])
    if ids[0] != 0 and ids[1] == 0:
        left_id = ids[0]
        left_marker = corners[0][0, :, :]
        right_marker = corners[1][0, :, :]
    elif ids[1] != 0 and ids[0] == 0:
        left_id = ids[1]
        left_marker = corners[1][0, :, :]
        right_marker = corners[0][0, :, :]
    else:
        raise  MarkerException('Exactly one marker must have the id 0, but the found ids were {}'.format(ids))
    return left_marker, right_marker, int(left_id[0])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    args = parser.parse_args()

    img = cv2.imread(args.file)

    left_marker, right_marker, left_id = find_markers(img)

    ocr_fields = extract_ocr_fields(img, left_marker, right_marker)

    ocr_fields_stacked = np.concatenate(ocr_fields, 1)
    cv2.namedWindow('markers', cv2.WINDOW_KEEPRATIO)
    cv2.moveWindow('markers', 0, 0)
    cv2.resizeWindow('markers', 1600, 200)
    cv2.imshow('markers', ocr_fields_stacked)
    cv2.waitKey(1)
    input('Press Enter to continue')
    cv2.destroyAllWindows()
