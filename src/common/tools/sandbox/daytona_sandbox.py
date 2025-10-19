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
        
        # Auto-include common environment variables from current environment
        auto_env_vars = {}
        important_env_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY", 
            "GOOGLE_API_KEY",
            "GITHUB_TOKEN",
            "DEV_MODEL_NAME",
            "DEV_LLM_NAME",
            "PROD_MODEL_NAME",
            "PROD_LLM_NAME",
        ]
        
        for var in important_env_vars:
            value = os.getenv(var)
            if value:
                auto_env_vars[var] = value
                print(f"✓ Including env var: {var}")
        
        # Merge auto-detected with user-provided env vars (user-provided takes precedence)
        self.env_vars = {**auto_env_vars, **(env_vars or {})}
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
                github_token = os.getenv("GITHUB_TOKEN")
                if github_token:
                    print(f"✓ Using GitHub token: {github_token[:10]}...")
                    self.sandbox.process.exec(
                        f'git config --global url."https://x-access-token:{github_token}@github.com/".insteadOf "https://github.com/"'
                    )
                else:
                    print("⚠️ No GITHUB_TOKEN found, trying public access")
                
                # Remove old clone if exists
                self.sandbox.process.exec(f"rm -rf /tmp/{repo.replace('/', '-')}")
                
                # Clone the repository first
                clone_result = self.sandbox.process.exec(f"git clone https://github.com/{repo}.git /tmp/{repo.replace('/', '-')}")
                print(f"✓ Clone result: {clone_result}")
                
                # Check if the directory exists and has pyproject.toml
                check_result = self.sandbox.process.exec(f"ls -la /tmp/{repo.replace('/', '-')}")
                print(f"✓ Directory contents: {check_result}")
                
                # Check if pyproject.toml exists
                pyproject_check = self.sandbox.process.exec(f"ls -la /tmp/{repo.replace('/', '-')}/pyproject.toml")
                print(f"✓ pyproject.toml check: {pyproject_check}")
                
                # Install the package in editable mode from the cloned directory
                install_result = self.sandbox.process.exec(f"cd /tmp/{repo.replace('/', '-')} && pip install -e .")
                if install_result.exit_code != 0:
                    print(f"❌ Install failed with exit code {install_result.exit_code}")
                    print(f"Error output: {install_result.result}")
                    raise RuntimeError(f"Failed to install package: {install_result.result}")
                print(f"✓ Install result: {install_result}")
                
                # Install AI dependencies for full functionality
                ai_install_result = self.sandbox.process.exec(f"cd /tmp/{repo.replace('/', '-')} && pip install -e .[ai]")
                if ai_install_result.exit_code != 0:
                    print(f"❌ AI dependencies install failed with exit code {ai_install_result.exit_code}")
                    print(f"Error output: {ai_install_result.result}")
                    # Don't fail completely, AI dependencies are optional
                else:
                    print(f"✓ AI dependencies install result: {ai_install_result}")
                
                # Check if the package was actually installed
                list_result = self.sandbox.process.exec("pip list | grep -i common")
                print(f"✓ Installed packages with 'common': {list_result}")
                
                # Verify installation - debug what's available
                debug_result = self.sandbox.process.exec("python -c 'import sys; print(\"Python path:\"); [print(f\"  {p}\") for p in sys.path]; print(\"\\nInstalled packages:\"); import pkg_resources; [print(f\"  {p.project_name}=={p.version}\") for p in pkg_resources.working_set if \"common\" in p.project_name.lower()]'")
                print(f"✓ Debug info: {debug_result}")
                
                # Try to import common
                verify_result = self.sandbox.process.exec("python -c 'import common; print(f\"common version: {common.__version__}\")'")
                print(f"✓ Verification: {verify_result}")
                
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
    
    def load_workflow_code(self, workflow_class: str, query: str, **workflow_kwargs) -> str:
        """
        Generate runnable sandbox code from a workflow class definition.
        
        Args:
            workflow_class: The workflow class code (class definition as string)
            query: The query string to pass to the workflow
            **workflow_kwargs: Additional keyword arguments for the workflow
            
        Returns:
            Complete executable code string for the sandbox
        """
        # Build kwargs string if provided
        kwargs_str = ""
        if workflow_kwargs:
            kwargs_parts = [f"{k}={repr(v)}" for k, v in workflow_kwargs.items()]
            kwargs_str = ", " + ", ".join(kwargs_parts)
        
        code = f'''
import asyncio

{workflow_class}

if __name__ == "__main__":
    workflow = Workflow()
    query = {repr(query)}
    result = asyncio.run(workflow(query{kwargs_str}))
    print(result)
'''
        return code
    
    def run_workflow(self, code: str, **kwargs) -> Any:
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
    def delete(self):
        """Delete the sandbox."""
        if not self.sandbox:
            return
        
        print("\n🗑️ Deleting sandbox...")
        self.sandbox.delete()
        print("✓ Sandbox deleted")

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
        private_repos=["nodetree-io/prisma-shared"],
        cpu=1,
        memory=1,
        disk=1,
    )

    workflow_class = '''

from typing import Optional, List
from common.operators.operator_manager import get_operator_instance
from common.tools.tool_manager import get_tools

class Workflow:
    def __init__(self):
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
        # Use SimpleTestOperator to verify the package is working
        test_op = get_operator_instance("SimpleTestOperator")
        test_response = await test_op.arun(message=task_query)
        test_result = test_response.base_result

        return test_result
'''

    # Generate runnable code using load_workflow_code
    query = "MSECE CMU start in Spring 2026 2 year program, give me class recommendations for securing FAANG internship in 2027 summer"
    code = engine.load_workflow_code(workflow_class, query)
    
    print("📝 Generated runnable code:")
    print("=" * 80)
    print(code)
    print("=" * 80)
    print()

    # Execute in sandbox
    engine.start()
    engine.run_workflow(code)
    print("✓ Sandbox exit!")
    engine.delete()

