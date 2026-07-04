### pdsh, clustershell, or slurm

# slurm in torchrec

user needs to apply cluster management tools like slurm to actually run this command on 2 nodes.

export MASTER_ADDR=$(scontrol show hostname ${SLURM_NODELIST} | head -n 1)

srun --nodes=2 ./torchrun_script.sh.
