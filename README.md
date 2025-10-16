# Physics-Based Animation: Affine Body Dynamics with Penalty Spring Contact
In this assignment you will learn to implement affine body dynamics with penalty springs for simulating stiff objects in contact. 
![output](https://github.com/user-attachments/assets/432b7c34-eb58-44ab-811c-223f3004b49f)
**Rendered assignment output played back at high-speed**


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

## Background and Resources
Affine body dynamics was introduced to graphics in this [paper](https://dannykaufman.io/projects/ABD/ABD.pdf) by Lei Lan. The online physics-based animation text [book](https://phys-sim-book.github.io/lec25.3-affine_body_dynamics.html) by Li and colleagues as a good overview of the technique. Penalty springs for contact have a long history in simulation. In this assignment we are using the formulation described in in this [paper](https://graphics.cs.utah.edu/research/projects/vbd/vbd-siggraph2024.pdf)

This assignment draws on previous lectures on [Newton's Method](https://github.com/dilevin/CSC417-physics-based-animation/blob/master/lectures/03-from_energy_to_motion.pdf), [Affine Body Dynamics](https://github.com/dilevin/CSC417-physics-based-animation/blob/master/lectures/04-rigid-and-affine-bodies.pdf) and [Contact Handling](https://github.com/dilevin/CSC417-physics-based-animation/blob/master/lectures/05-affine-bodies-contact.pdf). 

## Affine-Body Kinematics

Affine Bodies are a substitute for Rigid Body mechanics, useful when simulating stiff, effectively rigid objects. The key change is to replace a rigid kinematic map, represented by a rotation and a translation with an affine transformation, represented by a linear transformation and a translation:

<img width="256"  alt="image" src="https://github.com/user-attachments/assets/cff9a281-4d4e-404f-85e6-5e42b194bbdf" />

Flattening transformation $Q(t)$ to a $12\times 1$ vector $\mathbf{q}(t)$ allows us to rewrite the kinematic equation above as 

<img width="256"alt="image" src="https://github.com/user-attachments/assets/db988725-38bb-470d-a5e2-cbd4274df5ea" />

where $J(\mathbf{X})$ is a $3\times 12$ matrix called the kinematic Jacobian. That matrix has the following form (which maintains equivalence with the matrix-valued map):

<img width="512"  alt="image" src="https://github.com/user-attachments/assets/09a7087e-33d6-4f97-b0be-dca3040ff1b8" />

### Kinetic Energy

The kinetic energy of an affine body can be defined using the generalized velocity $\dot{\mathbf{q}}$ as

<img width="256" alt="image" src="https://github.com/user-attachments/assets/95d5b3eb-3edc-47ee-8e2f-7d333e9b0617" />

The mass matrix $M$ consists of volume integrals of second-order monomials. This integral can be converted to a surface integral via the divergence theorem for evaluation using only an input triangle mesh. 

<img width="256"  alt="image" src="https://github.com/user-attachments/assets/f6dbe819-f47b-4034-944a-d1ac1495cfb2" />

The surface integral is evaluated as a sum over triangle integrals. Each triangle integral can be performed using (barycentric integration)[https://en.wikipedia.org/wiki/Barycentric_coordinate_system]

### Potential Energy 
Unlike a true rigid body representation, affine bodies can still deform without additional constraints. To maintain rigid deformations in an affine simulation, we introduce an isometric potential energy which penalizes non rigid deformations. The simplest form of such an energy is the following

<img width="256"  alt="image" src="https://github.com/user-attachments/assets/a2e1b46a-db3e-448b-b1c3-b9b7b4808d16" />,

where $F\in\mathcal{R}^{3\times 3}$ is the deformation gradient of the affine kinematic map, $\kappa$ is a scalar material stiffness (**in this assignment set to $1e8$**)

You should be able to convince yourself that the deformation gradient for an affine body is constant for the entire object and so is the potential energy leading to the simple integration formula

<img width="256" alt="image" src="https://github.com/user-attachments/assets/4097bee1-aa7f-421b-80e9-dde961543e6f" />

## Contact Resolution using Penalty Springs

The second part of this assignment involves implementing contact resolution using penalty springs. Penalty springs are springs that push contacting objects apart if, and only if they are in contact. In this assignment the collision detection algorithm (the part of the simulation that checks if two objects are in contact) has been implemented for you. You are responsible for implementing the penalty spring energy, gradient and hessian for active contacts.

The penalty spring energy is "one-sided" in the sense the energy is $0$ when objects are not interpenetrating and increases quadratically as intepenetration increases. In the assignment this energy is only processed for active contacts, triangle-vertex contacts at which intepenetration is already occuring. This means you can ignore the $max$ operation in your implementations.

<img width="512" alt="image" src="https://github.com/user-attachments/assets/f6da7a7f-b2e6-42b8-ae19-7550f11cf931" />


## Backward Euler for Implicit-Integration
You will implement Backward Euler time integration to time step the affine body system with contact. Backward Euler proceeds by minimizing the following energy using Newton's Method 

<img width="512"  alt="image" src="https://github.com/user-attachments/assets/c21873d9-c9ef-4c37-8aa5-9028183127b0" />

Newton's method proceeds by iteratively evaluating the Hessian and Gradient of the above energy, computing the Newton search direction and then updating the current configuration variables for all objects in the simulation. 

<img width="512" alt="image" src="https://github.com/user-attachments/assets/e11433ba-2372-4014-aabd-2286b9a6ccef" />

In order to choose an approriate step-size, $\alpha$ you will need to implement backtracking line search to satisfy the sufficient decrease condition. Due to the stiff (re quickly increasing) energies present in contacting simulation of this kind, your simulation is likely to fail without a proper line search. Practically it is important to limit the maximum numer of line search iterations (in this assignment we set the max to 5) in order to prevent prohibitvely long simulation times.

## Some Debugging Hints
1. Start by implementing the transform_mesh method. This will cause scenes to be rendered correctly at startup and allow meshes to move during simulation.
1. Next work on the cube_compress.py example which doesn't require any contact forces. 
2. Next debug cube_floor.py which uses contact forces but only between too objects. Finally move on to more complicated examples.
3. The examples in this assignment will run more slowly then the previous assignment due to collision detection overhead. You will notice the simulation slow down once objects come into contact. This is normal. 
4. If you are using Visual Studio Code or Cursor, use the [interactive debugger](https://code.visualstudio.com/docs/python/debugging) and python debugging console.
5. There is a new "Step" button in the interface which advances the simulation by a single time step.
   
## Admissable Code and Libraries
You are allowed to use SymPy for computing formulas for integrals, derivatives and gradients. You are allowed to use any functions in the warp and warp.sparse packages. You ARE NOT allowed to use code from other warp packages like warp.fem. You are not allowed to use any of warps specialized spatial data structures for storing meshes, volumes or doing spatial subdivision. You cannot use code from any other external simulation library.  

## Hand-In
We will collect and grade the assignment using [MarkUs](https://markus.teach.cs.toronto.edu/markus/courses/109)

## Late Penalty
The late penalty is the same as for the course, specified on the main github page.
