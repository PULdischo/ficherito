"""Rich console utilities with Jupyter/Colab support."""

from rich.console import Console


def _is_notebook() -> bool:
    """Detect if we're running inside a Jupyter notebook or Google Colab."""
    try:
        from IPython import get_ipython
        shell = get_ipython()
        if shell is None:
            return False
        shell_class = type(shell).__name__
        # Colab uses 'Shell', Jupyter uses 'ZMQInteractiveShell'
        return shell_class in ("ZMQInteractiveShell", "Shell")
    except (ImportError, NameError):
        return False


def get_console(**kwargs) -> Console:
    """Create a Rich Console that works in both terminal and Jupyter/Colab.

    In notebook environments, Rich's default terminal detection fails because
    stdout is not a real TTY. This causes progress bars to print a new line
    for every update instead of overwriting in place. Setting force_jupyter=True
    enables Rich's native Jupyter display using IPython widgets.
    """
    if _is_notebook():
        kwargs.setdefault("force_jupyter", True)
    return Console(**kwargs)
