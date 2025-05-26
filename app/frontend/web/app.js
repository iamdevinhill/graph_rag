// Configuration
const API_URL = '/api';

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const fileInfo = document.getElementById('fileInfo');
const uploadButton = document.getElementById('uploadButton');
const refreshGraphButton = document.getElementById('refreshGraph');
const graphVisualization = document.getElementById('graphVisualization');

// Initialize graph visualization
let network = null;
let isProcessing = false;

// Status message types
const STATUS_TYPES = {
    INFO: 'info',
    SUCCESS: 'success',
    WARNING: 'warning',
    ERROR: 'error',
    PROGRESS: 'progress'
};

// Status message queue
let statusQueue = [];
let isProcessingStatus = false;

// Event Listeners
sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

dropZone.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    fileInput.click();
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

uploadButton.addEventListener('click', (e) => {
    e.preventDefault();
    uploadDocument();
});

refreshGraphButton.addEventListener('click', () => {
    refreshGraphButton.classList.add('rotating');
    updateGraphVisualization().finally(() => {
        refreshGraphButton.classList.remove('rotating');
    });
});

// Initialize graph visualization
updateGraphVisualization();

// Functions
function handleFileSelect(file) {
    if (file.type === 'application/pdf' || file.type === 'text/plain') {
        fileInfo.innerHTML = `
            <i class="fas fa-file"></i>
            <span>${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
        `;
        // Show and enable upload button
        uploadButton.style.display = 'inline-flex';
        uploadButton.disabled = false;
        uploadButton.innerHTML = '<i class="fas fa-upload"></i> Upload Document';
        dropZone.classList.add('file-selected');
    } else {
        showStatus('Please select a PDF or text file.', STATUS_TYPES.ERROR);
        fileInfo.textContent = '';
        uploadButton.style.display = 'none';
        uploadButton.disabled = true;
        dropZone.classList.remove('file-selected');
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showStatus(message, type = STATUS_TYPES.INFO, duration = 5000) {
    const status = {
        message,
        type,
        duration,
        timestamp: Date.now()
    };
    
    statusQueue.push(status);
    processStatusQueue();
}

function processStatusQueue() {
    if (isProcessingStatus || statusQueue.length === 0) return;
    
    isProcessingStatus = true;
    const status = statusQueue.shift();
    
    const statusContainer = document.getElementById('statusContainer');
    const statusElement = document.createElement('div');
    statusElement.className = `status-message ${status.type}`;
    
    // Add icon based on status type
    let icon = '';
    switch (status.type) {
        case STATUS_TYPES.SUCCESS:
            icon = '<i class="fas fa-check-circle"></i>';
            break;
        case STATUS_TYPES.ERROR:
            icon = '<i class="fas fa-exclamation-circle"></i>';
            break;
        case STATUS_TYPES.WARNING:
            icon = '<i class="fas fa-exclamation-triangle"></i>';
            break;
        case STATUS_TYPES.PROGRESS:
            icon = '<i class="fas fa-spinner fa-spin"></i>';
            break;
        default:
            icon = '<i class="fas fa-info-circle"></i>';
    }
    
    statusElement.innerHTML = `
        ${icon}
        <span>${status.message}</span>
        ${status.type === STATUS_TYPES.PROGRESS ? '<div class="progress-bar"></div>' : ''}
    `;
    
    statusContainer.appendChild(statusElement);
    
    // Animate in
    setTimeout(() => statusElement.classList.add('show'), 10);
    
    // Remove after duration
    setTimeout(() => {
        statusElement.classList.remove('show');
        setTimeout(() => {
            statusElement.remove();
            isProcessingStatus = false;
            processStatusQueue();
        }, 300);
    }, status.duration);
}

async function uploadDocument() {
    const file = fileInput.files[0];
    if (!file) {
        showStatus('Please select a file first.', STATUS_TYPES.ERROR);
        return;
    }

    showStatus('Preparing document for upload...', STATUS_TYPES.PROGRESS);
    uploadButton.disabled = true;
    uploadButton.innerHTML = '<span class="spinner"></span> Uploading...';

    try {
        const formData = new FormData();
        formData.append('file', file);

        // Upload phase
        showStatus('Uploading document...', STATUS_TYPES.PROGRESS);
        const response = await fetch(`${API_URL}/documents`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        // Processing phase
        showStatus('Processing document chunks...', STATUS_TYPES.PROGRESS);
        
        // Update graph visualization
        await updateGraphVisualization();
        
        showStatus('Document uploaded and processed successfully!', STATUS_TYPES.SUCCESS);
        
        // Reset file input and info
        fileInput.value = '';
        fileInfo.textContent = '';
        uploadButton.style.display = 'none';
        dropZone.classList.remove('file-selected');
        
        // Add a system message to the chat
        addMessageToChat('system', `Document "${file.name}" has been uploaded and processed. You can now ask questions about it.`);
    } catch (error) {
        let errorMessage = 'Error uploading document';
        if (error.message.includes('No text content could be extracted')) {
            errorMessage = 'The file appears to be empty or contains no extractable text. Please check the file and try again.';
        } else if (error.message.includes('file size')) {
            errorMessage = 'The file is too large. Please try a smaller file.';
        } else {
            errorMessage = `Error uploading document: ${error.message}`;
        }
        showStatus(errorMessage, STATUS_TYPES.ERROR);
        
        // Reset upload button state
        uploadButton.disabled = false;
        uploadButton.innerHTML = '<i class="fas fa-upload"></i> Upload Document';
    }
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isProcessing) return;

    isProcessing = true;
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="spinner"></span>';

    // Add user message to chat
    addMessageToChat('user', message);
    messageInput.value = '';

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: message })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';
        let context = '';

        // Create initial assistant message
        addMessageToChat('assistant', '');

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.chunk) {
                            assistantMessage += data.chunk;
                            updateAssistantMessage(assistantMessage);
                        } else if (data.context) {
                            context = data.context;
                            // Add context to the existing message
                            const lastMessage = chatMessages.lastElementChild;
                            if (lastMessage && lastMessage.classList.contains('assistant')) {
                                const contextDiv = document.createElement('div');
                                contextDiv.className = 'message-context';
                                contextDiv.innerHTML = `
                                    <i class="fas fa-info-circle"></i>
                                    <span>Context: ${context}</span>
                                `;
                                lastMessage.appendChild(contextDiv);
                            }
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, STATUS_TYPES.ERROR);
        // Remove the empty assistant message if there was an error
        const lastMessage = chatMessages.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('assistant')) {
            lastMessage.remove();
        }
    } finally {
        isProcessing = false;
        sendButton.disabled = false;
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i> Send';
    }
}

