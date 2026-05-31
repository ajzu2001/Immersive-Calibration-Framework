# PerceptionQuality.msg
# Quality assessment of perception output
# Published by arctos_perception to indicate confidence/quality of detections

std_msgs/Header header

# Overall quality score: 0.0 (poor) to 1.0 (excellent)
float32 overall_score

# Detection confidence: how confident are the detected features?
float32 detection_confidence

# Tracking consistency: 0.0 (lost) to 1.0 (continuously tracked)
float32 tracking_consistency

# Number of valid detections in current frame
uint32 num_detections

# Processing time in milliseconds
uint32 processing_time_ms

# Diagnostics message
string status_message
