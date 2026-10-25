"""Execute both SYNTHETIC teaching notebooks with the current Python environment."""

import argparse
import os
import sys
from pathlib import Path

import nbformat
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["tcp", "ipc"], default="tcp")
    parser.add_argument(
        "--in-process", action="store_true", help="Execute code cells with IPython without kernel sockets"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.in_process:
        execute_in_process(root)
        return
    # An explicit temporary kernel avoids silently using a different Python/env.
    import json
    from tempfile import TemporaryDirectory

    with TemporaryDirectory(prefix="alga-tutorial-kernel-") as directory:
        kernel = Path(directory) / "alga-tutorial"
        kernel.mkdir()
        (kernel / "kernel.json").write_text(
            json.dumps(
                {
                    "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                    "display_name": "AlgaTwin tutorial runner",
                    "language": "python",
                }
            )
        )
        manager = KernelSpecManager(kernel_dirs=[directory])
        for path in sorted(root.glob("*.ipynb")):
            book = nbformat.read(path, as_version=4)
            client = NotebookClient(
                book, timeout=300, kernel_name="alga-tutorial", resources={"metadata": {"path": str(root)}}
            )
            client.create_kernel_manager()
            client.km.kernel_spec_manager = manager
            if args.transport == "ipc":
                client.km.transport = "ipc"
                client.km.ip = str(Path(directory) / "connection")
            client.execute()
            nbformat.write(book, path)
            print(f"EXECUTED: {path.name}", flush=True)


def execute_in_process(root):
    """Explicit fallback for environments that disallow local kernel sockets."""
    from IPython.terminal.interactiveshell import TerminalInteractiveShell
    from IPython.utils.capture import capture_output

    shell = TerminalInteractiveShell.instance()
    shell.display_formatter.active_types = ["text/plain", "text/html", "image/png"]
    previous = Path.cwd()
    try:
        os.chdir(root)
        for path in sorted(root.glob("*.ipynb")):
            shell.reset(new_session=True)
            shell.run_line_magic("matplotlib", "inline")
            book = nbformat.read(path, as_version=4)
            count = 0
            for cell in book.cells:
                if cell.cell_type != "code":
                    continue
                count += 1
                with capture_output() as captured:
                    result = shell.run_cell(cell.source, store_history=True)
                if result.error_before_exec or result.error_in_exec:
                    raise RuntimeError(f"{path.name}, cell {count}: {captured.stdout} {captured.stderr}")
                cell.execution_count = count
                cell.outputs = []
                for stream, text in (("stdout", captured.stdout), ("stderr", captured.stderr)):
                    if text:
                        cell.outputs.append(nbformat.v4.new_output("stream", name=stream, text=text))
                for output in captured.outputs:
                    cell.outputs.append(
                        nbformat.v4.new_output("display_data", data=output.data, metadata=output.metadata)
                    )
            book.metadata["alga_twin_execution"] = {
                "method": "IPython in-process code-cell execution; no Jupyter socket transport",
                "python": sys.version.split()[0],
            }
            nbformat.write(book, path)
            print(f"EXECUTED IN-PROCESS: {path.name} ({count} code cells)", flush=True)
    finally:
        os.chdir(previous)


if __name__ == "__main__":
    main()
