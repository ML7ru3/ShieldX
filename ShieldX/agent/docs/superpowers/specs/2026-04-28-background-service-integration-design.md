# Background Service Integration Design

## Overview
This document outlines the architecture for integrating the Intelligent Security Agent as a native background service across Windows and Linux. The core application logic remains platform-agnostic, while platform-specific entry points manage the OS integration.

## Architecture

### 1. Service Entry Points (`src/service/`)
A new Service Launcher component will act as the OS-specific entry point for the core `Orchestrator`.

*   **Windows (`src/service/win_service.py`):**
    *   Utilizes the `pywin32` library, specifically `win32serviceutil.ServiceFramework`.
    *   Registers with the Windows Service Control Manager (SCM).
    *   Handles `SvcDoRun` (starts the `Orchestrator`) and `SvcStop` (signals the `Orchestrator` to shut down gracefully).
    *   Configured for automatic startup on boot.

*   **Linux (`src/service/linux_systemd.py` & `security-agent.service`):**
    *   Employs a standard `systemd` unit file installed to `/etc/systemd/system/`.
    *   Executes a simple Python launcher script that instantiates and runs the `Orchestrator`.
    *   Systemd handles backgrounding, automatic restarts, and log capture (`journalctl`).

### 2. Cross-Platform Desktop Notifications
Background services (Session 0 on Windows, root daemon on Linux) cannot directly display UI elements to the logged-in user. We will implement OS-native notification bridges to handle this:

*   **Windows:** We will use the `win32ts` (Terminal Services) API, specifically `WTSSendMessage`, to send a native OS message box to the active user session (Session 1+). This avoids needing a separate UI application.
*   **Linux:** We will execute `notify-send` via the `subprocess` module, explicitly targeting the active user's DBUS session (e.g., finding the `DBUS_SESSION_BUS_ADDRESS` for the logged-in user).

## Error Handling
*   **Linux:** The `systemd` unit file will be configured to restart the service automatically if the Python process exits unexpectedly.
*   **Windows:** The Service Control Manager (SCM) will be configured to restart the service on failure.

## Testing
*   **Linux:** Create and verify the `systemd` service file structure and commands.
*   **Windows:** Verify the `win32serviceutil` implementation handles the SCM lifecycle correctly.
