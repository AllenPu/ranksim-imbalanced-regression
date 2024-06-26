########################################################################################
# Code is based on the LDS and FDS (https://arxiv.org/pdf/2102.09554.pdf) implementation
# from https://github.com/YyzHarry/imbalanced-regression/tree/main/imdb-wiki-dir 
# by Yuzhe Yang et al.
########################################################################################
import os
import shutil
import torch
import logging
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal.windows import triang


class AverageMeter(object):
    def __init__(self, name, fmt=':f'):
        self.name = name
        self.fmt = fmt
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count

    def __str__(self):
        fmtstr = '{name} {val' + self.fmt + '} ({avg' + self.fmt + '})'
        return fmtstr.format(**self.__dict__)


class ProgressMeter(object):
    def __init__(self, num_batches, meters, prefix=""):
        self.batch_fmtstr = self._get_batch_fmtstr(num_batches)
        self.meters = meters
        self.prefix = prefix

    def display(self, batch):
        entries = [self.prefix + self.batch_fmtstr.format(batch)]
        entries += [str(meter) for meter in self.meters]
        logging.info('\t'.join(entries))

    @staticmethod
    def _get_batch_fmtstr(num_batches):
        num_digits = len(str(num_batches // 1))
        fmt = '{:' + str(num_digits) + 'd}'
        return '[' + fmt + '/' + fmt.format(num_batches) + ']'


def query_yes_no(question):
    """ Ask a yes/no question via input() and return their answer. """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    prompt = " [Y/n] "

    while True:
        print(question + prompt, end=':')
        choice = input().lower()
        if choice == '':
            return valid['y']
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def prepare_folders(args):
    folders_util = [args.store_root, os.path.join(args.store_root, args.store_name)]
    if os.path.exists(folders_util[-1]) and not args.resume and not args.pretrained and not args.evaluate:
        if query_yes_no('overwrite previous folder: {} ?'.format(folders_util[-1])):
            shutil.rmtree(folders_util[-1])
            print(folders_util[-1] + ' removed.')
        else:
            raise RuntimeError('Output folder {} already exists'.format(folders_util[-1]))
    for folder in folders_util:
        if not os.path.exists(folder):
            print(f"===> Creating folder: {folder}")
            os.mkdir(folder)


def adjust_learning_rate(optimizer, epoch, args):
    lr = args.lr
    for milestone in args.schedule:
        lr *= 0.1 if epoch >= milestone else 1.
    for param_group in optimizer.param_groups:
        param_group['lr'] = lr


def save_checkpoint(args, state, is_best, prefix=''):
    filename = f"{args.store_root}/{args.store_name}/{prefix}ckpt.pth.tar"
    torch.save(state, filename)
    if is_best:
        logging.info("===> Saving current best checkpoint...")
        shutil.copyfile(filename, filename.replace('pth.tar', 'best.pth.tar'))

def save_checkpoint_per_epoch(args, state, epoch, prefix=''):
    filename = f"{args.store_root}/{args.store_name}/{prefix}ckpt_ep"+str(epoch)+".pth.tar"
    torch.save(state, filename)

def calibrate_mean_var(matrix, m1, v1, m2, v2, clip_min=0.1, clip_max=10):
    if torch.sum(v1) < 1e-10:
        return matrix
    if (v1 == 0.).any():
        valid = (v1 != 0.)
        factor = torch.clamp(v2[valid] / v1[valid], clip_min, clip_max)
        matrix[:, valid] = (matrix[:, valid] - m1[valid]) * torch.sqrt(factor) + m2[valid]
        return matrix

    factor = torch.clamp(v2 / v1, clip_min, clip_max)
    return (matrix - m1) * torch.sqrt(factor) + m2


def get_lds_kernel_window(kernel, ks, sigma):
    assert kernel in ['gaussian', 'triang', 'laplace']
    half_ks = (ks - 1) // 2
    if kernel == 'gaussian':
        base_kernel = [0.] * half_ks + [1.] + [0.] * half_ks
        kernel_window = gaussian_filter1d(base_kernel, sigma=sigma) / max(gaussian_filter1d(base_kernel, sigma=sigma))
    elif kernel == 'triang':
        kernel_window = triang(ks)
    else:
        laplace = lambda x: np.exp(-abs(x) / sigma) / (2. * sigma)
        kernel_window = list(map(laplace, np.arange(-half_ks, half_ks + 1))) / max(map(laplace, np.arange(-half_ks, half_ks + 1)))

    return kernel_window




def cal_frob_norm(y, feat, majs, meds, mino, maj_shot, med_shot, min_shot, maj_shot_nuc, med_shot_nuc, min_shot_nuc):
    bsz = y.shape[0]
    # calculate the frob norm of test on different shots
    maj_index, med_index, min_index = [], [], []
    for i in range(bsz):
        if y[i] in majs:
            maj_index.append(i)
        elif y[i] in meds:
            med_index.append(i)
        else:
            min_index.append(i)
    #
    if len(maj_index) != 0:
        majority = torch.index_select(feat, dim=0, index=torch.LongTensor(maj_index).to(device))
        ma = torch.mean(torch.norm(majority, p='fro', dim=-1))
        ma_nuc = torch.norm(majority, p='nuc')/majority.shape[0]
        #maj_shot = math.sqrt(maj_shot**2 + ma)
        maj_shot.update(ma.item(), majority.shape[0])
        maj_shot_nuc.update(ma_nuc, majority.shape[0])
    if len(med_index) != 0:
        median = torch.index_select(feat, dim=0, index=torch.LongTensor(med_index).to(device))
        md = torch.mean(torch.norm(median, p='fro', dim=-1))
        md_nuc = torch.norm(median, p='nuc')/median.shape[0]
        #med_shot = math.sqrt(med_shot**2 + md)
        med_shot.update(md.item(), median.shape[0])
        med_shot_nuc.update(md_nuc, median.shape[0])
    if len(min_index) != 0:
        minority = torch.index_select(feat, dim=0, index=torch.LongTensor(min_index).to(device))
        mi = torch.mean(torch.norm(minority, p='fro', dim=-1))
        mi_nuc = torch.norm(minority, p='nuc')/minority.shape[0]
        #min_shot = math.sqrt(mi**2 + mi)
        min_shot.update(mi.item(), minority.shape[0])
        min_shot_nuc.update(mi_nuc, minority.shape[0])
    return maj_shot, med_shot, min_shot, maj_shot_nuc, med_shot_nuc, min_shot_nuc
