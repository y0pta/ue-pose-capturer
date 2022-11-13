import numpy as np
import os, sys, math

IBR_HEADER = 'frame_num   rot_x   rot_y   rot_z   transl_x   transl_y   transl_z\n'


def read_trajectory_UE(fname):
    '''Returns poses read from trajectory file [pitch yaw roll x y z]'''
    if os.path.exists(fname):
        f = open(fname, 'r')
        poses_UE = []
        for line in f:
            # удаляем все ненужные пробелы в координатах
            pose_UE_str = ' '.join([el for el in line.split(' ') if el.strip()])
            pose_UE = np.fromstring(pose_UE_str, dtype=float, sep=' ')
            poses_UE.append(pose_UE)
        return poses_UE

    else:
        print("Cannot find file %s." % fname)
        raise FileNotFoundError


def write_trajectory_ibr(fname, poses_ibr):
    '''Writes file with poses in IBR format'''
    f = open(fname, 'w')
    f.truncate()
    f.write(IBR_HEADER)
    i = 0
    for pose in poses_ibr:
        f.write('{:>4}'.format('%i ' % i))
        i += 1
        for item in pose:
            f.write('{:>10}'.format('%.4f ' % item))
        f.write('\n')
    f.close()


def UE2ibr_poses(poses_UE):
    '''Converts UE to IBR poses'''
    poses_ibr = []

    for pose in poses_UE:
        pose_ibr = np.zeros(6)
        pose_ibr[0] = math.radians(pose[3])
        pose_ibr[1] = math.radians(pose[4])
        pose_ibr[2] = math.radians(pose[5])
        pose_ibr[3] = pose[1] / 100.0
        pose_ibr[4] = -pose[2] / 100.0
        pose_ibr[5] = pose[0] / 100.0
        poses_ibr.append(pose_ibr)
    return poses_ibr


def write_internal_calib(fname, w, h, fov):
    f = w / (2 * math.tan(fov * math.pi / 360))
    file = open(fname, 'w')
    file.write("%i %i\n" % (w, h))

    internal = np.zeros((3, 3))
    internal[0, 0] = internal[1, 1] = f
    internal[0, 2] = w / 2
    internal[1, 2] = h / 2
    internal[2, 2] = 1
    for str in internal:
        for el in str:
            file.write('{:>10}'.format('%.4f' % (el)))
        file.write('\n')
    file.close()