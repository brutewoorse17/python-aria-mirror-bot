#!/usr/bin/env python3
"""
Async example demonstrating proper usage of megasdkrestclient
This shows how to work around the import issues
"""

import asyncio
import aiohttp

async def test_megasdkrestclient_async():
    """Test megasdkrestclient in proper async context"""
    try:
        import megasdkrestclient
        
        print("✓ megasdkrestclient imported successfully")
        
        # Create aiohttp session
        async with aiohttp.ClientSession() as session:
            # Create the client with the session
            client = megasdkrestclient.AsyncMegaSdkRestClient(
                base_endpoint="https://your-mega-rest-api.com",
                session=session
            )
            print("✓ Async MEGA client created successfully")
            
            # Example of how you would use it
            # response = await client.get_files()
            # print(f"Response: {response}")
            
            return client
            
    except Exception as e:
        print(f"✗ Error in async test: {e}")
        return None

async def main():
    """Main async function"""
    print("Testing MEGA SDK REST Client in Async Context\n")
    print("="*50)
    
    # Test the async client
    client = await test_megasdkrestclient_async()
    
    if client:
        print("\n✓ SUCCESS: megasdkrestclient is working in async context")
        print("   You can now use it for MEGA operations")
    else:
        print("\n✗ FAILED: megasdkrestclient still has issues")
    
    print("\n" + "="*50)
    print("USAGE NOTES:")
    print("1. Always use megasdkrestclient in an async function")
    print("2. Create aiohttp session before creating the client")
    print("3. Pass the session to the client constructor")
    print("4. Use await for all client operations")
    
    print("\nExample usage:")
    print("async def upload_file():")
    print("    async with aiohttp.ClientSession() as session:")
    print("        client = megasdkrestclient.AsyncMegaSdkRestClient(base_url, session)")
    print("        result = await client.upload_file(file_path)")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())