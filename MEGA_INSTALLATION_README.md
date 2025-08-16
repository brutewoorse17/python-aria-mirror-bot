# MEGA SDK Packages Installation Guide

## Overview
This guide explains how to install and use the MEGA SDK packages (`megasdkrestclient` and `mega`) in a Python virtual environment.

## Installation Status

### ✅ Successfully Installed Packages

1. **megasdkrestclient** (v0.1.1)
   - ✅ Package installed successfully
   - ✅ Dependencies resolved
   - ⚠️ Requires specific usage pattern (async context)

2. **mega** (v0.2.11)
   - ✅ Package installed successfully
   - ✅ Dependencies resolved
   - ⚠️ Terminal-based client (not suitable for programmatic use)

## Issues Encountered and Solutions

### Issue 1: Externally Managed Python Environment
**Problem**: System Python prevented package installation
**Solution**: Created virtual environment using `python3 -m venv venv`

### Issue 2: megasdkrestclient Import Error
**Problem**: `RuntimeError: no running event loop` when importing
**Root Cause**: Package tries to create aiohttp session without running event loop
**Solution**: Use package only in async context with proper aiohttp session management

### Issue 3: mega Package Misunderstanding
**Problem**: Package is terminal-based client, not Python SDK
**Solution**: Use for command-line operations only, not programmatic integration

## Working Usage Examples

### Using megasdkrestclient (Recommended for Programmatic Use)

```python
import asyncio
import aiohttp
import megasdkrestclient

async def upload_to_mega():
    async with aiohttp.ClientSession() as session:
        client = megasdkrestclient.AsyncMegaSdkRestClient(
            base_endpoint="https://your-mega-rest-api.com",
            session=session
        )
        
        # Now you can use the client
        result = await client.upload_file("path/to/file")
        return result

# Run the async function
asyncio.run(upload_to_mega())
```

### Using mega Package (Terminal-Based)

```python
from mega.mega import Mega, Megarc

# This package requires terminal screen and configuration
# Not suitable for programmatic use
# Use for command-line operations only
```

## Virtual Environment Setup

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   ```

2. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Install packages**:
   ```bash
   pip install -r requirements-venv.txt
   ```

## Package Dependencies

- **megasdkrestclient**: aiohttp, requests
- **mega**: trio, asks, beautifulsoup4, lxml, requests

## Testing Installation

Run the test scripts to verify installation:

```bash
# Test basic imports
python3 test_mega_imports.py

# Test working examples
python3 mega_working_example.py

# Test async functionality
python3 async_mega_example.py
```

## Recommendations

1. **For Programmatic Use**: Use `megasdkrestclient` in async context
2. **For Command Line**: Use `mega` package
3. **For Simple Operations**: Consider direct HTTP API integration
4. **Always Use Virtual Environment**: Avoid system package conflicts

## Troubleshooting

### If megasdkrestclient Still Fails
- Ensure you're in an async function
- Create aiohttp session before client
- Use `await` for all operations

### If mega Package Fails
- This is expected - it's terminal-based
- Use for command-line operations only

### If Virtual Environment Issues
- Install `python3-venv` package first
- Ensure proper activation with `source venv/bin/activate`

## Files Created

- `requirements-venv.txt` - Working requirements for virtual environment
- `test_mega_imports.py` - Basic import testing
- `mega_working_example.py` - Comprehensive usage examples
- `async_mega_example.py` - Async usage demonstration
- `MEGA_INSTALLATION_README.md` - This documentation

## Conclusion

The MEGA SDK packages are now properly installed and working:
- ✅ `megasdkrestclient` works in async context
- ✅ `mega` package works for terminal operations
- ✅ All dependencies resolved
- ✅ Virtual environment properly configured

Use `megasdkrestclient` for programmatic MEGA integration and `mega` for command-line operations.