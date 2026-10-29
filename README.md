# ROS 2 Robotics Workspace

This workspace contains two robots under active development:

- **PX150 manipulator** — based on the Interbotix PX150 arm. It can be controlled with `ros2_control` and used with MoveIt 2 for motion planning.
- **Simple differential-drive robot** — can be navigated with Nav2 and visualized/simulated in Gazebo Harmonic.

The workspace is still under development, so its packages, setup instructions, and launch workflows may change.

## Packages

### PX150 manipulator

- `custom_interbotix_xarms_description` — PX150 URDF/Xacro model, meshes, controller configuration, and visualization launch files.
- `custom_interbotix_xarms_moveit` — MoveIt 2 configuration and launch files for the PX150.
- `custom_interbotix_xarms_bringup` — Gazebo Sim and MoveIt bringup launch for the PX150.
- `interbotix_arms_controller` — a Python ROS 2 controller node for sending a home command to the arm.

### Differential-drive robot

- `simple_diff_robot_description` — robot URDF/Xacro description and RViz configuration.
- `simple_diff_robot_gz_bringup` — Gazebo Harmonic simulation bringup and ROS-Gazebo bridge configuration.
- `simple_diff_robot_navigation` — navigation and Cartographer launch files for the robot.

## Requirements

Install a ROS 2 distribution compatible with the packages, along with `colcon` and `rosdep`. The relevant robot workflows also require their ROS 2 dependencies, including MoveIt 2, Nav2, Gazebo Harmonic, and the Interbotix message packages used by the manipulator controller.

## Build

Place this repository in the `src` directory of a ROS 2 workspace. From the workspace root, source your ROS 2 installation, install package dependencies, and build:

