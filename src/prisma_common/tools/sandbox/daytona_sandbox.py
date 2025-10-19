"""
Daytona Sandbox Engine
A general-purpose sandbox execution engine for running Python code with private package support.
"""

from daytona import Daytona, Image, CreateSandboxFromImageParams, Resources
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv


class SandboxEngine:
    """
    A sandbox execution engine that supports:
    - Public Python packages (numpy, pandas, etc.)
    - Private GitHub repositories (via runtime installation)
    - Custom environment variables
    - Resource management (CPU, memory, disk)
    """
    
    def __init__(
        self,
        public_packages: Optional[List[str]] = None,
        private_repos: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        cpu: int = 1,
        memory: int = 1,
        disk: int = 1,
        auto_stop_interval: int = 0,
        auto_archive_interval: int = 60,
        auto_delete_interval: int = 120,
    ):
        """
        Initialize the sandbox engine.
        
        Args:
            public_packages: List of public PyPI packages (e.g., ["numpy", "pandas"])
            private_repos: List of private GitHub repos (e.g., ["nodetree-io/nodetree-prisma"])
            env_vars: Environment variables to inject into sandbox
            cpu: CPU cores (default: 1)
            memory: Memory in GiB (default: 1)
            disk: Disk space in GiB (default: 1)
            auto_stop_interval: Auto-stop after N minutes (0 = disabled)
            auto_archive_interval: Auto-archive after N minutes
            auto_delete_interval: Auto-delete after N minutes
        """
        # Load environment variables
        load_dotenv()
        
        # Configuration
        self.public_packages = public_packages or ["numpy", "pandas"]
        self.private_repos = private_repos or ["nodetree-io/prisma-shared"]
        self.env_vars = env_vars or {}
        self.cpu = cpu
        self.memory = memory
        self.disk = disk
        self.auto_stop_interval = auto_stop_interval
        self.auto_archive_interval = auto_archive_interval
        self.auto_delete_interval = auto_delete_interval
        
        # Runtime state
        self.daytona = Daytona()
        self.sandbox = None
        
    def _build_image(self) -> Image:
        """Build the base Docker image with public packages."""
        print(f"📦 Building image with packages: {self.public_packages}")
        
        image = (
            Image.base("python:3.11-alpine")
            .run_commands("apk add --no-cache git")
            .run_commands("git config --global credential.helper store")
            .pip_install(self.public_packages)
            .run_commands("pip install --upgrade pip --no-warn-script-location")
        )
        
        # Add environment variables if provided
        if self.env_vars:
            image = image.env(self.env_vars)
        
        return image
    
    def _install_private_repos(self):
        """Install private repositories at runtime (after sandbox starts)."""
        if not self.private_repos or not os.getenv("GITHUB_TOKEN"):
            print("No private repositories to install")
            return
        
        print(f"📦 Installing {len(self.private_repos)} private repository(ies)...")
        
        for repo in self.private_repos:
            print(f"📦 Installing {repo}...")
            try:
                # Configure git with token
                self.sandbox.process.exec(
                    f'git config --global url."https://x-access-token:{os.getenv("GITHUB_TOKEN")}@github.com/".insteadOf "https://github.com/"'
                )
                
                # Install the private package
                repo_url = f"git+https://github.com/{repo}.git"
                result = self.sandbox.process.exec(f"pip install {repo_url}")
                print(f"✓ Installed: {repo}")
                
            except Exception as e:
                print(f"⚠️ Failed to install {repo}: {e}")
    
    def start(self, timeout: int = 60) -> 'SandboxEngine':
        """
        Start the sandbox with configured settings.
        
        Args:
            timeout: Timeout in seconds for sandbox creation
            
        Returns:
            Self for method chaining
        """
        print("🚀 Starting sandbox engine...")
        
        # Build image
        image = self._build_image()
        
        # Create sandbox parameters
        params = CreateSandboxFromImageParams(
            language="python",
            image=image,
            env_vars=self.env_vars,
            resources=Resources(cpu=self.cpu, memory=self.memory, disk=self.disk),
            auto_stop_interval=self.auto_stop_interval,
            auto_archive_interval=self.auto_archive_interval,
            auto_delete_interval=self.auto_delete_interval,
        )
        
        # Create and start sandbox
        self.sandbox = self.daytona.create(
            params,
            timeout=40,
            on_snapshot_create_logs=lambda chunk: print(chunk, end=""),
        )
        
        print(f"✓ Sandbox created: {self.sandbox.id}")
        self.sandbox.start(timeout=timeout)
        print("✓ Sandbox started")
        
        # Install private repositories at runtime
        self._install_private_repos()
        
        print("✓ Sandbox engine ready!\n")
        return self
    
    def run(self, code: str, **kwargs) -> Any:
        """
        Execute Python code in the sandbox.
        
        Args:
            code: Python code to execute (can be multi-line)
            **kwargs: Additional keyword arguments passed to process.exec()
            
        Returns:
            Execution result from sandbox
        """
        if not self.sandbox:
            raise RuntimeError("Sandbox not started. Call start() first.")
        
        # Use code_run for better Python code execution
        response = self.sandbox.process.code_run(code)
        if response.exit_code != 0:
            print(f"Error running code: {response.exit_code} {response.result}")
            return None
        else:
            print(response.result)
            return response.result
    
    def get_info(self) -> Dict[str, Any]:
        """Get sandbox information."""
        if not self.sandbox:
            raise RuntimeError("Sandbox not started. Call start() first.")
        
        return {
            "id": self.sandbox.id,
            "state": self.sandbox.state.value,
            "cpu": self.sandbox.cpu,
            "memory": f"{self.sandbox.memory} GiB",
            "work_dir": self.sandbox.get_work_dir(),
        }
    
    def stop(self, timeout: int = 10):
        """Stop the sandbox."""
        if not self.sandbox:
            return
        
        print("\n🛑 Stopping sandbox...")
        self.sandbox.stop(timeout=timeout)
        print("✓ Sandbox stopped")
    
    def __enter__(self):
        """Context manager entry."""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Example usage
if __name__ == "__main__":
    # Create sandbox engine with custom configuration
    engine = SandboxEngine(
        public_packages=["numpy", "pandas"],
        private_repos=["nodetree-io/prisma-shared"],
        cpu=1,
        memory=1,
        disk=1,
    )


    code = '''
from typing import Optional, List
from prisma_common.operators.operator_manager import get_operator_instance
from prisma_common.tools.tool_manager import get_tools
class Workflow:
    def __init__(
        self
    ) -> None:
        self.name = "Deep Research and Synthesis Workflow"
        self.description = (
            "Workflow that performs deep research on the given task query and "
            "then synthesizes the gathered information into a comprehensive answer."
        )

    async def __call__(self, task_query: str, sources: Optional[List[str]] = None):
        """
        Execute the workflow to perform deep research and then synthesize the result.

        Args:
            task_query (str): The task description or query to be processed
            sources (Optional[List[str]]): Optional file sources (i.e., file paths)

        Returns:
            str: The synthesized research result
        """
        # Use DeepResearchOperator to perform in-depth investigation on the task_query
        deep_research_op = get_operator_instance("DeepResearchOperator")
        deep_research_response = await deep_research_op.arun(query=task_query, context=None)
        deep_research_result = deep_research_response.base_result

        # Use SynthesisOperator to synthesize the deep research results
        synthesis_op = get_operator_instance("SynthesisOperator")
        synthesis_response = await synthesis_op.arun(infos=[deep_research_result], context=None)
        synthesis_result = synthesis_response.base_result

        return synthesis_result
    '''
    with engine:

        engine.run(code)