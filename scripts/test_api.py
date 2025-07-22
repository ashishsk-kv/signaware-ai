#!/usr/bin/env python3
"""
Test script for SignAware AI APIs.
This script demonstrates how to use all the main endpoints with the new database schema.
"""

import asyncio
import httpx
import json
from typing import Optional
from uuid import uuid4

BASE_URL = "http://localhost:8000"

# Sample legal document for testing
SAMPLE_DOCUMENT = """
TERMS OF SERVICE

1. ACCEPTANCE OF TERMS
By accessing and using this service, you agree to be bound by the terms and conditions of this agreement.

2. PRIVACY AND DATA COLLECTION
We may collect personal information including but not limited to your name, email address, phone number, and usage data. This information may be shared with third parties for marketing purposes.

3. LIABILITY LIMITATION
IN NO EVENT SHALL THE COMPANY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL OR PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION, LOSS OF PROFITS, DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES.

4. TERMINATION
We reserve the right to terminate your account at any time, for any reason, without notice.

5. GOVERNING LAW
This agreement shall be governed by the laws of [JURISDICTION] and you hereby consent to the exclusive jurisdiction and venue of courts in [JURISDICTION].
"""

# Sample text with PII for testing
SAMPLE_PII_TEXT = """
Hello, my name is John Smith and I work at ABC Corporation. 
You can reach me at john.smith@abc-corp.com or call me at (555) 123-4567.
My social security number is 123-45-6789 and my credit card number is 4532-1234-5678-9012.
I live at 123 Main Street, Anytown, NY 12345.
"""

async def test_health_check():
    """Test the health check endpoint."""
    print("\n🏥 Testing Health Check...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=10.0)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Health check passed: {result['message']}")
            return True
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