```bash
source /opt/ros/<ros_distro>/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

Replace `<ros_distro>` with your installed ROS 2 distribution. Source `install/setup.bash` in each new terminal before using the packages.

## PX150 Gazebo and MoveIt simulation

The `custom_interbotix_xarms_bringup` package provides a launch file that starts
the PX150 in Gazebo Sim and then connects its ROS 2 controllers and MoveIt:

```bash
ros2 launch custom_interbotix_xarms_bringup custom_interbotix_gz.launch.py
```

Simulation time is enabled by default. To override it, pass the `use_sim_time`
launch argument:

```bash
ros2 launch custom_interbotix_xarms_bringup custom_interbotix_gz.launch.py use_sim_time:=false
```

The launch starts the system in this order:

1. `robot_state_publisher` publishes the PX150 description. The Xacro is
   expanded with `gz_sim:=true`, which configures the `gz_ros2_control`
   simulation hardware.
2. Gazebo Sim starts, along with a bridge that forwards Gazebo's `/clock` topic
   to ROS. The `use_sim_time` setting is also applied to the launch's nodes and
   inherited by the included MoveIt launch actions.
3. `ros_gz_sim create` spawns the robot as `px150` from `/robot_description`.
4. The `controller_manager` spawners load `arm_controller`,
   `gripper_controller`, and `joint_state_broadcaster` sequentially.
5. MoveGroup and MoveIt RViz start using the PX150 configuration from
   `custom_interbotix_xarms_moveit`.

`gripper_controller` retains its existing name and behavior:
`position_controllers/GripperActionController` controls the `gripper` joint.
The original mention of a `joint_controller` spawner was an error; this launch
uses the configured `gripper_controller` instead.

## Fork and customize

Students are welcome to fork this repository and modify their copy as needed for coursework, experiments, or personal projects.

1. Open this repository on GitHub and select **Fork**. Choose your GitHub account as the destination.
2. Clone your fork into the `src` directory of your ROS 2 workspace:

```bash
cd ~/ros2_ws/src
git clone https://github.com/<your-username>/<repository-name>.git
cd <repository-name>
```

Replace `<your-username>` and `<repository-name>` with the owner and repository name of your fork. If you cloned the fork already, skip the `git clone` command and navigate to its directory.

Create a branch for your changes, then edit and build the packages as needed:

```bash
git switch -c <your-branch-name>
```

Commit and push your changes to your fork whenever you want to save or share them:

```bash
git add .
git commit -m "Describe your changes"
git push -u origin <your-branch-name>
```

You can customize your fork in any way. Changes to your fork do not affect the original repository.

## Git & GitHub Quick Guide for Students

Follow these commands to keep your workspace tidy, stay synchronized with the main class repository, and submit your contributions cleanly.

| Category | Goal | Command | What It Does |
| :--- | :--- | :--- | :--- |
| **Clean Workspace** | Check current state | `git status` | Displays modified, staged, and untracked files. |
| | Discard edits to a file | `git restore <file>` | Undoes uncommitted changes to return a file to its last commit. |
| | Delete untracked build files | `git clean -fd` | Removes untracked files and directories (use `-nd` first to preview). |
| | Clean up local branches | `git branch -d <branch-name>` | Safely deletes a local branch after it has been merged. |
| | Remove obsolete remote references | `git remote prune origin` | Cleans up local references to branches deleted on GitHub. |
| **Link Upstream** | Connect original repo | `git remote add upstream <original-repo-url>` | Links your local clone to the main class repository (run once). |
| | Verify remotes | `git remote -v` | Confirms you have both `origin` (your fork) and `upstream` (class repo). |
| **Update Fork** | Fetch upstream updates | `git fetch upstream` | Downloads commits and branches from the main repo without changing your files. |
| | Update your local `main` | `git checkout main`<br>`git merge upstream/main` | Applies the latest updates from the main class repository into your local branch. |
| | Sync your GitHub fork | `git push origin main` | Pushes updated class commits up to your personal GitHub repository. |
| | Rebase personal branch | `git switch <your-branch>`<br>`git rebase upstream/main` | Moves your working branch forward onto the latest class updates. |
| **Submit a PR** | 1. Create a work branch | `git switch -c feature/<task-name>` | Creates and jumps to an isolated branch for your assignment or feature. |
| | 2. Save your changes | `git add .`<br>`git commit -m "feat: implement arm controller"` | Stages and records your changes with a clear summary message. |
| | 3. Push to your fork | `git push -u origin feature/<task-name>` | Uploads your new branch to your personal fork on GitHub. |
| | 4. Open Pull Request | Via GitHub Web UI or:<br>`gh pr create` | Go to GitHub, click **Compare & pull request**, set the base to upstream, and submit. |

### Conceptual Workflow (Upstream vs. Origin vs. Local)

```text
Main Class Repository (upstream)
                   ▲            │
 Open a PR with    │            │ git fetch upstream
  your changes     │            ▼
                   │     Your Fork on GitHub (origin)
                   │            ▲            │
                   │            │ git push   │ git clone
                   │            │            ▼
                   └──────── Your Local Clone (your machine)
```

---

### Best Practices for Commits

To keep the repository history clean and readable, follow the standard **Conventional Commits** format:

`<type>: <short description in present tense and lowercase>`

#### Common types:
* **`feat:`** A new feature or functionality (e.g., `feat: add trajectory controller for arm`).
* **`fix:`** A bug fix (e.g., `fix: correct lidar sensor orientation in urdf`).
* **`docs:`** Documentation changes only (e.g., `docs: update build instructions in readme`).
* **`refactor:`** Code changes that neither fix a bug nor add a feature (e.g., `refactor: modularize motor node functions`).
* **`test:`** Adding or updating automated tests (e.g., `test: add unit tests for inverse kinematics`).

#### Complete submission example workflow:
```bash
# 1. Ensure your local main branch is up-to-date with upstream
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

# 2. Create a dedicated work branch for your assignment
git switch -c feature/kinematics-controller

# 3. Stage changes and make organized commits
git add .
git commit -m "feat: implement analytical inverse kinematics solver"

# 4. Push the branch to your GitHub fork
git push -u origin feature/kinematics-controller