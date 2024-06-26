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



    
def shot_count(train_labels, many_shot_thr=100, low_shot_thr=20):
    #
    train_labels = np.array(train_labels).astype(int)
    #
    train_class_count = []
    #
    maj_class, med_class, min_class = [], [], []
    #
    for l in np.unique(train_labels):
        train_class_count.append(len(
            train_labels[train_labels == l]))
    #
    for i in range(len(train_class_count)):
        if train_class_count[i] > many_shot_thr:
            maj_class.append(np.unique(train_labels)[i])
        elif train_class_count[i] < low_shot_thr:
            min_class.append(np.unique(train_labels)[i])
        else:
            med_class.append(np.unique(train_labels)[i]) 
    #
    return maj_class, med_class, min_class






def shot_reg(label, pred, maj, med, min):
    # how many preditions in this shots
    pred_dict = {'maj':0, 'med':0, 'min':0}
    # how many preditions from min to med, min to maj, med to maj, min to med
    pred_label_dict = {'min to med':0, 'min to maj':0, 'med to maj':0, 'med to min':0, 'maj to min':0, 'maj to med':0}
    #
    pred = int_tensors(pred)
    #
    labels, preds = np.stack(label), np.floor(np.hstack(pred))
    #dis = np.floor(np.abs(labels - preds)).tolist()
    bsz = labels.shape[0]
    #    
    for i in range(bsz):
        k_pred = check_shot(preds[i], maj, med, min)
        k_label = check_shot(labels[i], maj, med, min)
        if k_pred in pred_dict.keys():
            pred_dict[k_pred] = pred_dict[k_pred] + 1
        pred_shift = check_pred_shift(k_pred, k_label)
        if pred_shift in pred_label_dict.keys():
            pred_label_dict[pred_shift] = pred_label_dict[pred_shift] + 1
    return pred_dict['maj'], pred_dict['med'], pred_dict['min'], \
        pred_label_dict['min to med'], pred_label_dict['min to maj'], pred_label_dict['med to maj'],pred_label_dict['med to min'],pred_label_dict['maj to min'],pred_label_dict['maj to med']


def check_shot(e, maj, med, min):
    if e in maj:
        return 'maj'
    elif e in med:
        return 'med'
    else:
        return 'min'
    


def int_tensors(pred):
    pred = torch.Tensor(pred).unsquueze(-1)
    zero = torch.zeros_like(pred)
    one = torch.ones_like(pred)
    diff = pred - torch.floor(pred)
    diff = torch.where(diff > 0.5, one, diff)
    diff = torch.where(diff < 0.5, zero, diff)
    pred = torch.floor(pred) + diff
    pred = torch.clamp(pred, 0, 100)
    pred = pred.squeeze().tolist()
    return pred
    
# check reditions from min to med, min to maj, med to maj
def check_pred_shift(k_pred, k_label):
    if k_pred is 'med' and k_label is 'min':
        return 'min to med'
    elif k_pred is 'maj' and k_label is 'min':
        return 'min to maj'
    elif k_pred is 'maj' and k_label is 'med':
        return 'med to maj'
    elif k_pred is 'min' and k_label is 'med':
        return 'med to min'
    elif k_pred is 'min' and k_label is 'maj':
        return 'maj to min'
    elif k_pred is 'med' and k_label is 'maj':
        return 'maj to med'
    else:
        return 'others'
      