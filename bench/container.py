import subprocess
import uuid


class Container:
    """A throwaway container kept alive with `sleep infinity`; scripts are fed through stdin to avoid quoting."""

    def __init__(self, image, *, network="none", env_names=(), mounts=(), memory="4g", cpus="3"):
        self.name = f"tb-{uuid.uuid4().hex[:10]}"
        cmd = ["docker", "run", "-d", "--name", self.name, "--network", network,
               "--memory", memory, "--cpus", cpus]
        for name in env_names:
            cmd += ["-e", name]
        for src, dst in mounts:
            cmd += ["-v", f"{src}:{dst}:ro"]
        subprocess.run(cmd + [image, "sleep", "infinity"], check=True, capture_output=True)

    def exec(self, script, timeout=None, user=None):
        cmd = ["docker", "exec", "-i"] + (["-u", user] if user else []) + [self.name, "bash", "-s"]
        try:  # bytes, not text mode: on Windows text mode would turn every "\n" of the script into "\r\n"
            p = subprocess.run(cmd, input=script.encode("utf-8"), capture_output=True, timeout=timeout)
            return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
        except subprocess.TimeoutExpired as e:
            return None, (e.stdout or b"").decode("utf-8", "replace")

    def read(self, path):
        p = subprocess.run(["docker", "exec", self.name, "cat", path], capture_output=True)
        return p.stdout.decode("utf-8", "replace") if p.returncode == 0 else None

    def cp_in(self, src, dst):
        subprocess.run(["docker", "cp", str(src), f"{self.name}:{dst}"], check=True, capture_output=True)

    def remove(self):
        subprocess.run(["docker", "rm", "-f", self.name], capture_output=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.remove()
