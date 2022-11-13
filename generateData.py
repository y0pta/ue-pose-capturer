from utils.readwrite import *
from utils.unrealcv_utils import *
import argparse, os, shutil
from os.path import join as pjoin

IMG_FOLDER = 'images_%ix%i_FOV%i'
IMG_NAME = 'image%05d.png'

DEPTH_FOLDER = 'depths_%ix%i_FOV%i'
DEPTH_NAME = 'depth%05d.npy'
from unrealcv.automation import UE4Binary
from unrealcv import client
import PIL.Image as Image
import os, io
import numpy as np


def start_binary(binary_path, w, h, fov):
    '''
    Starts binary with given params and connect client software for rendering
    '''
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
    '''
    Read bytes
    '''
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

TRAJ_FNAME = 'trajectoryUE.txt'
IBR_FNAME = 'trajectory.txt'
INTERNAL_FNAME = 'intrinsics_FOV%i_%ix%i.txt'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("workdir",
                        help="working directory with .exe", type=str)
    parser.add_argument("model_name",
                        help="name of model for rendering", type=str)
    parser.add_argument("traj",
                        help="name for trajectory file in workdir", type=str)
    parser.add_argument("-W", default=1280,
                        help="width of rendering", type=int, required=False)
    parser.add_argument("-H", default=960,
                        help="height of rendering", type=int, required=False)
    parser.add_argument("--fov", default=80,
                        help="field of view for renders in degrees", type=int, required=False)
    parser.add_argument("-k", default=5000,
                        help="K_depth for depth-maps", type=int, required=False)

    args = parser.parse_args()
    return args


def prepare_workdir(workdir, w, h, fov):
    '''Removes previous content'''
    global DEPTH_FOLDER, IMG_FOLDER, INTERNAL_FNAME
    DEPTH_FOLDER = pjoin(workdir, DEPTH_FOLDER % (w, h, fov))
    IMG_FOLDER = pjoin(workdir, IMG_FOLDER % (w, h, fov))
    INTERNAL_FNAME = INTERNAL_FNAME % (fov, w, h)
    traj = pjoin(workdir, IBR_FNAME)

    if os.path.isdir(DEPTH_FOLDER):
        shutil.rmtree(DEPTH_FOLDER)
    os.makedirs(DEPTH_FOLDER)
    if os.path.isdir(IMG_FOLDER):
        shutil.rmtree(IMG_FOLDER)
    os.makedirs(IMG_FOLDER)
    if os.path.exists(traj):
        os.remove(traj)


def main():
    args = parse_args()
    focal_len = args.W / (2 * math.tan(args.fov * math.pi / 360))

    binary_path = pjoin(args.workdir, 'renderModel', args.model_name + '.exe')
    prepare_workdir(args.workdir, args.W, args.H, args.fov)
    print("Workdir prepared.")

    game = start_binary(binary_path, args.W, args.H, args.fov)
    poses_UE = read_trajectory_UE(pjoin(args.workdir, args.traj))
    print(poses_UE)

    # render and save each pose in trajectory
    i = 0
    for pose_ue in poses_UE:
        print(f"Rendering {i}... {poses_UE}")
        out_d_name = pjoin(DEPTH_FOLDER, (DEPTH_NAME % (i)))
        out_i_name = pjoin(IMG_FOLDER, (IMG_NAME % (i)))

        render_pose(pose_ue,
                    out_i_name,
                    out_d_name,
                    focal_len, args.k)
        i += 1

    stop_binary(game)

    poses_ibr = UE2ibr_poses(poses_UE)
    write_trajectory_ibr(pjoin(args.workdir, IBR_FNAME), poses_ibr)
    print("IBR trajectory recorded.")

    write_internal_calib(pjoin(args.workdir, INTERNAL_FNAME), args.W, args.H, args.fov)
    print("Camera intrinsics recorded.")
    os.system('pause')


if __name__ == "__main__":
    main()