async def test_create_user():
    """Test creating a test user."""
    print("\n👤 Testing User Creation...")
    
    user_data = {
        "email": f"testuser-{uuid4().hex[:8]}@example.com",
        "firstName": "Test",
        "lastName": "User",
        "role": "customer",
        "password": "testpassword123"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/users/",
                json=user_data,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            user_id = result['id']
            print(f"✅ User created successfully!")
            print(f"   - User ID: {user_id}")
            print(f"   - Email: {result['email']}")
            print(f"   - Name: {result['firstName']} {result['lastName']}")
            
            return user_id
            
        except Exception as e:
            print(f"❌ User creation failed: {e}")
            return None

async def test_create_document(user_id: str):
    """Test creating a document."""
    print("\n📄 Testing Document Creation...")
    
    document_data = {
        "title": "Sample Terms of Service",
        "content": SAMPLE_DOCUMENT,
        "type": "terms_of_service",
        "originalFileName": "terms_of_service.txt"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/documents/?user_id={user_id}",
                json=document_data,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            document_id = result['id']
            print(f"✅ Document created successfully!")
            print(f"   - Document ID: {document_id}")
            print(f"   - Title: {result['title']}")
            print(f"   - Type: {result['type']}")
            print(f"   - Status: {result['status']}")
            
            return document_id
            
        except Exception as e:
            print(f"❌ Document creation failed: {e}")
            return None

async def test_pii_masking_text():
    """Test the PII masking endpoint with raw text."""
    print("\n🔒 Testing PII Masking (Text)...")
    
    # Create a temporary user for this test
    user_id = str(uuid4())
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/pii/mask",
                json={"text": SAMPLE_PII_TEXT, "userId": user_id},
                timeout=60.0
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ PII masking completed!")
            print(f"   - Original length: {result['original_length']}")
            print(f"   - Masked length: {result['masked_length']}")
            print(f"   - Original: {SAMPLE_PII_TEXT[:100]}...")
            print(f"   - Masked: {result['masked_content'][:100]}...")
            
        except Exception as e:
            print(f"❌ PII masking failed: {e}")

async def test_document_analysis(document_id: str, user_id: str):
    """Test the document analysis endpoint."""
    print("\n📋 Testing Document Analysis...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/documents/{document_id}/analyze",
                json={"user_id": user_id},
                timeout=120.0
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Document analysis completed!")
            print(f"   - Document ID: {result['document_id']}")
            print(f"   - Status: {result['status']}")
            
            if result.get('analysis'):
                analysis = result['analysis']
                print(f"   - Risk Score: {analysis['risk_score']}/5")
                print(f"   - Confidence: {analysis['confidence_rating']}%")
                print(f"   - Summary: {analysis['summary'][:100]}...")
                print(f"   - Key Concerns: {len(analysis['key_concerns'])} identified")
                print(f"   - Red Flags: {len(analysis['red_flags'])} identified")
            else:
                print(f"   - Processing status: {result['status']}")
            
            return result.get('analysis') is not None
            
        except Exception as e:
            print(f"❌ Document analysis failed: {e}")
            return False

async def test_document_pii_masking(document_id: str, user_id: str):
    """Test PII masking on a document."""
    print("\n🔒 Testing Document PII Masking...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/pii/mask/document/{document_id}?user_id={user_id}",
                timeout=60.0
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Document PII masking completed!")
            print(f"   - Document ID: {result['document_id']}")
            print(f"   - Original length: {result['original_length']}")
            print(f"   - Masked length: {result['masked_length']}")
            print(f"   - Masked at: {result['masked_at']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Document PII masking failed: {e}")
            return False

async def test_chat_message(document_id: str, user_id: str, has_analysis: bool):
    """Test the non-streaming chat endpoint."""
    print("\n💬 Testing Chat Message...")
    
    session_id = f"test-session-{uuid4().hex[:8]}"
    message = "What are the main risks in this document?" if has_analysis else "Can you tell me about this document?"
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "message": message,
                "session_id": session_id,
                "document_id": document_id,
                "user_id": user_id
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/chat/message",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Chat response received!")
            print(f"   - Session ID: {result['session_id']}")
            print(f"   - Message ID: {result['message_id']}")
            print(f"   - Response: {result['response'][:200]}...")
            
            return session_id
            
        except Exception as e:
            print(f"❌ Chat failed: {e}")
            return None

async def test_chat_history(session_id: str, document_id: str, user_id: str):
    """Test the chat history endpoint."""
    print("\n📚 Testing Chat History...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/chat/history/{session_id}?document_id={document_id}&user_id={user_id}",
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Chat history retrieved!")
            print(f"   - Session ID: {result['session_id']}")
            print(f"   - Document ID: {result['document_id']}")
            print(f"   - Total messages: {result['total_messages']}")
            
            for i, msg in enumerate(result['messages'][-2:], 1):  # Show last 2 messages
                print(f"   - Message {i}: {msg['role']} - {msg['content'][:100]}...")
            
        except Exception as e:
            print(f"❌ Chat history failed: {e}")

async def test_get_user_documents(user_id: str):
    """Test getting user documents."""
    print("\n📂 Testing Get User Documents...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/documents/?user_id={user_id}",
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ User documents retrieved!")
            print(f"   - Total documents: {len(result)}")
            
            for doc in result:
                print(f"   - {doc['title']} ({doc['type']}) - {doc['status']}")
            
        except Exception as e:
            print(f"❌ Get user documents failed: {e}")

async def main():
    """Run all tests."""
    print("🚀 Starting SignAware AI API Tests (Updated Schema)...")
    print(f"Base URL: {BASE_URL}")
    
    # Test health check first
    if not await test_health_check():
        print("\n❌ Health check failed. Make sure the server is running.")
        return
    
    # Create a test user
    user_id = await test_create_user()
    if not user_id:
        print("\n❌ Cannot proceed without a user ID.")
        return
    
    # Create a test document
    document_id = await test_create_document(user_id)
    if not document_id:
        print("\n❌ Cannot proceed without a document ID.")
        return
    
    # Test PII masking with text
    await test_pii_masking_text()
    
    # Test document PII masking
    await test_document_pii_masking(document_id, user_id)
    
    # Test document analysis
    has_analysis = await test_document_analysis(document_id, user_id)
    
    # Test chat with document context
    session_id = await test_chat_message(document_id, user_id, has_analysis)
    
    # Test chat history (if chat succeeded)
    if session_id:
        await test_chat_history(session_id, document_id, user_id)
    
    # Test get user documents
    await test_get_user_documents(user_id)
    
    print("\n✨ All tests completed!")
    print("\n📖 Next steps:")
    print(f"   - Visit {BASE_URL}/docs for interactive API documentation")
    print(f"   - Visit {BASE_URL} for API overview")
    print("   - Check the database for stored results")
    print(f"   - Test user ID: {user_id}")
    print(f"   - Test document ID: {document_id}")

if __name__ == "__main__":
    asyncio.run(main()) 