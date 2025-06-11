# ProjectHub

A curated collection of student-level robotics and computer vision projects. All code is modular and self-contained, with demos and setup instructions.

---

## Contents

- **[LightsOut](LightsOut/)**  
  Unity 2D zombie shooter with scoring system and multiple AI behaviors.  
  ▶️ [Gameplay demo](https://youtu.be/xHVbZc6AC74)

- **[RobotSafetySystem](RobotSafetySystem/)**  
  Unity-based safety simulation with real-time vest detection via UDP from a Python vision module.  
  ▶️ [System demo](https://youtu.be/Jszq-5aXHnU)

- **[SortifyPerceptionModule](SortifyPerceptionModule/)**  
  Python-based computer vision module using OpenCV and YOLOv4-tiny to detect shapes and colors in real time. Supports ROS2 and Unity via UDP.  
  ▶️ [Vision demo](https://youtu.be/h6cor_CGYTA)

Each folder contains a full README with technical breakdowns and usage instructions.

---

## Python Module Setup

```bash
cd SortifyPerceptionModule
pip install -r requirements.txt
```

> Note: The perception module includes YOLO weights and media assets. Clone with [Git LFS](https://git-lfs.com/) enabled to avoid corruption or partial downloads.

---

## License

All projects are released under the MIT License. See [LICENSE](LICENSE).
