# Installation

This guide will walk you through installing Flatfish on your computer. Don't worry if you're new to the command line—we'll explain every step!

---

## Prerequisites

Before installing Flatfish, you'll need:

1. **Python 3.10 or newer** - The programming language Flatfish is written in
2. **A terminal application** - To run commands
3. **An internet connection** - To download packages and access AI services

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

Alternatively, use **Git Bash** or **Anaconda Prompt**.
:::

:::{tab-item} Linux
Open your distribution's terminal application (usually Ctrl+Alt+T).
:::

::::

---

## Step 1: Check Your Python Version

First, let's make sure you have Python installed. Open your terminal and type:

```bash
python --version
```

You should see something like `Python 3.10.12` or higher. If you see an error or a version below 3.10, you'll need to install Python.

```{note}
On some systems, you may need to use `python3` instead of `python`.
```

### Installing Python

::::{tab-set}

:::{tab-item} macOS
The easiest way is to use Homebrew:

```bash
# Install Homebrew (if you don't have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11
```

Or download directly from [python.org](https://www.python.org/downloads/).
:::

:::{tab-item} Windows (WSL)
WSL Ubuntu comes with Python. If you need a newer version:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```
:::

:::{tab-item} Linux
Use your package manager:

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

## Step 2: Create a Virtual Environment

A **virtual environment** is an isolated space for your project's packages. This prevents conflicts with other Python projects on your computer.

```bash
# Create a new directory for your projects
mkdir ~/flatfish-projects
cd ~/flatfish-projects

# Create a virtual environment
python -m venv flatfish-env

# Activate the virtual environment
source flatfish-env/bin/activate  # macOS/Linux
# OR
flatfish-env\Scripts\activate     # Windows
```

```{important}
You'll need to **activate** your virtual environment each time you open a new terminal window to work with Flatfish. You'll know it's active when you see `(flatfish-env)` at the start of your command prompt.
```

---

## Step 3: Install Flatfish

With your virtual environment activated, install Flatfish:

```bash
pip install flatfish
```

This will download Flatfish and all its dependencies. It may take a minute or two.

### Verify Installation

Check that Flatfish installed correctly:

```bash
flatfish --version
```

You should see the version number, like `Flatfish 0.1.0`.

---

## Step 4: Get Your API Keys

Flatfish uses AI services to extract text and generate summaries. You'll need API keys for:

1. **Hugging Face** - To access document datasets
2. **DashScope (Alibaba Cloud)** - To use the Qwen AI models

### Getting a Hugging Face Token

1. Go to [huggingface.co](https://huggingface.co) and create a free account
2. Click your profile picture → **Settings**
3. Click **Access Tokens** in the left sidebar
4. Click **New token**
5. Give it a name like "flatfish" and select **Read** access
6. Click **Generate token**
7. **Copy the token** (it starts with `hf_`)—you won't be able to see it again!

```{image} ../images/hf-token.png
:alt: Hugging Face token creation
:width: 600px
:align: center
```

### Getting a DashScope API Key

DashScope provides access to Alibaba's Qwen models, which power Flatfish's text extraction and AI features.

1. Go to [dashscope.aliyun.com](https://dashscope.aliyun.com/) (International version)
2. Create an account or sign in with your Alibaba Cloud account
3. Navigate to **API Key Management**
4. Click **Create API Key**
5. **Copy the key** (it starts with `sk-`)

```{tip}
DashScope offers a free tier with generous limits for getting started. Check their [pricing page](https://dashscope.aliyun.com/pricing) for current details.
```

---

## Step 5: Store Your API Keys

Flatfish reads API keys from a `.env` file in your project directory. We'll set this up when you create your first project, but here's a preview:

```bash
# .env file
HUGGINGFACE_TOKEN=hf_your_token_here
DASHSCOPE_API_KEY=sk_your_key_here
```

```{warning}
**Never share your API keys** or commit them to version control (like Git). The `.env` file should always be in your `.gitignore`.
```

---

## Troubleshooting

### "command not found: flatfish"

Make sure your virtual environment is activated. You should see `(flatfish-env)` in your prompt.

### "pip: command not found"

Try using `pip3` instead of `pip`, or `python -m pip`.

### Permission errors on Linux/macOS

Don't use `sudo pip install`. Instead, make sure you're using a virtual environment.

### SSL certificate errors

This sometimes happens on corporate networks. Try:

```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org flatfish
```

---

## Next Steps

You're ready to go! Continue to:

- **[Quick Start](quickstart.md)** - Process your first documents in 10 minutes
- **[Your First Project](first-project.md)** - A complete walkthrough
