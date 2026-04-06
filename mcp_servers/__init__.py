"""
Smart Grid MCP Servers — AssetOpsBench extension for power transformers.

Four MCP servers wrapping the four AssetOpsBench tool domains:
  - iot_server:  sensor telemetry and asset metadata
  - fmsr_server: failure-mode-to-sensor-relation mapping (DGA diagnostics)
  - tsfm_server: time-series forecasting and anomaly detection
  - wo_server:   work order creation and management
"""
