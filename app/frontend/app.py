import streamlit as st
import requests
import json
import os
import PyPDF2
import io
import logging
import datetime
import sseclient
import streamlit.components.v1 as components
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_URL = os.getenv("API_URL", "http://api:8000")

# Set page config with dark theme
st.set_page_config(
    page_title="Graph RAG Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode
st.markdown("""
<style>
    .stApp {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .stButton>button {
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #3D3D3D;
    }
    .stButton>button:hover {
        background-color: #3D3D3D;
        border-color: #4D4D4D;
    }
    .stTextInput>div>div>input {
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #3D3D3D;
    }
    .stTextInput>div>div>input:focus {
        border-color: #4D4D4D;
    }
    .stSidebar {
        background-color: #2D2D2D;
    }
    .stExpander {
        background-color: #2D2D2D;
        border: 1px solid #3D3D3D;
    }
    .stChatMessage {
        background-color: #2D2D2D;
        border: 1px solid #3D3D3D;
    }
    .stChatMessage:hover {
        background-color: #3D3D3D;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "graph_data" not in st.session_state:
    st.session_state.graph_data = None

st.title("Graph RAG Chat")
st.markdown("""
This application allows you to:
1. Upload PDF or text documents
2. Chat with an AI about the content
3. Visualize the document graph structure
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
        
        if st.button("📤 Upload Document", type="primary"):
            try:
                # Create a placeholder for status messages
                status_placeholder = st.empty()
                
                # Initialize progress bar
                progress_bar = st.progress(0)
                status_placeholder.info("Starting document processing...")
                
                # Step 1: Extract text from file
                progress_bar.progress(20)
                status_placeholder.info("Extracting text from file...")
                
                if uploaded_file.type == "application/pdf":
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    document_text = ""
                    total_pages = len(pdf_reader.pages)
                    
                    for i, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        document_text += page_text
                        # Update progress based on page extraction
                        progress = 20 + (i + 1) / total_pages * 30
                        progress_bar.progress(int(progress))
                        status_placeholder.info(f"Extracting text from page {i + 1} of {total_pages}...")
                    
                    if len(document_text.strip()) == 0:
                        status_placeholder.error("Warning: No text could be extracted from the PDF. The PDF might be scanned or image-based.")
                        st.stop()
                else:
                    document_text = uploaded_file.getvalue().decode("utf-8")
                
                # Step 2: Prepare metadata
                progress_bar.progress(50)
                status_placeholder.info("Preparing document metadata...")
                
                metadata = {
                    "filename": uploaded_file.name,
                    "file_type": uploaded_file.type,
                    "file_size": uploaded_file.size,
                    "upload_time": str(datetime.datetime.now())
                }
                
                # Step 3: Upload to API
                progress_bar.progress(60)
                status_placeholder.info("Uploading document to server...")
                
                payload = {
                    "content": document_text,
                    "metadata": metadata
                }
                
                try:
                    response = requests.post(
                        f"{API_URL}/documents",
                        json=payload,
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    # Step 4: Process chunks
                    progress_bar.progress(80)
                    status_placeholder.info("Processing document chunks...")
                    
                    # Step 5: Fetch updated graph
                    progress_bar.progress(90)
                    status_placeholder.info("Updating document graph...")
                    
                    graph_response = requests.get(f"{API_URL}/graph")
                    if graph_response.status_code == 200:
                        st.session_state.graph_data = graph_response.json()
                    
                    # Complete
                    progress_bar.progress(100)
                    status_placeholder.success("Document uploaded and processed successfully!")
                    
                    # Add a small delay to show the success message
                    time.sleep(1)
                    
                    # Clear the progress bar and status
                    progress_bar.empty()
                    status_placeholder.empty()
                    
                except requests.exceptions.RequestException as e:
                    error_message = str(e)
                    if "timeout" in error_message.lower():
                        error_message = "The server took too long to respond. Please try again."
                    elif "connection" in error_message.lower():
                        error_message = "Could not connect to the server. Please check your internet connection."
                    status_placeholder.error(f"Error uploading document: {error_message}")
                    progress_bar.empty()
                    
            except Exception as e:
                error_message = str(e)
                if "No text content could be extracted" in error_message:
                    error_message = "The file appears to be empty or contains no extractable text. Please check the file and try again."
                elif "file size" in error_message.lower():
                    error_message = "The file is too large. Please try a smaller file."
                st.error(f"An unexpected error occurred: {error_message}")
                progress_bar.empty()

# Main content area with two columns
col1, col2 = st.columns([2, 1])

with col1:
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
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        try:
            response_placeholder = st.empty()
            context_placeholder = st.empty()
            full_response = ""
            
            response = requests.post(
                f"{API_URL}/query",
                json={"text": prompt},
                stream=True
            )
            response.raise_for_status()
            
            client = sseclient.SSEClient(response)
            for event in client.events():
                try:
                    data = json.loads(event.data)
                    if "chunk" in data:
                        full_response += data["chunk"]
                        response_placeholder.write(full_response)
                    elif "context" in data:
                        context = data["context"]
                        with context_placeholder.expander("View Context"):
                            st.write(context)
                except json.JSONDecodeError:
                    continue
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "context": context if 'context' in locals() else "No relevant context found."
            })
            
        except Exception as e:
            st.error(f"Error getting answer: {str(e)}")

with col2:
    st.header("Document Graph")
    
    # Add a refresh button for the graph
    if st.button("🔄 Refresh Graph"):
        try:
            response = requests.get(f"{API_URL}/graph")
            if response.status_code == 200:
                st.session_state.graph_data = response.json()
        except Exception as e:
            st.error(f"Error refreshing graph: {str(e)}")
    
    # Display graph visualization
    if st.session_state.graph_data:
        # Create HTML for graph visualization
        graph_html = f"""
        <div id="graph-container" style="width: 100%; height: 600px; background-color: #2D2D2D; border: 1px solid #3D3D3D;"></div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet" type="text/css" />
        <script>
            const nodes = new vis.DataSet({json.dumps(st.session_state.graph_data['nodes'])});
            const edges = new vis.DataSet({json.dumps(st.session_state.graph_data['relationships'])});
            
            const container = document.getElementById('graph-container');
            const data = {{ nodes, edges }};
            const options = {{
                nodes: {{
                    shape: 'dot',
                    size: 16,
                    color: {{
                        background: '#4D4D4D',
                        border: '#5D5D5D',
                        highlight: {{
                            background: '#6D6D6D',
                            border: '#7D7D7D'
                        }}
                    }},
                    font: {{
                        color: '#FFFFFF'
                    }}
                }},
                edges: {{
                    color: {{
                        color: '#5D5D5D',
                        highlight: '#6D6D6D'
                    }},
                    font: {{
                        color: '#FFFFFF'
                    }}
                }},
                physics: {{
                    stabilization: true,
                    barnesHut: {{
                        gravitationalConstant: -80000,
                        springConstant: 0.001,
                        springLength: 200
                    }}
                }}
            }};
            
            const network = new vis.Network(container, data, options);
            
            network.on('click', function(params) {{
                if (params.nodes.length > 0) {{
                    const nodeId = params.nodes[0];
                    const node = nodes.get(nodeId);
                    if (node.properties && node.properties.description) {{
                        alert(node.properties.description);
                    }}
                }}
            }});
        </script>
        """
        components.html(graph_html, height=600)
    else:
        st.info("Upload a document to see the graph visualization.") 