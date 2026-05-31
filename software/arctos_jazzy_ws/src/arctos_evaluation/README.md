# arctos_evaluation

## Purpose
Evaluation and validation framework for the ICF dissertation system.
Measures calibration quality, generates metrics, and produces analysis reports.

## Planned Nodes
- `evaluation_engine`: Main evaluation coordinator
- `metric_calculator`: Computes accuracy metrics
- `report_generator`: Creates evaluation reports

## Planned Topics
**Subscribers:**
- `/calibration/results` (from arctos_calibration)
- `/perception/poses` (from arctos_perception)

**Publishers:**
- `/evaluation/metrics` (custom EvaluationMetrics messages)
- `/evaluation/reports` (std_msgs/String)

## Dissertation Relevance
**Critical for Validation**: Provides empirical evidence of calibration effectiveness.
Generates quantitative results for dissertation's evaluation chapter.
Enables reproducibility and comparison with baseline methods.

## Package Structure
```
arctos_evaluation/
├── README.md                      # This file
├── package.xml                    # Dependencies: numpy, pandas, matplotlib
├── arctos_evaluation/
│   ├── __init__.py
│   ├── evaluation_node.py        # Main evaluation node
│   └── metrics/                   # Placeholder for metric implementations
└── setup.py / setup.cfg\n```

## Next Steps
1. Define evaluation metrics (positional error, orientation error, etc.)
2. Implement statistical analysis tools
3. Create visualization and report generation
4. Add comparison mode for baseline calibration methods
