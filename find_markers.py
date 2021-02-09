import numpy as np
import cv2
import os
import os_utils
import argparse

'''def length_from_two_points(a, b):
    return np.dot()np.sqrt(np.sum(np.power(b - a, 2)))'''

def angle_from_three_points(origin, a, b):
    da = a - origin
    db = b - origin
    return np.arccos( np.dot(da, db) / np.linalg.norm(da,2) / np.linalg.norm(db, 2) )

def check_marker_is_square(marker_corners):
    # markers are listed clockwise, starting from the top left
    # check that all lengths are equal
    lengths = np.array([np.linalg.norm(marker_corners[i, :] - marker_corners[np.mod(i+1, 4)], 2) for i in range(4)])
    mean_length = np.sum(lengths)/4.
    relative_length_deviation = np.max(np.abs(lengths - mean_length))/mean_length

    # check all angles are 90 degrees
    angles  = np.array([angle_from_three_points(marker_corners[i, :], marker_corners[np.mod(i-1, 4)], marker_corners[np.mod(i+1, 4)]) for i in range(4)])
    max_angle_deviation = np.max(np.abs(angles - np.pi/2.))
    if relative_length_deviation > 0.05 or max_angle_deviation > 5.*180./np.pi:
        raise RuntimeError('The marker is not a square, which indicates that the picture was not scanned correctly.')

