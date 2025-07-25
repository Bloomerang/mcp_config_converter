import json
import argparse
from datetime import datetime
import os

def convert_copilot_to_claude(copilot_data):
    claude_data = {
        "globalShortcut": "",
        "mcpServers": {}
    }
    for server_name, server_config in copilot_data.get("servers", {}).items():
        if server_config.get("type") == "stdio":
            new_config = {
                "command": server_config.get("command"),
                "args": server_config.get("args")
            }
            if "env" in server_config and server_config["env"]:
                new_config["env"] = {key: "PLEASE_SET_YOUR_VARIABLE" for key in server_config["env"]}
            claude_data["mcpServers"][server_name] = new_config
        elif server_config.get("type") == "http":
            claude_data["mcpServers"][server_name] = {
                "command": "npx",
                "args": ["-y", "mcp-remote", server_config.get("url")]
            }
    return claude_data

def convert_copilot_to_gemini(copilot_data):
    gemini_data = {
        "mcpServers": {}
    }
    for server_name, server_config in copilot_data.get("servers", {}).items():
        if server_config.get("type") == "stdio":
            new_config = {
                "command": server_config.get("command"),
                "args": server_config.get("args")
            }
            if "env" in server_config and server_config["env"]:
                new_config["env"] = {key: "PLEASE_SET_YOUR_VARIABLE" for key in server_config["env"]}
            gemini_data["mcpServers"][server_name] = new_config
        elif server_config.get("type") == "http":
            gemini_data["mcpServers"][server_name] = {
                "command": "npx",
                "args": ["-y", "mcp-remote", server_config.get("url")]
            }
    return gemini_data

def convert_claude_to_copilot(claude_data):
    copilot_data = {
        "servers": {},
        "inputs": []
    }
    for server_name, server_config in claude_data.get("mcpServers", {}).items():
        command = server_config.get("command")
        args = server_config.get("args", [])
        if command == "npx" and len(args) > 2 and args[0] == "-y" and args[1] == "mcp-remote":
            copilot_data["servers"][server_name] = {
                "type": "http",
                "url": args[2],
                "gallery": True
            }
        else:
            server_details = {
                "type": "stdio",
                "command": command,
                "args": args,
                "gallery": True
            }
            if "env" in server_config and server_config["env"]:
                server_details["env"] = {key: "PLEASE_SET_YOUR_VARIABLE" for key in server_config["env"]}
            copilot_data["servers"][server_name] = server_details
    return copilot_data

def convert_claude_to_gemini(claude_data):
    gemini_data = {"mcpServers": {}}
    for server_name, server_config in claude_data.get("mcpServers", {}).items():
        new_config = server_config.copy()
        if "env" in new_config and new_config["env"]:
            new_config["env"] = {key: "PLEASE_SET_YOUR_VARIABLE" for key in new_config["env"]}
        gemini_data["mcpServers"][server_name] = new_config
    return gemini_data

def convert_gemini_to_copilot(gemini_data):
    claude_equivalent = {"mcpServers": gemini_data.get("mcpServers", {})}
    return convert_claude_to_copilot(claude_equivalent)

def convert_gemini_to_claude(gemini_data):
    claude_data = {
        "globalShortcut": "",
        "mcpServers": {}
    }
    for server_name, server_config in gemini_data.get("mcpServers", {}).items():
        new_config = server_config.copy()
        if "env" in new_config and new_config["env"]:
            new_config["env"] = {key: "PLEASE_SET_YOUR_VARIABLE" for key in new_config["env"]}
        claude_data["mcpServers"][server_name] = new_config
    return claude_data

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def load_json(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def get_server_count(data, filename):
    if "copilot" in filename:
        return len(data.get("servers", {}))
    else:
        return len(data.get("mcpServers", {}))

def main():
    parser = argparse.ArgumentParser(description="Convert MCP configuration files.")
    parser.add_argument("source_file", nargs='?', default=None, help="The source configuration file (e.g., copilot.json, claude.json, gemini.json)")
    args = parser.parse_args()

    source_filename = args.source_file

    if source_filename is None:
        files = ["copilot.json", "claude.json", "gemini.json"]
        file_data = {f: load_json(f) for f in files}
        file_data = {f: d for f, d in file_data.items() if d is not None}

        if not file_data:
            print("Error: No valid configuration files found.")
            return

        latest_file = max(file_data.keys(), key=lambda f: get_server_count(file_data[f], f))
        source_filename = latest_file
        print(f"Automatically selected {source_filename} as the source.")


    try:
        with open(source_filename, "r") as f:
            source_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {source_filename} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode {source_filename}.")
        return

    if "copilot.json" in source_filename:
        claude_config = convert_copilot_to_claude(source_data)
        gemini_config = convert_copilot_to_gemini(source_data)
        save_json("claude.json", claude_config)
        save_json("gemini.json", gemini_config)
        print("Successfully converted copilot.json to claude.json and gemini.json")
    elif "claude.json" in source_filename:
        copilot_config = convert_claude_to_copilot(source_data)
        gemini_config = convert_claude_to_gemini(source_data)
        save_json("copilot.json", copilot_config)
        save_json("gemini.json", gemini_config)
        print("Successfully converted claude.json to copilot.json and gemini.json")
    elif "gemini.json" in source_filename:
        copilot_config = convert_gemini_to_copilot(source_data)
        claude_config = convert_gemini_to_claude(source_data)
        save_json("copilot.json", copilot_config)
        save_json("claude.json", claude_config)
        print("Successfully converted gemini.json to copilot.json and claude.json")
    else:
        print(f"Unsupported source file: {source_filename}")

if __name__ == "__main__":
    main()