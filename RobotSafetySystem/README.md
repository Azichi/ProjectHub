# Robot Safety System

Unity project for simulating industrial robot safety scenarios using visual detection and zone monitoring.

## Features
- Integrated Unity robot simulation with real-time perception input via UDP
- Reflective vest detection using OpenCV (Python pipeline)
- Trigger zone monitoring using Unity collider logic
- Fail-safe logic: robot stops only when both danger conditions are true (PLC-inspired AND gate)
- Real-time system with minimal latency between camera input and robot response

## How to Run
1. Open this project in Unity Hub (Unity 2022.x.x)
2. Launch the main scene
3. Run the Python perception module (linked separately)
4. Ensure both systems are on the same network or loopback to simulate UDP stream

## Repo Structure
- `Assets/` – Simulation scenes, scripts, robot models
- `Packages/`, `ProjectSettings/` – Unity config files

> Perception code lives in the [SortifyPerceptionModule](../SortifyPerceptionModule) repo
