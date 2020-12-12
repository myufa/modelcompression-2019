import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.cluster import KMeans
from scipy.sparse import csc_matrix, csr_matrix
import pdb
import datetime
from .kmeans import lloyd
import matplotlib.pyplot as plt
from torch.utils.tensorboard import SummaryWriter

def get_all_weights(model):
    weights = []

    if len(list(model.children())) != 0:
        for l in model.children():
            weights += get_all_weights(l)
    else:
        for p in model.parameters():
            if len(p.data.size()) != 1: # Avoid bias parameters
                weights += list(p.cpu().data.abs().numpy().flatten())

    return weights

def gen_masks_for_layer(model, threshold, layerwise_thresh=False):
    # generate mask
    for p in model.parameters():
        if len(p.data.size()) != 1:
            if layerwise_thresh:
                #"""
                #FROM:
                #https://github.com/mightydeveloper/Deep-Compression-PyTorch/blob/a3ace3156b50bb29dd9d5e8498bdc79fe7aaac8c/net/prune.py#L39

                s = 0.25
                threshold = np.std(p.data.cpu().numpy()) * s

            pruned_inds = p.data.abs() > threshold
            return pruned_inds.float()
    
def gen_masks_recursive(model, threshold, layerwise_thresh=False):
    masks = []
    
    for module in model.children():
        if 'Masked' not in str(type(module)):
            #print("Skipping masking of layer: ", module)
            continue
        if len(list(module.children())) != 0:
            masks.append(gen_masks_recursive(module, threshold, layerwise_thresh=layerwise_thresh))
        else:
            masks.append(gen_masks_for_layer(module, threshold, layerwise_thresh=layerwise_thresh))
    
    return masks


def quantize_k_means(model, bits=5, show_figures=False):
    for module in model.children():
        if 'List' in module.__class__.__name__ or 'Sequential' in module.__class__.__name__ or 'Bottleneck' in module.__class__.__name__:
            quantize_k_means(module, bits=bits, show_figures=show_figures)
            continue
        if 'weight' not in dir(module):
            continue
        if 'BatchNorm' in module.__class__.__name__:
            continue
        if 'MaxPool' in module.__class__.__name__:
            continue   

        dev = module.weight.device
        weight = module.weight.data
        original_shape = weight.shape
        weight = weight.reshape(-1, 1)
        n_clusters = (int(weight.nelement() / 300000) + 1)*2**(bits)
        cluster_labels, centroids = lloyd(weight, n_clusters)
        centroid_weights = centroids[cluster_labels]

        weight = torch.where(weight == 0, weight, centroid_weights).reshape(original_shape)

        if show_figures:
            writer = SummaryWriter()
            fig, ax = plt.subplots()
            writer.add_histogram(f'Quantized weights {module}', weight)
            # for i in range(n_clusters):
            #     cpu_labels = cluster_labels.cpu().numpy()
            #     cpu_weight = weight.cpu().numpy()
            #     indices = np.where(cpu_labels == i)[0]
            #     selected = cpu_weight[indices]
            #     ax.plot(selected, '.', label=str(i))
            # plt.show()


        module.weight.data = weight.reshape(original_shape)
        # module.weight.register_hook(gen_param_hook(cluster_labels, dev, n_clusters))

def gen_param_hook(c_labels, dev, n_clusters):
    
    def hook(grad):
        grad_original_shape = grad.shape
        reshape_start_time = datetime.datetime.now()
        grads = grad.reshape(-1, 1)
        grad_indices = torch.arange(0, grads.nelement(), device=dev)
        updates = torch.zeros(n_clusters, layout=c_labels.layout, device=dev, dtype=torch.float)
        reshape_end_time = datetime.datetime.now()

        # print(f"Reshape took: {reshape_end_time - reshape_start_time}")

        start_time = datetime.datetime.now()

        enumartion_start_time = datetime.datetime.now()
        updates[c_labels[grad_indices]] += grads[grad_indices].flatten()
        enumeration_end_time = datetime.datetime.now()

        # print(f"Enumeration time took: {enumeration_end_time - enumartion_start_time}")

        updated_grads = updates[c_labels].reshape(grad_original_shape)
        end_time = datetime.datetime.now()
        # print(f"Weight vector with {updated_grads.nelement()} gradients took {end_time - start_time} to cluster gradient updates.")

        return updated_grads
    
    return hook

def weight_prune(model, pruning_perc, layerwise_thresh=False):
    '''
    Prune pruning_perc% weights globally (not layer-wise)
    arXiv: 1606.09274
    '''    
    all_weights = get_all_weights(model)
    threshold = np.percentile(np.array(all_weights), pruning_perc)
    return gen_masks_recursive(model, threshold, layerwise_thresh=layerwise_thresh)


def prune_rate(model, verbose=True):
    """
    Print out prune rate for each layer and the whole network
    """
    total_nb_param = 0
    nb_zero_param = 0

    layer_id = 0

    for parameter in model.parameters():

        param_this_layer = 1
        for dim in parameter.data.size():
            param_this_layer *= dim
        total_nb_param += param_this_layer

        # only pruning linear and conv layers
        if len(parameter.data.size()) != 1:
            layer_id += 1
            zero_param_this_layer = \
                np.count_nonzero(parameter.cpu().data.numpy()==0)
            nb_zero_param += zero_param_this_layer

            if verbose:
                print("Layer {} | {} layer | {:.2f}% parameters pruned" \
                    .format(
                        layer_id,
                        'Conv' if len(parameter.data.size()) == 4 \
                            else 'Linear',
                        100.*zero_param_this_layer/param_this_layer,
                        ))
    pruning_perc = 100.*nb_zero_param/total_nb_param
    if verbose:
        print("Final pruning rate: {:.2f}%".format(pruning_perc))
    return pruning_perc
