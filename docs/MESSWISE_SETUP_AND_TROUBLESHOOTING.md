# MessWise Beginner Setup, Local Startup & Troubleshooting Guide

> **Document Version:** 2.0.0  
> **Target Audience:** Developers, Hackathon Reviewers, Evaluators & Students  
> **Operating Systems Supported:** Windows 10/11 (PowerShell), macOS (zsh), Linux (bash)  

---

## 1. Prerequisites & Environment Check

Before launching MessWise, confirm that your system satisfies the required runtimes.

### 1.1 Minimum System Requirements
- **Python:** Version 3.11 or higher (Python 3.11, 3.12, 3.13, 3.14).
- **Node.js:** Version 18.0.0 or higher (LTS recommended).
- **npm:** Version 9.0.0 or higher.
- **Git:** Version 2.30 or higher.

### 1.2 Verification Commands
Open a terminal in the repository root directory (`Messwise/`) and run:
```bash
# Check Python version
python --version

# Check Node.js and npm versions
node --version
npm --version

# Check Git
git --version
```

---

## 2. Step-by-Step Local Setup from Zero

Follow these steps to launch the entire platform in separate dedicated terminals.

---

### Step 1: Open the Project in VS Code
1. Launch **Visual Studio Code**.
2. Click **File $\rightarrow$ Open Folder...** and select the root directory:
   `c:\Users\kotha\Desktop\Messwise\Messwise`
3. Confirm that the top-level folder contains `PLAN.md`, `README.md`, `requirements.txt`, `api/`, `frontend/`, `messwise/`, and `data/`.

---

### Step 2: Set Up & Activate the Python Virtual Environment
MessWise includes a pre-configured Python virtual environment located in the parent folder or root directory (`.venv`).

#### On Windows (PowerShell):
```powershell
# If .venv exists in parent or root, activate it:
& "..\.venv\Scripts\Activate.ps1"

# Or if .venv is inside the repository:
& ".\.venv\Scripts\Activate.ps1"

# Verify active Python interpreter
Get-Command python | Select-Object -ExpandProperty Source
```

#### On Linux / macOS (bash / zsh):
```bash
source ../.venv/bin/activate
# or
source .venv/bin/activate

which python
```

*If dependencies need to be installed from scratch:*
```bash
pip install -r requirements.txt
```

---

### Step 3: Launch the FastAPI Backend Service (Terminal 1)
The backend REST API provides all data persistence, forecasting, optimization, and analytics endpoints.

1. Open **Terminal 1** in VS Code.
2. Ensure the virtual environment is activated.
3. Start the Uvicorn server:

```powershell
# Set PYTHONPATH so messwise modules are discoverable
$env:PYTHONPATH = "."

# Start FastAPI on port 8000 with auto-reload
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Verify Backend is Running:
- Open your browser and navigate to:
  **`http://127.0.0.1:8000/health`**
- You should see:
  ```json
  {"status":"healthy","app":"MessWise","version":"0.1.0","phase":1,...}
  ```
- Access the interactive **Swagger UI** documentation at:
  **`http://127.0.0.1:8000/docs`**

---

### Step 4: Launch the React / Vite Frontend (Terminal 2)
The frontend provides the modern, responsive React interface.

1. Open **Terminal 2** in VS Code.
2. Navigate to the `frontend/` directory:
   ```powershell
   cd frontend
   ```
3. If node dependencies have not been installed yet, run:
   ```powershell
   npm install
   ```
4. Start the Vite development server on port 3000:
   ```powershell
   npm run dev -- --host 127.0.0.1 --port 3000
   ```

#### Verify Frontend is Running:
- Open your browser and visit:
  **`http://localhost:3000`** (or `http://127.0.0.1:3000`)
- The landing page will load with the headline:
  *"Feed the right number. Waste less. Serve everyone."*
- Click **"Launch Workspace"** or **"Launch Operational Workspace"** to enter the operational Command Center.

