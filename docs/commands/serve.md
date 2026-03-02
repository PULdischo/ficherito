# flatfish serve

Start a local development server to preview your site.

---

## Usage

```bash
flatfish serve [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--port` | `-p` | Port number | `8000` |
| `--host` | `-h` | Host address | `localhost` |
| `--open` | `-o` | Open browser automatically | `False` |
| `--watch` | `-w` | Watch for changes | `True` |
| `--directory` | `-d` | Site directory | `site/` |

---

## What It Does

The `serve` command:

1. Starts a local HTTP server
2. Serves your generated site
3. Optionally watches for changes
4. Provides live reload

---

## Examples

### Basic Server

```bash
flatfish serve
# Server running at http://localhost:8000
```

### Custom Port

```bash
flatfish serve --port 3000
# Server running at http://localhost:3000
```

### Open Browser Automatically

```bash
flatfish serve --open
# Opens http://localhost:8000 in default browser
```

### Network Access

```bash
flatfish serve --host 0.0.0.0
# Server accessible from other devices on network
```

### Different Directory

```bash
flatfish serve --directory public/
```

---

## Live Reload

When `--watch` is enabled (default):

```
Flatfish Serve
══════════════

Server running at http://localhost:8000

Watching for changes...
  • transcriptions/
  • entities/
  • output/
  • templates/

[10:30:15] Changed: output/timeline.txt
[10:30:15] Rebuilding affected pages...
[10:30:16] ✓ 3 pages updated
[10:30:16] Browser reloaded
```

### Watched Paths

By default, watches:
- `transcriptions/` - Document content
- `entities/` - Entity data
- `output/` - Summary files
- `templates/` - Custom templates
- `flatfish.yaml` - Configuration

### Disable Watch

```bash
flatfish serve --no-watch
```

---

## Development Workflow

### Typical Session

```bash
# Terminal 1: Run server
flatfish serve --open

# Terminal 2: Make changes
# Edit templates, update config, etc.
# Browser auto-refreshes
```

### Quick Iteration

1. Start server with watch
2. Edit `flatfish.yaml` or templates
3. See changes immediately
4. Repeat until satisfied
5. Deploy when ready

---

## Console Output

```
Flatfish Serve
══════════════

Starting development server...

  Local:   http://localhost:8000
  Network: http://192.168.1.100:8000

Press Ctrl+C to stop

[10:30:00] GET / 200
[10:30:01] GET /assets/css/main.css 200
[10:30:01] GET /assets/js/search.js 200
[10:30:05] GET /documents/letter_001/ 200
[10:30:10] GET /finding-aid/ 200
```

### Request Logging

Each request shows:
- Timestamp
- HTTP method
- Path
- Status code

---

## Configuration

### flatfish.yaml Settings

```yaml
serve:
  # Default port
  port: 8000
  
  # Open browser on start
  open_browser: false
  
  # Enable live reload
  live_reload: true
  
  # Paths to watch
  watch_paths:
    - "transcriptions/"
    - "entities/"
    - "output/"
    - "templates/"
```

---

## Accessing from Other Devices

### Local Network

```bash
flatfish serve --host 0.0.0.0
```

Find your IP:
```bash
# macOS/Linux
ip addr | grep inet
# or
hostname -I

# Windows
ipconfig
```

Access from other device:
```
http://192.168.1.100:8000
```

### Tunneling (ngrok)

For external access:

```bash
# Install ngrok
# https://ngrok.com/

# Start server
flatfish serve

# In another terminal
ngrok http 8000
# Gives public URL like https://abc123.ngrok.io
```

---

## Troubleshooting

### Port Already in Use

```
Error: Port 8000 already in use
```

Solution:
```bash
# Use different port
flatfish serve --port 8001

# Or find and kill existing process
lsof -i :8000
kill <PID>
```

### Watch Not Working

```bash
# Increase watch limit (Linux)
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Slow Reload

For large sites, limit watched paths:

```yaml
serve:
  watch_paths:
    - "templates/"  # Only watch templates
```

---

## See Also

- **[build](build.md)** - Generate site
- **[deploy](deploy.md)** - Deploy to hosting
- **[Building Sites](../usage/building-sites.md)** - Usage guide
