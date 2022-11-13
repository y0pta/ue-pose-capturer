from unrealcv.automation import UE4Binary
from unrealcv import client
import PIL.Image as Image
import os, io
import numpy as np


def start_binary(binary_path, w, h, fov):
    '''Starts binary with given params and connect client software for rendering'''
    ini_path = binary_path[:binary_path.rfind('.')] + '/Binaries/Win64/unrealcv.ini'
    config(ini_path, w, h, fov)
    binary = open_binary(binary_path)
    client.connect()
    if not client.isconnected():
        print('Error when connecting with binary. Restart script')
        os._exit(-1)
        os.system('pause')
    else:
        print('Connection with binary established.')
    return binary


def open_binary(binary_path):
    '''Tries to open .exe binary'''
    # Пытаемся открыть бинарник
    print('Path to binary:' + binary_path)
    if os.path.isfile(binary_path):
        binary = UE4Binary(binary_path)
        print('binary is opened successfully')
        binary.start()
    else:
        print('Can not find binary file %s ' % binary_path)
        os.system('pause')
        os._exit(-1)
    return binary


def config(ini_path, w, h, fov):
    try:
        ini = open(ini_path, 'w')
        ini.write(
            '[UnrealCV.Core]\nPort=9000\nWidth=%s\nHeight=%s\nFOV=%sEnableInput=TrueEnableRightEye=False' % (w, h, fov))
        ini.close()
        print('INI-params defined.')
    except IOError:
        print('ERROR.INI-file for binary not found in %s' % ini_path)
        os.system('pause')
        os._exit(-1)


def stop_binary(binary):
    client.disconnect()
    binary.close()


def pose2str(pose):
    pose_str = ''
    for el in pose:
        pose_str += str(el)
        pose_str += ' '
    return pose_str


def render_pose(pose_ue, img_path, depth_path, focal_len, kDepth=5000):
    # print('vset /camera/0/pose ' + pose2str(pose_ue))
    client.request('vset /camera/0/pose ' + pose2str(pose_ue))

    img_name = os.path.split(img_path)[1]
    depth_name = os.path.split(depth_path)[1]
    # print('vget /camera/0/lit ' + 'image%02d.png')
    img = client.request('vget /camera/0/lit ' + img_path)
    if os.path.exists(depth_path):
        os.remove(depth_path)
    save_plane_depth_npy(depth_path, focal_len, kDepth)


def read_npy(res):
    '''Read bytes'''
    return np.load(io.BytesIO(res))


def get_plane_depth(focal_len):
    '''Gets plane depth from unrealcv'''
    res = client.request('vget /camera/0/depth npy')
    ray_dist = read_npy(res)
    # отрезаем дальние объекты
    ray_dist[ray_dist > 10000] = 10000
    return raydist2depthmap(ray_dist, focal_len)


def save_plane_depth_img(path, focal_len, kDepth=5000):
    depth = get_plane_depth(focal_len)
    depth *= kDepth
    depth[depth > np.iinfo(np.uint16).max] = np.iinfo(np.uint16).max

    depth_map = np.zeros(depth.shape, dtype=np.uint16)
    depth_map = np.uint16(depth)

    img = Image.fromarray(depth_map, "I;16")
    img.save(path)


def save_plane_depth_npy(path, focal_len, kDepth=5000):
    depth = get_plane_depth(focal_len)
    np.save(path, depth)


# PointDepth - массив точек с глубинами, f- фокусное расстояние
def raydist2depthmap(PointDepth, focal_len):
    '''Converts ray distanse to plane depth'''
    H = PointDepth.shape[0]
    W = PointDepth.shape[1]
    i_c = np.float(H) / 2 - 1
    j_c = np.float(W) / 2 - 1
    columns, rows = np.meshgrid(np.linspace(0, W - 1, num=W), np.linspace(0, H - 1, num=H))
    DistanceFromCenter = ((rows - i_c) ** 2 + (columns - j_c) ** 2) ** (0.5)
    PlaneDepth = PointDepth / (1 + (DistanceFromCenter / focal_len) ** 2) ** (0.5)
    return PlaneDepth