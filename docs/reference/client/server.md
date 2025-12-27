# Server

The `Server` class is the main entry point for the WhatsNext client library.

## Usage

```python
from whatsnext.api.client import Server

# Connect to the server
server = Server("http://localhost:8000")

# Get all projects
projects = server.projects

# Get or create a specific project
project = server.get_project("my-project")
```

## API Reference

::: whatsnext.api.client.server.Server
