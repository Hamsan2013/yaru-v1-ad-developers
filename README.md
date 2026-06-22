🌟 Yaru 1.0 (by AD Developers)
Yaru 1.0 is an automated, high-precision Image-to-3D Model Generator framework designed to parse multi-angle orthographic 2D images and validate them for 3D spatial mesh generation.
By separating the architecture into a clean repository configuration layer and an isolated external execution environment, Yaru 1.0 ensures data integrity, strict structural validation, and automated alignment targeting before the AI engine begins generation.
📋 Foundational Input Rules & Constraints
To achieve clean silhouette masking and artifact-free point cloud generation, the incoming image pipeline enforces three strict rules:
1. Subject-Background Isolation
The Subject: Fully textured and rendered in its native colors.
The Background: Must be absolute solid white or absolute solid black. No gradients, shadows, or secondary colors are accepted.
2. Explicit View Conventions
Images must use exact naming parameters so the engine can explicitly map spatial coordinates without guesswork:
front.png / back.png (Minimum 2-View configuration)
left.png / right.png (Standard 4-View configuration)
top.png / bottom.png (Maximum 6-View configuration)
3. Aspect and Axis Alignment
All view files within a processing bundle must share identical dimensions (e.g., 512x512 pixels).
The target object must be centered perfectly on a shared central axis across all viewsheets.
📂 Repository Blueprint

yaru-v1-ad-developers/
├── .github/
│   └── workflows/
│       └── validate.yml       # Automated push validation pipeline
├── adapters/
│   └── execution_bridge.py    # Manifest export layer for external execution
├── core/
│   ├── __init__.py
│   └── view_gatekeeper.py     # Image matrix & background verification engine
├── requirements.txt           # Environment dependencies (Pillow, NumPy)
└── README.md                  # Project documentation

🚀 Execution Model
Code, configuration rules, and pipeline logic are managed strictly inside this repository, while heavy GPU inference, pixel-to-voxel arrays, and final 3D mesh processing are executed via an external execution pipeline—keeping the repository lightweight, fast, and secure.
