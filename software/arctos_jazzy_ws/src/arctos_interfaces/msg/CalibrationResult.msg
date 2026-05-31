# CalibrationResult.msg
# Output from calibration optimization engine
# Published by arctos_calibration after successful calibration

std_msgs/Header header

# Unique session/run identifier
string calibration_id

# Calibration parameters (flattened array)
# Typically DH parameters, base offsets, or joint offsets
float64[] parameters

# Residual error magnitude after optimization
float64 residual_error

# Number of iterations taken by optimizer
uint32 iterations

# Convergence status: 0=not converged, 1=converged, 2=max iterations
uint8 convergence_status

# Execution time in seconds
float64 execution_time
