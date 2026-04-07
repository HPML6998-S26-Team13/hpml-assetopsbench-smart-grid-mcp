## Verified Insomnia Configuration (March 25, 2026)

The following was discovered through hands-on testing. The instructor's post above
contains some outdated information.

### Slurm Account & Partitions

The instructor's example uses `--partition=gpu` — **this partition does not exist**.

**Correct settings:**

```bash
--account=edu
--partition=burst    # or short
--qos=burst          # must match partition
```

Check your associations: `sacctmgr show associations user=<UNI> format=Account%20,Partition%20,QOS%30`

### Actual GPU Inventory (from `sinfo`)

The README above lists V100/A100. The actual GPUs on `short`/`burst` partitions are:

| GPU | Per Node | Nodes | Total GPUs |
|-----|----------|-------|------------|
| **H100** | 2 | 2–3 | 4–6 |
| **A6000** | 8 | 13 | 104 |
| **A6000** | 4 | 2 | 8 |
| **L40** | 2 | 3 | 6 |
| **L40S** | 2 | 8 | 16 |

Lab-specific partitions (e.g., `pmg1`, `friesner1`, `morpheus1`) have additional GPUs
but are restricted to their respective groups.

### CUDA Version

- **CUDA 12.9** is installed on compute nodes at `/usr/local/cuda` (symlink to `/usr/local/cuda-12.9/`)
- The `module load cuda/12.3` module is **broken** — it points to `/usr/local/cuda-12.3` which no longer exists (see Ed post #227)
- **Workaround**: Don't use `module load cuda`. Instead, set paths directly in your job script:
  ```bash
  export PATH=/usr/local/cuda/bin:$PATH
  export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
  ```
- `nvcc` version: 12.9, V12.9.86

### cuDNN

- **NOT system-installed** on Insomnia (as of March 25, 2026)
- The `cuda/12.3` module references a cuDNN path at `/usr/local/lib/python3.9/site-packages/nvidia/cudnn`, but this path does not exist
- Ed post #236 confirms: no system-wide `cudnn.h` on the cluster
- Students who report cuDNN "just working" have it in their own conda/pip environments
- **Workaround**: Install locally via pip and point nvcc to it:
  ```bash
  pip install --user nvidia-cudnn-cu12
  # Find the installed paths
  find ~/.local -name "cudnn.h" 2>/dev/null
  find ~/.local -name "libcudnn*" 2>/dev/null
  # Create the missing symlink (pip only installs libcudnn.so.9, linker needs libcudnn.so)
  cd ~/.local/lib/python3.9/site-packages/nvidia/cudnn/lib/
  ln -s libcudnn.so.9 libcudnn.so
  # Compile with explicit paths
  nvcc c3.cu -o c3 -O3 \
    -I$HOME/.local/lib/python3.9/site-packages/nvidia/cudnn/include \
    -L$HOME/.local/lib/python3.9/site-packages/nvidia/cudnn/lib \
    -lcudnn
  # At runtime, also set LD_LIBRARY_PATH
  export LD_LIBRARY_PATH=$HOME/.local/lib/python3.9/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH
  ```

### Login Node vs Compute Nodes

- **Login node**: No GPU, no CUDA toolkit, no `nvidia-smi`. Used for editing, file transfer, and job submission only.
- **Compute nodes** (via `srun`/`sbatch`): Have GPUs, CUDA 12.9, `nvidia-smi`.
- Even **compilation** (`nvcc`) must happen on a compute node.

### Working Slurm Job Template

```bash
#!/bin/bash
#SBATCH --job-name=my_gpu_job
#SBATCH --account=edu
#SBATCH --partition=burst
#SBATCH --qos=burst
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --output=slurm-%j.out

# CUDA setup (don't use module load cuda, it's broken)
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Include cuDNN if needed (pip install --user nvidia-cudnn-cu12)
export LD_LIBRARY_PATH=$HOME/.local/lib/python3.9/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH

# Your commands here
nvcc -O3 my_program.cu -o my_program
./my_program
```

### Interactive GPU Session

For iterative development (compile, run, edit, repeat):

```bash
srun --account=edu --partition=burst --qos=burst --gres=gpu:1 --time=01:00:00 --pty bash
```

### Scratch Directory

```
/insomnia001/depts/edu/users/wax1/
```

### Python / PyTorch / Triton on Insomnia

The system Python 3.9 has an old PyTorch that requires cuDNN 8. To run Python-based
GPU code (e.g., Triton), install your own stack:

```bash
# From login node
pip install --user torch triton typing_extensions --upgrade
```

The `typing_extensions` upgrade is needed because the system version is too old for
current PyTorch. At runtime on compute nodes, set:

```bash
export LD_LIBRARY_PATH=$HOME/.local/lib/python3.9/site-packages/nvidia/cudnn/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

### Requesting Specific GPUs

You can request a specific GPU type:

```bash
srun --pty -t 0-00:30 --gres=gpu:A6000:1 -A edu --partition=burst --qos=burst /bin/bash
srun --pty -t 0-00:30 --gres=gpu:h100:1 -A edu --partition=burst --qos=burst /bin/bash
srun --pty -t 0-00:30 --gres=gpu:l40s:1 -A edu --partition=burst --qos=burst /bin/bash
```

Or just `--gres=gpu:1` to get whatever is available fastest.

Note: different nodes may have different software images. CUDA 12.9 is available on
A6000 and H100 nodes via `/usr/local/cuda`. The `module load cuda/12.3` path may or
may not exist depending on the node.

### SSH Multiplexing (avoid repeated Duo 2FA)

Add to `~/.ssh/config` on your local machine:

```
Host insomnia
  HostName insomnia.rcs.columbia.edu
  User <UNI>
  ControlMaster auto
  ControlPath ~/.ssh/sockets/%r@%h-%p
  ControlPersist 4h
```

Then `mkdir -p ~/.ssh/sockets`. First `ssh insomnia` needs Duo; subsequent
`ssh`/`scp` reuse the connection for 4 hours.

### Relevant Ed Posts

- **#192**: Workaround for broken `module load cuda`
- **#209**: Build/run script for HW3 ("super script")
- **#226**: cuDNN `PREFER_FASTEST` deprecated; use `cudnnFindConvolutionForwardAlgorithm()` instead
- **#227**: CUDA permanent fix, explains the 12.3 to 12.9 symlink issue
- **#236**: Confirms no system cuDNN on Insomnia (student workaround: pip install locally)