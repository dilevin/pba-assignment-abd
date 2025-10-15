# Physics-Based Animation: Affine Body Dynamics with Penalty Spring Contact
In this assignment you will learn to implement affine body dynamics with penalty springs for simulating stiff objects in contact. 

**WARNING:** Do not create public repos or forks of this assignment or your solution. Do not post code to your answers online or in the class discussion board. Doing so will result in a 20% deduction from your final grade. 

## Checking out the code and setting up the python environment
These instructions use [Conda](https://docs.conda.io/projects/conda/en/stable/user-guide/getting-started.html) for virtual environment. If you do not have it installed, follow the 
instructions at the preceeding link for your operating system

Checkout the code ```git clone git@github.com:dilevin/pba-assignment-abd.git {ROOT_DIR}```, where **{ROOT_DIR}*** is a directory you specify for the source code. 

Next create a virtual environment and install relevant python dependencies install.
```
cd {ROOT_DIR}
conda create -n csc417  python=3.12 -c conda-forge
conda activate csc417
pip install -e . 
```
Optionally, if you have an NVIDIA GPU you might need to install CUDA if you want to use the GPU settings
```
conda install cuda -c nvidia/label/cuda-12.1.0
```
Assignment code templates are stored in the ```{ROOT_DIR}/assginment``` directory. 

**WINDOWS NOTE:** If you want to run the assignments using your GPU you may have to force install torch with CUDA support using 
```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Installation without conda
If you are having too many problems with Conda or prefer to use another package manager, we recommend using [UV](https://docs.astral.sh/uv/getting-started/installation/). If you do not have it installed, follow the instructions at the preceeding link for your operating system

Next, create a virtual environment and install relevant python dependencies:

```
cd {ROOT_DIR}
uv venv
uv pip install -e . 
```

If you opted to use UV, you can run the examples using:

```
uv run python main.py <arguments-for-tests>
```


## Tools You Will Use
1. [NVIDIA Warp](https://github.com/NVIDIA/warp) -- python library for kernel programming
2. [PyTorch](https://pytorch.org/) -- python library for array management, deep learning etc ...
3. [SymPy](https://www.sympy.org/en/index.html) -- python symbolic math package
   
## Running the Assignment Code
```
cd {ROOT_DIR}
python main.py --scene=tests/{SCENE_PYTHON_FILE}.py
```
By default the assignment code runs on the cpu, you can run it using your GPU via:
```
python main.py --scene=tests/{SCENE_PYTHON_FILE}.py --device=cuda
```
Finally, the code runs, headless and can write results to a USD file which can be viewed in [Blender](https://www.blender.org/):
```
python main.py --scene=tests/{SCENE_PYTHON_FILE}.py --usd_output={FULL_PATH_AND_NAME}.usd --num_steps={Number of steps to run}
```
**Occasionaly on windows the assignment will fail to run the first time, but subsequent attempts should work fine**
## Assignment Structure and Instructions
1. You are responsible for implementing all functions found in the [assignments](./assignment) subdirectory.
2. The [tests](./tests) subdirectory contains the scenes, specified as python files,  we will validate your code against.
3. This [Google Drive link](https://drive.google.com/drive/folders/1Vyp4Fk77LIB_EQfGQwTnWpm0KO5Hemai?usp=sharing) contains output from the solution code that you can use to validate your code. The output consists of **USD (Universal Scene Description)** files which contain simulated results. These can be played back in any USD viewer. I use [Blender](https://www.blender.org/). You can output your own simulations as USD files, load both files in blender and examine the simulations side-by-side.