---

### Step 5: (Optional) Launch the Legacy Streamlit Fallback (Terminal 3)
If you wish to inspect the companion Streamlit operational interface:

1. Open **Terminal 3** in VS Code.
2. Activate the Python virtual environment.
3. Start Streamlit:
   ```powershell
   $env:PYTHONPATH = "."
   streamlit run app/Home.py --server.port 8501
   ```
4. Access Streamlit in your browser at:
   **`http://localhost:8501`**

---

## 3. Running Automated Tests

To run the complete automated test suite verifying all 248 test cases across the database, APIs, forecasts, optimizer, food safety clock, and simulations:

Open a terminal with the virtual environment activated and run:
```powershell
$env:PYTHONPATH = "."
& "..\.venv\Scripts\pytest.exe" -v
```
All 248 tests should execute and pass in approximately 20 seconds.

---

## 4. Port Architecture Summary

| Service | Protocol | Host / Binding | Port | Primary Purpose | URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FastAPI Backend** | HTTP / REST | `127.0.0.1` | **8000** | REST API endpoints, SQLite ORM, calculations | `http://127.0.0.1:8000/docs` |
| **Vite / React Frontend**| HTTP / WS | `127.0.0.1` | **3000** | Interactive React UI, proxies `/api` to 8000 | `http://localhost:3000` |
| **Streamlit Fallback** | HTTP / WS | `127.0.0.1` | **8501** | Python prototype / benchmark companion | `http://localhost:8501` |

---

## 5. Troubleshooting Common Issues

### Issue 1: Port 8000 Already in Use (`[Errno 10048] error while attempting to bind on address`)
- **Cause:** A previous Uvicorn process is still running in the background.
- **Solution (Windows PowerShell):**
  ```powershell
  # Find process using port 8000
  Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess

  # If a zombie python.exe holds the port, terminate it safely:
  Stop-Process -Id <OwningProcessId>
  ```
  Then restart Uvicorn.

### Issue 2: Frontend Shows "Network Error" or 500 on API Requests
- **Cause:** The backend FastAPI server on port 8000 is not running, or Vite proxy is misconfigured.
- **Solution:**
  1. Check Terminal 1 to ensure Uvicorn is active.
  2. Visit `http://127.0.0.1:8000/health` directly in the browser to confirm the backend is responding.
  3. Inspect `frontend/vite.config.ts` to confirm `/api` proxies to `http://127.0.0.1:8000`.

### Issue 3: "ModuleNotFoundError: No module named 'messwise'" during Pytest
- **Cause:** Python cannot resolve the local repository root on its search path.
- **Solution:**
  Ensure you set `PYTHONPATH` before executing pytest:
  ```powershell
  $env:PYTHONPATH = "."
  python -m pytest
  ```

### Issue 4: "OperationalError: database is locked" in SQLite
- **Cause:** Multiple concurrent writing processes attempted to execute transactions simultaneously without waiting.
- **Solution:**
  MessWise configures `connect_args={"check_same_thread": False}` and short transaction windows. If this occurs, ensure no other background script (e.g. manual synthetic generator) is executing a bulk write loop while the server is active.

### Issue 5: Dark Mode Overrides Light Mode Formatting
- **Cause:** Operating system dark mode preference leaking into web view.
- **Solution:**
  MessWise includes `@custom-variant dark (&:where(.dark, .dark *));` in `frontend/src/index.css`. Ensure `document.documentElement` contains `.dark` only when the user explicitly toggles the moon icon in the workspace header.

---

## 6. How to Safely Stop Services
When you finish testing or working:
1. In Terminal 1 (FastAPI), press `Ctrl + C` once to gracefully shut down the Uvicorn worker.
2. In Terminal 2 (Vite), press `Ctrl + C` and type `y` to terminate the development server.
3. In Terminal 3 (Streamlit), press `Ctrl + C` to stop the Streamlit process.
