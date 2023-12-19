import os
import json
from random import randint, randrange

main_path = '/bgfs/kjohnson/pbs13/DeePMD/reactive_active_learning'
current_gen=1 # if current gen is 0 then copy input.json from main path
for i in range(4):
	if f'dp{i}' not in os.listdir():
		os.mkdir(f'dp{i}')
	if current_gen:
		os.system(f'cp {main_path}/gen-{current_gen-1}/train/dp{i}/input.json dp{i}/')
	#os.system(f'cp {main_path}/dp.slurm dp{i}/job.slurm')

	path=f'dp{i}/input.json'
	levels = [x for x in sorted(os.listdir(f'../../gen-{current_gen-1}/relabel/')) if x.split('.')[0] == 'level']
	deepmd_data_curr = []
	for level in levels:
		deepmd_data_curr += os.popen(f'cat ../../gen-{current_gen-1}/relabel/{level}/deepmd_data_path.dat').read().split('\n')[:-1]

	with open(path, 'r+') as f:
		data = json.load(f)
		app_sys =  data["training"]["training_data"]["systems"] + deepmd_data_curr
		data["model"]["fitting_net"]["seed"] = randint(1e6, 1e7)
		data["model"]["descriptor"]["seed"] = randint(1e6, 1e7)
		data["model"]["descriptor"]["sel"] = [92, 46]
		data["model"]["descriptor"]["rcut"] = 6.0
		data["model"]["descriptor"]["rcut_smth"] = 2.0
		data["model"]["descriptor"]["neuron"]=[120,120,120]
		data["model"]["fitting_net"]["neuron"]=[240,240,240]
		data["training"]["seed"] = randint(1e6, 1e7)
		data["training"]["training_data"]["systems"] = app_sys
		data["training"]["stop_batch"] = 1000000
		data["training"]["training_data"]["batch_size"] = "auto"

	os.remove(path)
	with open(path, 'w') as f:
	    json.dump(data, f, indent = 4)
	os.chdir(f'dp{i}')
	os.system('sbatch job.slurm') # remember to change the init model in the job slrum
	os.chdir('../')

	



