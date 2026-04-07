# Nyx Setup Guide

## LM Studio Configuration

Open LM Studio, load your model, and apply these settings before starting Nyx:

| Setting | Value |
|---|---|
| Context Length | 1024 |
| GPU Offload | 20 |
| Evaluation Batch Size | 256 |
| JIT Model Loading | Off |

## Activate the Virtual Environment

```bat
cd D:\Nyx\nyx_v1\nyx
.venv\Scripts\activate
```

## Start Nyx

### Option A — Single command (watcher + chat together)

```bat
start_nyx.bat
```

Launches `watcher.py` in a background window and `main.py` interactively in the current terminal. The watcher window closes automatically when you exit the chat.

### Option B — Individually

```bat
# Watcher only
.venv\Scripts\python.exe watcher.py

# Chat only
.venv\Scripts\python.exe main.py
```

## Search Memory

```bat
.venv\Scripts\python.exe query_nyx.py "search term"
```

## Install / Update Dependencies

```bat
.venv\Scripts\pip install -r requirements.txt
```
