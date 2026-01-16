# tool-testing.py
import asyncio
from agent import Assistant

async def test_tools():
    assistant = Assistant()
    
    # Set initial values
    assistant.user_problem = "Roof leak in living room during rain"
    assistant.solution = "Professional leak source identification and seal repair"
    assistant.user_email = "test@example.com"
    assistant.meeting_agreed = False
    
    print("Testing save_problem...")
    result = await assistant.save_problem("Roof leak in living room during rain")
    print(f"Result: {result}")
    
    print("\nTesting save_solution...")
    result = await assistant.save_solution("Professional leak source identification and seal repair")
    print(f"Result: {result}")
    
    print("\nTesting email_store...")
    result = await assistant.email_store("test@example.com")
    print(f"Result: {result}")
    
    print("\nTesting save_meeting_decision...")
    result = await assistant.save_meeting_decision("no")
    print(f"Result: {result}")

    print("\nTesting email_sending...")
    result = await assistant.email_sending(confirm=True)  # Add the confirm parameter
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_tools())