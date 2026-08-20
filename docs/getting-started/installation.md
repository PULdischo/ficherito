# Installation

This guide will walk you through installing Ficherito on your computer.

---

## Prerequisites

Before installing Ficherito, you'll need:

1. **Python 3.10 or newer** - The programming language Ficherito is written in
2. **Node.js 20+** - Runs the Eleventy/Pagefind site build (`ficherito build`)
3. **A terminal application** - To run commands
4. **An internet connection** - To download packages and access AI services

### What's a Terminal?

A terminal (also called "command line" or "shell") is a text-based way to interact with your computer. Instead of clicking icons, you type commands.

::::{tab-set}

:::{tab-item} macOS
Open **Terminal** (find it in Applications → Utilities → Terminal, or search for "Terminal" with Spotlight).
:::

:::{tab-item} Windows
We recommend using **Windows Terminal** with **WSL** (Windows Subsystem for Linux) for the best experience.

1. Install WSL by opening PowerShell as Administrator and running:
   ```
   wsl --install
   ```
2. Restart your computer
3. Open **Ubuntu** from the Start menu

Alternatively, use **Git Bash** or **PowerShell** directly.
:::

:::{tab-item} Linux
Open your distribution's terminal application (usually Ctrl+Alt+T).
:::

::::

---

## Step 1: Check Your Python Version

```bash
python --version
```

You should see `Python 3.10.x` or higher.

```{note}
On some systems, you may need to use `python3` instead of `python`.
```

### Installing Python

::::{tab-set}

:::{tab-item} macOS
```bash
brew install python@3.11
```
Or download directly from [python.org](https://www.python.org/downloads/).
:::

:::{tab-item} Windows (WSL)
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```
:::

:::{tab-item} Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Fedora
sudo dnf install python3.11

# Arch
sudo pacman -S python
```
:::

::::

---

## Step 2: Check Your Node.js Version

Only needed for `ficherito build` (the site build). The rest of the pipeline
works without it.

```bash
node --version
```

You should see `v20.x` or higher. If it's missing, install it from
[nodejs.org](https://nodejs.org/) or via your package manager
(`brew install node`, `sudo apt install nodejs npm`, etc.).

---

## Step 3: Create a Virtual Environment

A **virtual environment** is an isolated space for your project's packages.

```bash
mkdir ~/ficherito-projects
cd ~/ficherito-projects

python -m venv ficherito-env

source ficherito-env/bin/activate  # macOS/Linux
# OR
ficherito-env\Scripts\activate     # Windows
```

```{important}
You'll need to **activate** your virtual environment each time you open a new terminal window. You'll know it's active when you see `(ficherito-env)` at the start of your command prompt.
```

---

## Step 4: Install Ficherito

```bash
pip install ficherito
```

### Verify Installation

```bash
ficherito --version
```

---

## Step 5: Get an API Key

Ficherito sends document images to a vision-language model for transcription
and entity extraction, via any OpenAI-compatible endpoint. The default is
DashScope (Alibaba Cloud), which hosts Qwen-VL:

1. Go to [dashscope.aliyun.com](https://dashscope.aliyun.com/) (International version)
2. Create an account or sign in
3. Navigate to **API Key Management**
4. Click **Create API Key** and copy it (starts with `sk-`)

```{tip}
Any OpenAI-compatible vision endpoint works — set `OPENAI_BASE_URL` to point
at OpenAI, a self-hosted model, or another provider instead.
```

---

## Step 6: Store Your API Key

Ficherito reads configuration from a `.env` file in your project directory
(created for you by `ficherito init`):

```bash
# .env
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=qwen-vl-max
```

```{warning}
**Never share your API key** or commit `.env` to version control. `ficherito init` adds it to `.gitignore` automatically.
```

---

## Troubleshooting

### "command not found: ficherito"

Make sure your virtual environment is activated. You should see `(ficherito-env)` in your prompt.

### "pip: command not found"

Try `pip3` instead of `pip`, or `python -m pip`.

### Permission errors on Linux/macOS

Don't use `sudo pip install`. Use a virtual environment instead.

### `npm not found; skipping Eleventy/Pagefind build`

This warning appears from `ficherito build` if Node.js isn't installed. Install it (Step 2 above) and re-run the build.

---

## Next Steps

- **[Quick Start](quickstart.md)** - Process your first documents in 10 minutes
- **[Your First Project](first-project.md)** - A complete walkthrough