function addMessageToChat(role, content, context = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    messageDiv.appendChild(contentDiv);

    if (context) {
        const contextDiv = document.createElement('div');
        contextDiv.className = 'message-context';
        contextDiv.innerHTML = `
            <i class="fas fa-info-circle"></i>
            <span>Context: ${context}</span>
        `;
        messageDiv.appendChild(contextDiv);
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updateAssistantMessage(content) {
    const lastMessage = chatMessages.lastElementChild;
    if (lastMessage && lastMessage.classList.contains('assistant')) {
        const contentDiv = lastMessage.querySelector('.message-content');
        if (contentDiv) {
            contentDiv.textContent = content;
        }
    }
}

async function updateGraphVisualization() {
    try {
        const response = await fetch(`${API_URL}/graph`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        renderGraph(data);
    } catch (error) {
        showStatus(`Error fetching graph data: ${error.message}`, STATUS_TYPES.ERROR);
    }
}

function renderGraph(graphData) {
    // Create nodes and edges for vis.js
    const nodes = new vis.DataSet(graphData.nodes.map(node => ({
        id: node.id,
        label: node.label,
        title: node.properties?.description || '',
        color: node.type === 'Document' ? '#3B82F6' : '#10B981',
        font: {
            color: '#FFFFFF',
            size: 14,
            face: 'Inter'
        },
        shape: node.type === 'Document' ? 'dot' : 'circle',
        size: node.type === 'Document' ? 20 : 16
    })));
    
    const edges = new vis.DataSet(graphData.relationships.map(rel => ({
        from: rel.startNode,
        to: rel.endNode,
        label: rel.type,
        arrows: 'to',
        color: {
            color: '#60A5FA',
            highlight: '#93C5FD',
            opacity: 0.8
        },
        font: {
            color: '#CBD5E1',
            size: 12,
            face: 'Inter',
            align: 'middle'
        },
        smooth: {
            type: 'curvedCW',
            roundness: 0.2
        }
    })));
    
    // Create network
    const container = document.getElementById('graphVisualization');
    const data = { nodes, edges };
    const options = {
        nodes: {
            borderWidth: 2,
            borderWidthSelected: 3,
            shadow: true
        },
        edges: {
            width: 2,
            widthSelected: 3,
            shadow: true
        },
        physics: {
            stabilization: {
                iterations: 100,
                updateInterval: 50
            },
            barnesHut: {
                gravitationalConstant: -80000,
                springConstant: 0.001,
                springLength: 200
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true
        }
    };
    
    if (network) {
        network.destroy();
    }
    
    network = new vis.Network(container, data, options);
    
    // Add click event for node details
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            if (node.title) {
                showStatus(node.title, STATUS_TYPES.INFO);
            }
        }
    });

    // Add hover event for better interaction
    network.on('hoverNode', function(params) {
        document.body.style.cursor = 'pointer';
    });

    network.on('blurNode', function(params) {
        document.body.style.cursor = 'default';
    });
} 