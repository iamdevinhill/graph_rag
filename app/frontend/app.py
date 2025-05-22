import streamlit as st
import requests
import json
import os
import PyPDF2
import io
import logging
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(
    page_title="Document Chat System",
    page_icon="💬",
    layout="wide"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("RAG Chat System")
st.markdown("""
This application allows you to:
1. Upload PDF or text documents
2. Chat with an AI about the content
""")

# Sidebar for document upload
with st.sidebar:
    st.header("Document Upload")
    st.markdown("""
    **Steps to upload:**
    1. Select your PDF or text file below
    2. Click the 'Upload Document' button that appears
    3. Wait for the success message
    4. Then you can start asking questions!
    """)
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'txt'])
    
    if uploaded_file is not None:
        st.write(f"File type: {uploaded_file.type}")
        st.write(f"File size: {uploaded_file.size} bytes")
        
        # Show upload button with more prominent styling
        if st.button("📤 Upload Document", type="primary"):
            try:
                logger.info(f"Processing uploaded file: {uploaded_file.name}")
                if uploaded_file.type == "application/pdf":
                    # Read PDF file
                    logger.info("Reading PDF file")
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    document_text = ""
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        document_text += page_text
                        logger.info(f"Extracted {len(page_text)} characters from page")
                    logger.info(f"Total extracted text length: {len(document_text)} characters")
                    if len(document_text.strip()) == 0:
                        st.error("Warning: No text could be extracted from the PDF. The PDF might be scanned or image-based.")
                        st.stop()
                else:
                    # Read text file
                    logger.info("Reading text file")
                    document_text = uploaded_file.getvalue().decode("utf-8")
                    logger.info(f"Read {len(document_text)} characters from text file")
                
                logger.info(f"Sending document to API at {API_URL}/documents")
                # Show a spinner while uploading
                with st.spinner("Uploading document..."):
                    # Create metadata with file information
                    metadata = {
                        "filename": uploaded_file.name,
                        "file_type": uploaded_file.type,
                        "file_size": uploaded_file.size,
                        "upload_time": str(datetime.datetime.now())
                    }
                    payload = {
                        "content": document_text,
                        "metadata": metadata
                    }
                    logger.info(f"Request payload size: {len(str(payload))} bytes")
                    try:
                        response = requests.post(
                            f"{API_URL}/documents",
                            json=payload,
                            timeout=30  # Add timeout
                        )
                        logger.info(f"API response status: {response.status_code}")
                        logger.info(f"API response: {response.text}")
                        response.raise_for_status()
                        logger.info("Document uploaded successfully")
                        st.success("Document uploaded successfully!")
                    except requests.exceptions.Timeout:
                        logger.error("Request timed out while uploading document")
                        st.error("The upload took too long. Please try again.")
                    except requests.exceptions.ConnectionError as e:
                        logger.error(f"Connection error while uploading document: {str(e)}")
                        st.error("Failed to connect to the API. Please try again.")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Request error while uploading document: {str(e)}")
                        st.error(f"Error uploading document: {str(e)}")
                    except Exception as e:
                        logger.error(f"Unexpected error while uploading document: {str(e)}")
                        st.error(f"An unexpected error occurred: {str(e)}")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error while uploading document: {str(e)}")
                st.error("Failed to connect to the API. Please try again.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error while uploading document: {str(e)}")
                st.error(f"Error uploading document: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error while uploading document: {str(e)}")
                st.error(f"An unexpected error occurred: {str(e)}")

# Main chat interface
st.header("Chat")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "context" in message:
            with st.expander("View Context"):
                st.write(message["context"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    try:
        logger.info(f"Sending query to API: {prompt}")
        with st.spinner("Getting answer..."):
            response = requests.post(
                f"{API_URL}/query",
                json={"text": prompt}
            )
            response.raise_for_status()
            result = response.json()
            logger.info("Received response from API")
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "context": result.get("context", "No relevant context found.")
            })
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.write(result["response"])
                if result.get("context"):
                    with st.expander("View Context"):
                        st.write(result["context"])
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error while querying: {str(e)}")
        st.error("Failed to connect to the API. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while querying: {str(e)}")
        st.error(f"Error getting answer: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while querying: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}") 