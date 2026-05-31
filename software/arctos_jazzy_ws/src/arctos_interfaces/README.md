# arctos_interfaces

## Purpose
Central interface definitions package for the Immersive Calibration Framework (ICF) dissertation system.
Defines all ROS 2 message types, service definitions, and action interfaces used across the system.

## Planned Nodes
None - this is a pure definition package (no executables).

## Planned Topics
- Custom message types for:
  - Calibration parameters and poses
  - Virtual environment synchronization
  - Perception system outputs
  - VR interaction events

## Planned Services
- Calibration trigger and status queries
- Environment state synchronization
- Evaluation result submission

## Dissertation Relevance
**Phase 0 Scaffolding**: Serves as the contract layer for all inter-package communication.
Ensures type safety and decoupling in the modular dissertation architecture.
Future phases will define domain-specific messages for calibration, perception, and evaluation.

## Package Structure
```
arctos_interfaces/
├── README.md                 # This file
├── package.xml              # ROS 2 package metadata
├── setup.py / setup.cfg     # Python build configuration
└── arctos_interfaces/       # Source directory (empty in Phase 0)
```

## Next Steps
1. Define message types for calibration parameters
2. Define service interfaces for inter-package communication
3. Update package.xml with proper dependencies
