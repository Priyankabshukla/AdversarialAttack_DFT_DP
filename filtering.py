import os
import numpy as np
from ase import Atoms
from ase.io import read, write
# from deepmd.calculator import DP
from deepmd.infer import DeepPot
from deepmd.infer import calc_model_devi
import matplotlib.pyplot as plt
import json
from random import randint, randrange

# TODO: Make changes as needed.



# path where gsm exploration was performed
working_path='/bgfs/kjohnson/pbs13/DeePMD/reactive_active_learning'

# path to the ensemble of DPs - these DPs were used to perform exploration
dp_main_path = '/bgfs/kjohnson/pbs13/DeePMD/reactive_active_learning/gen-0/train'

# path to submit calculations for relabeling
relabel_dir = '/bgfs/kjohnson/pbs13/DeePMD/reactive_active_learning/gen-0/relabel/level.01/'

# location of all sample VASP files for relabling - you do not need to change these. 
input_path = '/bgfs/kjohnson/pbs13/DeePMD/reactive_active_learning/relabel_inputs'

# upper and lower threshold for configuration filtering - these are for max. froce deviation
upthresh = 1.5
lowthresh = 0.5

dp_paths= []
for i in range(4):
    dp_paths += [DeepPot(f'{dp_main_path}/dp{i}/nh.pb')]


    total_reactions = 6


coord_list = []
boxes_list = []
atypes_list = []
sampled = []

for i in range(0,total_reactions):
    coord_rxn = []
    box_rxn = []
    files = []
    sampled_rxn = []
    rxn_path = working_path+f'/rxn_{i}'
    for j in os.listdir(rxn_path):
        if j.startswith(f'dc_comb'):
            files.append(rxn_path+'/'+j)            
    get_atype = 1
    for k in range(len(files)): # iterate over each dc_comb
        box = []
        coord = []   
        if f'opt_converged_000_ase.xyz' in os.listdir(files[k]):
            pos=read(f'{files[k]}/opt_converged_000_ase.xyz',index=slice(None)) # also include xyz files where gsm fails. 
            sampled_rxn += [files[k]]
            for l in range(len(pos)): # 
                im = pos[l]
                box += [np.array(im.cell).ravel()]
                coord += [im.get_positions().ravel()]                
                if get_atype:
                    a=im.get_chemical_symbols()
                    indexes = np.unique(a, return_index=True)[1]
                    type_map = [a[index] for index in sorted(indexes)]
                    type_file = [type_map.index(x) for x in a]
                    atypes_list += [type_file]
                    get_atype = 0
            if len(coord):
                coord_rxn += [coord]
                box_rxn += [box]
                
    if len(coord_rxn):
        sampled += [sampled_rxn]
        coord_list += [coord_rxn]
        boxes_list += [box_rxn]



filtered_gsm = []
total_gsm_images = []
good_gsm = []
rejected_gsm = []
for j, mdev in enumerate(model_dev_i):
    total_gsm_images += [len(mdev[:,-2])]
    good_gsm += [[i for i,m in enumerate(mdev[:,-2]) if m <= lowthresh]]
    filtered_gsm+=[[i for i,m in enumerate(mdev[:,-2]) if m > lowthresh and m <= upthresh]]
    rejected_gsm+=[[i for i,m in enumerate(mdev[:,-2]) if m > upthresh]]
    plt.hlines(upthresh, -10,200,'grey',alpha=0.5,linestyles='--')
    plt.hlines(lowthresh, -10,200,'grey',alpha=0.5,linestyles='--')
    plt.plot(mdev[:,-2],'o',alpha=0.5,label=f'rxn_{j}')
plt.title(f'Filtered = {len(sum(filtered_gsm,[]))}/{sum(total_gsm_images)}')
plt.legend(frameon=False)
plt.xlabel('image no.')
plt.ylabel('max force dev.')
plt.xlim(-5,150)
plt.ylim(-0.5,11)

config_number = []
# config_number
# just a list of lists to find the structures that we have filtered out. 
for rxn in coord_list:
    count = 0
    config_i = []
    for dccomb in rxn:
        config_i += [list(np.arange(count, count+len(dccomb)))]
        count += len(dccomb)
    config_number += [config_i]

# preparing jobs for relabeling
for i, rxn in enumerate(filtered_gsm):
    ci = config_number[i]
    count = 0
    for f in filtered_gsm[i]:
            for ri, row in enumerate(ci):
                if f in row:
                    rj = row.index(f)
                    rxn_dir = f'{relabel_dir}/rxn.{str(i).zfill(2)}'
                    if f'rxn.{str(i).zfill(2)}' not in os.listdir(relabel_dir):
                        os.mkdir(rxn_dir)
                    job_c = f'{rxn_dir}/{str(count).zfill(4)}'
                    if f'{str(count).zfill(4)}' not in os.listdir(rxn_dir):
                        os.mkdir(job_c)
                    atom = read(f'{sampled[i][ri]}/opt_converged_000_ase.xyz', index=rj)
                    atom.set_cell([10,10,10])
                    write(f'{job_c}/POSCAR', atom)
                    os.system(f'cp {input_path}/INCAR {job_c}/INCAR')
                    os.system(f'cp {input_path}/job.slurm {job_c}/job.slurm')
                    os.system(f'cp {input_path}/POTCAR {job_c}/POTCAR')
                    count += 1
                    
                    break