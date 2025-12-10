# Govee VMA Integration

This integration connects Home Assistant with Krisinformation VMA alerts
and triggers visual notifications using Govee lights.

## Overview

The integration periodically polls the Krisinformation API for VMA alerts.
When data is updated, a predefined light pattern is executed on all
configured Govee devices.

## Architecture

- `api.py` – Fetches VMA alert data from Krisinformation
- `coordinator.py` – Handles periodic updates and processing of alerts
- `light_controller.py` – Executes light patterns across devices
- `govee_coordinator.py` – Communicates with the Govee API
- `config_flow.py` – UI-based setup and configuration

## Configuration

The integration is set up via the Home Assistant UI and requires
a valid Govee API key.

## Development Notes

This folder contains only integration logic.
Tests and user documentation are maintained separately.