def extract_ocr_area(image, left_marker, right_marker):
    pos = left_marker[0, :]

    dx = right_marker[1, :] - left_marker[0, :]
    dy = left_marker[3, :] - left_marker[0, :]
    ref_length = 1./9. * np.linalg.norm(dx)

    angle = np.arctan2(dx[1], dx[0]) * 180. / np.pi  # arctan2 takes y coordinate first
    M = cv2.getRotationMatrix2D(tuple(pos.astype(int)), angle, 1.0)
    rotated = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_CONSTANT)
    ocr_area = rotated[int(pos[1]):int(pos[1] + ref_length), int(pos[0]):int(pos[0] + 9. * ref_length), :]
    eps = 5
    cv2.rectangle(ocr_area, (int(1.5 * ref_length+eps), 0+eps), (int(3.5 * ref_length-eps), int(ref_length-eps)), (255, 0, 0), 1)
    cv2.rectangle(ocr_area, (int(3.5 * ref_length+eps), 0+eps), (int(5.5 * ref_length-eps), int(ref_length-eps)), (0, 255, 0), 1)
    cv2.rectangle(ocr_area, (int(5.5 * ref_length+eps), 0+eps), (int(7.5 * ref_length-eps), int(ref_length-eps)), (0, 0, 255), 1)

    ocr_fields = [ocr_area[eps:-eps, int(1.5 * ref_length + eps):int(3.5 * ref_length - eps), :],
                  ocr_area[eps:-eps, int(3.5 * ref_length + eps):int(5.5 * ref_length - eps), :],
                  ocr_area[eps:-eps, int(5.5 * ref_length + eps):int(7.5 * ref_length - eps), :]
                  ]
    return ocr_area


    # #cv2.rectangle(rotated, tuple(pos.astype(int)), tuple((pos + np.array([8*ref_length, ref_length])).astype(int)), (255, 0, 0), 1)
    # int_ref_length = ref_length#int(np.floor(ref_length))
    # ocr_area = rotated[int(pos[1]):int(pos[1]+int_ref_length), int(pos[0]):int(pos[0]+8*int_ref_length), :]
    # eps = 1
    # cv2.rectangle(ocr_area, (int(2 * int_ref_length+eps), 0+eps), (int(4 * int_ref_length-eps), int(int_ref_length-eps)), (255, 0, 0), 1)
    # cv2.rectangle(ocr_area, (int(4 * int_ref_length+eps), 0+eps), (int(6 * int_ref_length-eps), int(int_ref_length-eps)), (0, 255, 0), 1)
    # cv2.rectangle(ocr_area, (int(6 * int_ref_length+eps), 0+eps), (int(8 * int_ref_length-eps), int(int_ref_length-eps)), (0, 0, 255), 1)
    # ocr_fields = [ocr_area[eps:-eps, int(2 * ref_length + eps):int(4 * ref_length - eps), :],
    #               ocr_area[eps:-eps, int(4 * ref_length + eps):int(6 * ref_length - eps), :],
    #               ocr_area[eps:-eps, int(6 * ref_length + eps):int(8 * ref_length - eps), :]
    #               ]
    # return ocr_area
    #
    # ocr_corners = np.stack([pos, pos + 8 * dx, pos + 8 * dx + dy, pos + dy])
    # bounding_rect_ll = np.min(ocr_corners, 0)
    # bounding_rect_ur = np.max(ocr_corners, 0)
    # bounding_rect_dims = bounding_rect_ur - bounding_rect_ll
    # cut_rect_center = (0.5 * bounding_rect_dims)
    # # TODO: check if the cut area lies completely inside the image
    #
    # cut = image[int(bounding_rect_ll[1]):int(bounding_rect_ur[1]), int(bounding_rect_ll[0]):int(bounding_rect_ur[0]), :]
    #
    # angle = np.arctan2(dx[1], dx[0])*180./np.pi  # arctan2 takes y coordinate first
    # M = cv2.getRotationMatrix2D(tuple(cut_rect_center.astype(int)), angle, 1.0)
    # rotated = cv2.warpAffine(cut, M, tuple(bounding_rect_dims.astype(int)), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
    #
    # rh = rotated.shape[0]
    # ocr_area = rotated[int(0.5*rh - 0.5*ref_length):int(0.5*rh + 0.5*ref_length), :, :]
    #
    # eps = 3
    # cv2.rectangle(ocr_area, (int(2*ref_length),0), (int(4*ref_length), int(ref_length)), (255, 0, 0), 1)
    # '''ocr_fields = [ocr_area[eps:-eps, int(2*ref_length+eps):int(4*ref_length-eps), :],
    #               ocr_area[eps:-eps, int(4 * ref_length + eps):int(6 * ref_length - eps), :],
    #               ocr_area[eps:-eps, int(6 * ref_length + eps):int(8 * ref_length - eps), :]
    #               ]'''
    #
    # return ocr_area

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    args = parser.parse_args()

    img = cv2.imread(args.file)

    markers = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    corners, ids, rejected = cv2.aruco.detectMarkers(img, markers)

    '''for mi in range(corners[0].shape[0]):
        center = np.zeros((1, 2))
        for ci in range(4):
            c1 = corners[0][mi, ci, :]
            c2 = corners[0][mi, np.mod(ci+1, 4), :]
            center = center + c1
            cv2.line(img, tuple(c1), tuple(c2), (0, 255, 0), 3)
        center = center / 4
        cv2.circle(img, (int(center[0,0]), int(center[0,1]) ), 3, (255, 0, 0))
        #cv2.putText(img, '{}'.format(ids[0][mi]), (int(center[0,0]), int(center[0,1]) ), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0))
    print(corners[0][0, :, :])
    cv2.line(img, tuple(corners[0][0, 1, :]), tuple(corners[0][0, 2, :]), (0, 255, 0), 3)
    pos, angle, scale = get_trafo_from_marker_corners(corners[0][0, :, :])'''

    if len(ids) != 2:
        raise RuntimeError('There need to be exactly 2 markers, found {}'.format(len(ids)))
    for i in range(len(ids)):
        check_marker_is_square(corners[i][0,:,:])
    if ids[0] != 0 and ids[1] == 0:
        left_marker = corners[0][0, :, :]
        right_marker = corners[1][0, :, :]
    elif ids[1] != 0 and ids[0] == 0:
        left_marker = corners[1][0, :, :]
        right_marker = corners[0][0, :, :]
    else:
        raise  RuntimeError('Exactly one marker must have the id 0, but the found ids were {}'.format(ids))

    ocr_fields = extract_ocr_area(img, left_marker, right_marker)

    cv2.namedWindow('markers', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('markers', 1600, 200)
    cv2.imshow('markers', ocr_fields)
    cv2.waitKey(1)
    input('Press Enter to continue')
    cv2.destroyAllWindows()