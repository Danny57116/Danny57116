import socket
import json
import threading
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Optional

# ===== Model Context Protocol (MCP) Base Classes =====

class MCPMessage:
    """Base class for MCP message format"""
    
    def __init__(self, request_type: str, payload: Dict[str, Any], request_id: str = None):
        self.request_type = request_type
        self.payload = payload
        self.request_id = request_id or f"{int(time.time() * 1000)}"
        
    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps({
            "request_type": self.request_type,
            "payload": self.payload,
            "request_id": self.request_id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPMessage':
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls(
            request_type=data["request_type"],
            payload=data["payload"],
            request_id=data["request_id"]
        )


class MCPServer(ABC):
    """Abstract base class for MCP servers"""
    
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.handlers = {}
        self.socket = None
        self.running = False
        
    def register_handler(self, request_type: str, handler: Callable):
        """Register a handler for a specific request type"""
        self.handlers[request_type] = handler
        
    def start(self):
        """Start the server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.running = True
        
        print(f"MCP Server started on {self.host}:{self.port}")
        
        try:
            while self.running:
                client_socket, address = self.socket.accept()
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"Server error: {e}")
            self.stop()
    
    def _handle_client(self, client_socket, address):
        """Handle client connection"""
        try:
            # Receive data size (4 bytes)
            size_bytes = client_socket.recv(4)
            if not size_bytes:
                return
                
            message_size = int.from_bytes(size_bytes, byteorder='big')
            
            # Receive message data
            data = b''
            while len(data) < message_size:
                chunk = client_socket.recv(min(4096, message_size - len(data)))
                if not chunk:
                    break
                data += chunk
                
            message_str = data.decode('utf-8')
            message = MCPMessage.from_json(message_str)
            
            # Process the message
            if message.request_type in self.handlers:
                response_payload = self.handlers[message.request_type](message.payload)
                response = MCPMessage(
                    request_type=f"{message.request_type}_response",
                    payload=response_payload,
                    request_id=message.request_id
                )
                
                # Send response
                response_data = response.to_json().encode('utf-8')
                response_size = len(response_data).to_bytes(4, byteorder='big')
                client_socket.sendall(response_size + response_data)
            else:
                # Send error response
                error_response = MCPMessage(
                    request_type="error",
                    payload={"error": f"Unknown request type: {message.request_type}"},
                    request_id=message.request_id
                )
                response_data = error_response.to_json().encode('utf-8')
                response_size = len(response_data).to_bytes(4, byteorder='big')
                client_socket.sendall(response_size + response_data)
                
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("MCP Server stopped")


class MCPClient:
    """Client for connecting to MCP servers"""
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 5000):
        self.server_host = server_host
        self.server_port = server_port
    
    def send_request(self, request_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the server and return the response"""
        message = MCPMessage(request_type, payload)
        
        # Connect to server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.server_host, self.server_port))
        
        try:
            # Send message
            message_data = message.to_json().encode('utf-8')
            message_size = len(message_data).to_bytes(4, byteorder='big')
            client_socket.sendall(message_size + message_data)
            
            # Receive response size
            size_bytes = client_socket.recv(4)
            if not size_bytes:
                return {"error": "Connection closed"}
                
            response_size = int.from_bytes(size_bytes, byteorder='big')
            
            # Receive response data
            response_data = b''
            while len(response_data) < response_size:
                chunk = client_socket.recv(min(4096, response_size - len(response_data)))
                if not chunk:
                    break
                response_data += chunk
                
            response_str = response_data.decode('utf-8')
            response = MCPMessage.from_json(response_str)
            
            return response.payload
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
        finally:
            client_socket.close()


class MCPHost(ABC):
    """Abstract base class for MCP hosts"""
    
    def __init__(self, client: MCPClient):
        self.client = client
    
    @abstractmethod
    def run(self):
        """Main method to run the host application"""
        pass


# ===== Implementation Examples =====

class FileOperationServer(MCPServer):
    """MCP Server for file operations"""
    
    def __init__(self, host: str = 'localhost', port: int = 5000):
        super().__init__(host, port)
        self.register_handler("read_file", self.handle_read_file)
        self.register_handler("write_file", self.handle_write_file)
        self.register_handler("list_directory", self.handle_list_directory)
    
    def handle_read_file(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle read file requests"""
        file_path = payload.get("file_path")
        if not file_path or not os.path.isfile(file_path):
            return {"success": False, "error": "File not found or invalid path"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_write_file(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle write file requests"""
        file_path = payload.get("file_path")
        content = payload.get("content")
        
        if not file_path:
            return {"success": False, "error": "Invalid file path"}
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_list_directory(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle directory listing requests"""
        directory_path = payload.get("directory_path")
        if not directory_path or not os.path.isdir(directory_path):
            return {"success": False, "error": "Directory not found or invalid path"}
        
        try:
            items = os.listdir(directory_path)
            files = [item for item in items if os.path.isfile(os.path.join(directory_path, item))]
            directories = [item for item in items if os.path.isdir(os.path.join(directory_path, item))]
            
            return {
                "success": True, 
                "files": files, 
                "directories": directories
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class CodeCompletionServer(MCPServer):
    """MCP Server for code completion"""
    
    def __init__(self, host: str = 'localhost', port: int = 5001):
        super().__init__(host, port)
        self.register_handler("complete_code", self.handle_complete_code)
        
    def handle_complete_code(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code completion requests"""
        code = payload.get("code", "")
        language = payload.get("language", "python")
        
        # In a real implementation, this would connect to a language model
        # For this example, we'll just provide simple completions
        completions = []
        
        if language == "python":
            if "def " in code:
                completions = ["self", "return", "if ", "for ", "while "]
            elif "import " in code:
                completions = ["os", "sys", "json", "time", "requests"]
            else:
                completions = ["def ", "class ", "import ", "print(", "if "]
                
        return {
            "success": True,
            "completions": completions
        }


class ClaudeDesktopHost(MCPHost):
    """Example implementation of Claude Desktop Host"""
    
    def __init__(self, file_server_host: str = 'localhost', file_server_port: int = 5000):
        super().__init__(MCPClient(file_server_host, file_server_port))
        
    def run(self):
        """Run the Claude Desktop application"""
        print("Claude Desktop is running...")
        
        while True:
            print("\nClaude Desktop Options:")
            print("1. Read a file")
            print("2. List directory contents")
            print("3. Exit")
            
            choice = input("Select an option (1-3): ")
            
            if choice == "1":
                file_path = input("Enter file path to read: ")
                response = self.client.send_request("read_file", {"file_path": file_path})
                
                if response.get("success"):
                    print("\n--- File Content ---")
                    print(response.get("content"))
                    print("-------------------")
                else:
                    print(f"Error: {response.get('error')}")
                    
            elif choice == "2":
                dir_path = input("Enter directory path to list: ")
                response = self.client.send_request("list_directory", {"directory_path": dir_path})
                
                if response.get("success"):
                    print("\n--- Directory Content ---")
                    print("Files:")
                    for file in response.get("files", []):
                        print(f"  - {file}")
                    print("Directories:")
                    for directory in response.get("directories", []):
                        print(f"  - {directory}")
                    print("------------------------")
                else:
                    print(f"Error: {response.get('error')}")
                    
            elif choice == "3":
                print("Exiting Claude Desktop...")
                break
            else:
                print("Invalid choice. Please try again.")


class IDEHost(MCPHost):
    """Example implementation of IDE Host"""
    
    def __init__(self, code_server_host: str = 'localhost', code_server_port: int = 5001):
        super().__init__(MCPClient(code_server_host, code_server_port))
        
    def run(self):
        """Run the IDE application"""
        print("IDE is running...")
        
        while True:
            print("\nIDE Options:")
            print("1. Get code completion suggestions")
            print("2. Exit")
            
            choice = input("Select an option (1-2): ")
            
            if choice == "1":
                language = input("Enter programming language (default: python): ") or "python"
                code = input("Enter code context: ")
                
                response = self.client.send_request("complete_code", {
                    "code": code,
                    "language": language
                })
                
                if response.get("success"):
                    print("\n--- Completion Suggestions ---")
                    for i, completion in enumerate(response.get("completions", []), 1):
                        print(f"{i}. {completion}")
                    print("----------------------------")
                else:
                    print(f"Error: {response.get('error')}")
                    
            elif choice == "2":
                print("Exiting IDE...")
                break
            else:
                print("Invalid choice. Please try again.")


# ===== Main Function =====

def run_demo():
    """Run the MCP demo"""
    server_choice = input("Which server to start? (1: File Server, 2: Code Server): ")
    
    if server_choice == "1":
        # Start file operation server
        server = FileOperationServer()
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Give the server time to start
        time.sleep(1)
        
        # Start Claude Desktop host
        host = ClaudeDesktopHost()
        host.run()
        
    elif server_choice == "2":
        # Start code completion server
        server = CodeCompletionServer()
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Give the server time to start
        time.sleep(1)
        
        # Start IDE host
        host = IDEHost()
        host.run()
        
    else:
        print("Invalid choice")


if __name__ == "__main__":
    run_demo()