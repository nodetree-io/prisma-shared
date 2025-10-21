import os
import sys
import json
from typing import List, Dict, Any, Optional, Set, Union, Tuple
import hashlib
import yaml
from collections import OrderedDict, defaultdict
from dotenv import load_dotenv

from mcp_use import MCPClient

load_dotenv()

MCP_BENCH_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "commands.json")
MCP_BENCH_INFO_PATH = os.path.join(os.path.dirname(__file__), "mcp_servers_info.json")

class MCPBenchZoo:
    """
    MCP Tools wrapper for Composio integration with built-in authorization checking
    """
    def __init__(self):
        """Initialize MCP tools client with authorization checking
        
        Args:
            user_id: User ID for authorization checking
            mcp_names: Set of MCP names to initialize. If None, loads all available MCPs
        """
        self._max_cache_size = 100

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate up to YOPO root directory and then to benchmarks
        self.running_root_dir = os.path.join(current_file_dir, "mcp_servers")
        # Initialize MCP configuration boxes
        self._init_mcp_boxes()
        self._init_mcp_tools_info()
        
    def _init_mcp_boxes(self):
        """Initialize MCP configuration boxes based on user ID and MCP names."""        
        with open(MCP_BENCH_CONFIG_PATH, 'r') as file:
            mcp_config_dict: dict = json.load(file)

        self.mcp_box: Dict[str, dict] = defaultdict(dict)
        self.mcp_description: Dict[str, str] = defaultdict(str)

        for mcp_name, item in mcp_config_dict.items():
            # Get info
            self.mcp_description[mcp_name] = item["description"]

            # node dist/cli.js --apikey AIzaSyD1IaqzaoeTWsUgyg7bH-JKgNZuaIOWsh4 --port 3001
            if mcp_name == "Google Maps":
                self.mcp_box[mcp_name] = {
                    "url": "http://localhost:3001/mcp"
                }
                continue
            cwd: str = item["cwd"].lstrip("../")
            cmd_l: List[str] = item["cmd"].strip().split()

            if "uv" not in cmd_l:
                if cmd_l[-1] == "run":
                    execution_file = cmd_l[-2]
                    cmd_l[-2] = os.path.join(self.running_root_dir, cwd, execution_file)
                else:
                    execution_file = cmd_l[-1]
                    cmd_l[-1] = os.path.join(self.running_root_dir, cwd, execution_file)
            else:
                _run_idx = cmd_l.index("run")
                cmd_l.insert(_run_idx+1, "--directory")
                cmd_l.insert(_run_idx+2, os.path.join(self.running_root_dir, cwd))
            env= {}
            if item["env"] != []:
                value = os.getenv(item["env"][0], None)
                if value: env[item["env"][0]] = value
                
            self.mcp_box[mcp_name] = {
                "command": cmd_l[0],
                "args": cmd_l[1:],
                "env": env
            }
    
    def _init_mcp_tools_info(self):
        with open(MCP_BENCH_INFO_PATH, 'r') as file:
            mcp_info_dict: dict = json.load(file)
        self.mcp_tool_details: Dict[str, str] = defaultdict(str)
        for name, items in mcp_info_dict["servers"].items():
            tools_info = []
            for tool_name, tool_items in items["tools"].items():
                tools_info.append(tool_items["description"])
            
            self.mcp_tool_details[name] = "It has the following abilities: \n" + "\n".join([f"{idx+1}. {value}" for idx, value in enumerate(tools_info)])

    def format_mcp_servers_info(self, mcp_name_list: List[str]) -> str:
        """
        Format MCP server information for display.
        
        Args:
            mcp_name_list: List of MCP server names to format information for
            
        Returns:
            str: Formatted string containing numbered list of MCP servers with their descriptions
        """
        result = []
        for name in mcp_name_list:
            if name in self.mcp_tool_details:
                result.append(f"{name}: {self.mcp_tool_details[name]}")
        
        return "\n".join([f"{idx+1}. {value}" for idx, value in enumerate(result)])
        
    def list_all_mcp_servers(self) -> List[str]:
        """List all available MCP server names.
        
        Returns:
            List[str]: A list of all MCP server names that are configured and available.
        """
        return list(self.mcp_box.keys())

    def create_client(self, mcp_name_list: List[str]) -> MCPClient:
        """Create and configure the MCP client for authorized MCPs only"""
        # Filter to only include authorized MCPs
        authorized_mcp_list = [mcp for mcp in mcp_name_list if mcp in self.mcp_box]
        
        if not authorized_mcp_list:
            raise ValueError("No authorized MCPs available for client creation")
            
        new_mcp_server_dict = {mcp_name: self.mcp_box[mcp_name] for mcp_name in authorized_mcp_list}
        
        return MCPClient.from_dict({
            "mcpServers": new_mcp_server_dict
        })