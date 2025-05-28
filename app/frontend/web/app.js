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
const selectFileButton = document.getElementById('selectFileButton');
const refreshGraphButton = document.getElementById('refreshGraph');
const graphVisualization = document.getElementById('graphVisualization');
const nodeDetails = document.getElementById('nodeDetails');

// Graph Controls
const zoomInButton = document.getElementById('zoomIn');
const zoomOutButton = document.getElementById('zoomOut');
const resetViewButton = document.getElementById('resetView');
const togglePhysicsButton = document.getElementById('togglePhysics');

// Initialize graph visualization
let network = null;
let isProcessing = false;
let selectedFile = null;
let physicsEnabled = true;

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
document.addEventListener('DOMContentLoaded', () => {
    // Initialize event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Enhanced dropzone event listeners
    dropZone.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        fileInput.click();
    });

    dropZone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInput.click();
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', (e) => {
        if (!dropZone.contains(e.relatedTarget)) {
            dropZone.classList.remove('dragover');
        }
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

    selectFileButton.addEventListener('click', (e) => {
        e.preventDefault();
        fileInput.click();
    });

    refreshGraphButton.addEventListener('click', () => {
        refreshGraphButton.classList.add('rotating');
        updateGraphVisualization().finally(() => {
            refreshGraphButton.classList.remove('rotating');
        });
    });

    // Initialize upload button state
    updateUploadButtonState();

    // Initialize graph visualization
    updateGraphVisualization();
});

zoomInButton.addEventListener('click', () => {
    if (network) {
        const scale = network.getScale();
        network.moveTo({
            scale: scale * 1.2,
            animation: true
        });
    }
});

zoomOutButton.addEventListener('click', () => {
    if (network) {
        const scale = network.getScale();
        network.moveTo({
            scale: scale * 0.8,
            animation: true
        });
    }
});

resetViewButton.addEventListener('click', () => {
    if (network) {
        network.fit({
            animation: true
        });
    }
});

// Add event listener for physics toggle
togglePhysicsButton.addEventListener('click', () => {
    if (network) {
        physicsEnabled = !physicsEnabled;
        network.setOptions({
            physics: {
                enabled: physicsEnabled,
                barnesHut: {
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 200,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.1
                },
                stabilization: {
                    enabled: physicsEnabled,
                    iterations: 1000,
                    updateInterval: 50,
                    fit: true
                }
            }
        });
        
        // Update button appearance
        togglePhysicsButton.classList.toggle('active', physicsEnabled);
        togglePhysicsButton.title = physicsEnabled ? 'Disable Physics' : 'Enable Physics';
    }
});

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
        selectedFile = file;
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
    if (!selectedFile) {
        showStatus('Please select a file first.', STATUS_TYPES.ERROR);
        return;
    }

    showStatus('Preparing document for upload...', STATUS_TYPES.PROGRESS);
    uploadButton.disabled = true;
    uploadButton.innerHTML = '<span class="spinner"></span> Uploading...';

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

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
        addMessageToChat('system', `Document "${selectedFile.name}" has been uploaded and processed. You can now ask questions about it.`);
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
                            // Add context to the existing message using the collapsible structure
                            const lastMessage = chatMessages.lastElementChild;
                            if (lastMessage && lastMessage.classList.contains('assistant')) {
                                const contextDiv = document.createElement('div');
                                contextDiv.className = 'message-context';
                                
                                const contextHeader = document.createElement('div');
                                contextHeader.className = 'message-context-header collapsed';
                                contextHeader.innerHTML = `
                                    <i class="fas fa-chevron-down"></i>
                                    <span>Context</span>
                                `;
                                
                                const contextContent = document.createElement('div');
                                contextContent.className = 'message-context-content';
                                contextContent.textContent = context;
                                
                                contextDiv.appendChild(contextHeader);
                                contextDiv.appendChild(contextContent);
                                
                                // Add click handler for toggling
                                contextHeader.addEventListener('click', (e) => {
                                    e.stopPropagation();
                                    const isCollapsed = contextHeader.classList.contains('collapsed');
                                    contextHeader.classList.toggle('collapsed');
                                    contextContent.classList.toggle('expanded');
                                });
                                
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
        
        const contextHeader = document.createElement('div');
        contextHeader.className = 'message-context-header collapsed';
        contextHeader.innerHTML = `
            <i class="fas fa-chevron-down"></i>
            <span>Context</span>
        `;
        
        const contextContent = document.createElement('div');
        contextContent.className = 'message-context-content';
        contextContent.textContent = context;
        
        contextDiv.appendChild(contextHeader);
        contextDiv.appendChild(contextContent);
        
        // Add click handler for toggling
        contextHeader.addEventListener('click', (e) => {
            e.stopPropagation();
            const isCollapsed = contextHeader.classList.contains('collapsed');
            contextHeader.classList.toggle('collapsed');
            contextContent.classList.toggle('expanded');
        });
        
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
        // Show loading state
        const loadingElement = document.querySelector('.graph-loading');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }

        const response = await fetch(`${API_URL}/graph`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // Hide loading state
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        renderGraph(data);
    } catch (error) {
        showStatus(`Error fetching graph data: ${error.message}`, STATUS_TYPES.ERROR);
        // Hide loading state on error
        const loadingElement = document.querySelector('.graph-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
}

function renderGraph(graphData) {
    // Create nodes and edges for vis.js
    const nodes = new vis.DataSet(graphData.nodes.map(node => ({
        id: node.id,
        label: node.label || node.name || node.title || 'Unnamed',
        title: createNodeTooltip(node),
        group: node.type || 'default',
        color: {
            background: getNodeColor(node.type),
            border: getNodeBorderColor(node.type),
            highlight: {
                background: getNodeHighlightColor(node.type),
                border: getNodeBorderColor(node.type)
            },
            hover: {
                background: getNodeHighlightColor(node.type),
                border: getNodeBorderColor(node.type)
            }
        },
        font: {
            color: '#FFFFFF',
            size: 14,
            face: 'Inter',
            strokeWidth: 2,
            strokeColor: '#1E293B',
            align: 'center'
        },
        shape: getNodeShape(node.type),
        size: getNodeSize(node.type),
        borderWidth: 2,
        borderWidthSelected: 3,
        shadow: {
            enabled: true,
            color: 'rgba(0,0,0,0.2)',
            size: 10,
            x: 5,
            y: 5
        },
        properties: node.properties || {}
    })));
    
    const edges = new vis.DataSet(graphData.relationships.map(rel => ({
        from: rel.startNode,
        to: rel.endNode,
        label: rel.type,
        title: createRelationshipTooltip(rel),
        arrows: {
            to: { 
                enabled: true, 
                scaleFactor: 0.8, 
                type: 'arrow',
                color: getEdgeColor(rel.type)
            }
        },
        color: {
            color: getEdgeColor(rel.type),
            highlight: getEdgeHighlightColor(rel.type),
            hover: getEdgeHighlightColor(rel.type),
            opacity: 0.8
        },
        font: {
            color: '#CBD5E1',
            size: 12,
            face: 'Inter',
            align: 'middle',
            strokeWidth: 2,
            strokeColor: '#1E293B',
            background: 'rgba(15, 23, 42, 0.8)',
            padding: 4
        },
        smooth: {
            type: 'curvedCW',
            roundness: 0.2,
            forceDirection: 'none'
        },
        width: 2,
        widthSelected: 3,
        shadow: {
            enabled: true,
            color: 'rgba(0,0,0,0.2)',
            size: 10,
            x: 5,
            y: 5
        },
        properties: rel.properties || {}
    })));
    
    // Create network
    const container = document.getElementById('graphVisualization');
    const data = { nodes, edges };
    const options = {
        nodes: {
            borderWidth: 2,
            borderWidthSelected: 3,
            shadow: true,
            scaling: {
                min: 16,
                max: 32,
                label: {
                    enabled: true,
                    min: 14,
                    max: 16,
                    maxVisible: 16
                }
            }
        },
        edges: {
            width: 2,
            widthSelected: 3,
            shadow: true,
            selectionWidth: 3,
            hoverWidth: 3,
            smooth: {
                type: 'curvedCW',
                roundness: 0.2,
                forceDirection: 'none'
            }
        },
        groups: {
            Document: {
                color: { background: '#3B82F6', border: '#2563EB' },
                shape: 'dot',
                size: 20
            },
            Chunk: {
                color: { background: '#10B981', border: '#059669' },
                shape: 'circle',
                size: 16
            },
            Entity: {
                color: { background: '#F59E0B', border: '#D97706' },
                shape: 'diamond',
                size: 18
            },
            Concept: {
                color: { background: '#8B5CF6', border: '#7C3AED' },
                shape: 'square',
                size: 18
            },
            Person: {
                color: { background: '#EC4899', border: '#DB2777' },
                shape: 'triangle',
                size: 18
            },
            Organization: {
                color: { background: '#6366F1', border: '#4F46E5' },
                shape: 'triangleDown',
                size: 18
            },
            Location: {
                color: { background: '#14B8A6', border: '#0D9488' },
                shape: 'star',
                size: 18
            },
            Event: {
                color: { background: '#F97316', border: '#EA580C' },
                shape: 'hexagon',
                size: 18
            }
        },
        physics: {
            enabled: physicsEnabled,
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 200,
                springConstant: 0.04,
                damping: 0.09,
                avoidOverlap: 0.1
            },
            stabilization: {
                enabled: physicsEnabled,
                iterations: 1000,
                updateInterval: 50,
                fit: true
            }
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
            navigationButtons: true,
            keyboard: {
                enabled: true,
                speed: { x: 10, y: 10, zoom: 0.1 }
            },
            zoomSpeed: 0.5,
            dragSpeed: 0.5,
            hoverSpeed: 0.5,
            multiselect: true,
            selectable: true,
            selectConnectedEdges: true
        },
        layout: {
            improvedLayout: true,
            randomSeed: 42,
            hierarchical: {
                enabled: false
            }
        },
        manipulation: {
            enabled: false
        },
        width: '100%',
        height: '100%',
        autoResize: true,
        maxHeight: 600,
        minHeight: 400
    };
    
    if (network) {
        network.destroy();
    }
    
    network = new vis.Network(container, data, options);

    // Force a resize after initialization
    setTimeout(() => {
        network.redraw();
        network.setSize('100%', '600px');
    }, 100);

    // Add click event for node details
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            showNodeDetails(node);
            
            // Highlight connected nodes and edges
            const connectedEdges = network.getConnectedEdges(nodeId);
            network.selectEdges(connectedEdges);
            
            // Focus on the selected node
            network.focus(nodeId, {
                scale: 1.5,
                animation: true
            });
        } else if (params.edges.length > 0) {
            const edgeId = params.edges[0];
            const edge = edges.get(edgeId);
            showRelationshipDetails(edge);
            
            // Highlight connected nodes
            const connectedNodes = network.getConnectedNodes(edgeId);
            network.selectNodes(connectedNodes);
        }
    });

    // Add hover event for better interaction
    network.on('hoverNode', function(params) {
        document.body.style.cursor = 'pointer';
        const nodeId = params.node;
        const connectedEdges = network.getConnectedEdges(nodeId);
        network.selectEdges(connectedEdges);
    });

    network.on('blurNode', function(params) {
        document.body.style.cursor = 'default';
        network.unselectAll();
    });

    // Add double click event to focus on node
    network.on('doubleClick', function(params) {
        if (params.nodes.length > 0) {
            network.focus(params.nodes[0], {
                scale: 1.5,
                animation: true
            });
        }
    });

    // Add stabilization progress event
    network.on('stabilizationProgress', function(params) {
        const loadingElement = document.querySelector('.graph-loading');
        if (loadingElement) {
            loadingElement.querySelector('span').textContent = `Stabilizing graph: ${Math.round(params.iterations / params.total * 100)}%`;
        }
    });

    // Add stabilization complete event
    network.on('stabilizationIterationsDone', function() {
        const loadingElement = document.querySelector('.graph-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    });
}

function createNodeTooltip(node) {
    let tooltip = `<strong>${node.label}</strong><br>Type: ${node.type}`;
    
    if (node.properties && Object.keys(node.properties).length > 0) {
        tooltip += '<br><br><strong>Properties:</strong><br>';
        for (const [key, value] of Object.entries(node.properties)) {
            if (value !== null && value !== undefined) {
                const formattedValue = typeof value === 'object' ? JSON.stringify(value) : value;
                tooltip += `${key}: ${formattedValue}<br>`;
            }
        }
    }
    
    return tooltip;
}

function createRelationshipTooltip(rel) {
    let tooltip = `<strong>${rel.type}</strong>`;
    
    if (rel.properties && Object.keys(rel.properties).length > 0) {
        tooltip += '<br><br><strong>Properties:</strong><br>';
        for (const [key, value] of Object.entries(rel.properties)) {
            if (value !== null && value !== undefined) {
                const formattedValue = typeof value === 'object' ? JSON.stringify(value) : value;
                tooltip += `${key}: ${formattedValue}<br>`;
            }
        }
    }
    
    return tooltip;
}

function showNodeDetails(node) {
    const detailsContainer = document.getElementById('nodeDetails');
    if (!detailsContainer) return;

    let details = `
        <div class="node-details">
            <h3>${node.label}</h3>
            <h4>Type: ${node.type}</h4>
    `;

    if (node.properties && Object.keys(node.properties).length > 0) {
        details += `
            <div class="properties-section">
                <h4>Properties</h4>
                <table class="properties-table">
                    <tbody>
        `;
        
        for (const [key, value] of Object.entries(node.properties)) {
            if (value !== null && value !== undefined) {
                const formattedValue = typeof value === 'object' ? JSON.stringify(value, null, 2) : value;
                details += `
                    <tr>
                        <td class="property-key">${key}</td>
                        <td class="property-value">${formattedValue}</td>
                    </tr>
                `;
            }
        }
        
        details += `
                    </tbody>
                </table>
            </div>
        `;
    }

    details += '</div>';
    detailsContainer.innerHTML = details;
    detailsContainer.style.display = 'block';
}

function showRelationshipDetails(edge) {
    const detailsContainer = document.getElementById('nodeDetails');
    if (!detailsContainer) return;

    let details = `
        <div class="node-details">
            <h3>${edge.type}</h3>
            <h4>Relationship</h4>
    `;

    if (edge.properties && Object.keys(edge.properties).length > 0) {
        details += `
            <div class="properties-section">
                <h4>Properties</h4>
                <table class="properties-table">
                    <tbody>
        `;
        
        for (const [key, value] of Object.entries(edge.properties)) {
            if (value !== null && value !== undefined) {
                const formattedValue = typeof value === 'object' ? JSON.stringify(value, null, 2) : value;
                details += `
                    <tr>
                        <td class="property-key">${key}</td>
                        <td class="property-value">${formattedValue}</td>
                    </tr>
                `;
            }
        }
        
        details += `
                    </tbody>
                </table>
            </div>
        `;
    }

    details += '</div>';
    detailsContainer.innerHTML = details;
    detailsContainer.style.display = 'block';
}

// Helper functions for node styling
function getNodeColor(type) {
    const colors = {
        'Document': '#3B82F6',  // Blue
        'Chunk': '#10B981',     // Green
        'Entity': '#F59E0B',    // Amber
        'Concept': '#8B5CF6',   // Purple
        'Person': '#EC4899',    // Pink
        'Organization': '#6366F1', // Indigo
        'Location': '#14B8A6',  // Teal
        'Event': '#F97316',     // Orange
        'default': '#64748B'    // Slate
    };
    return colors[type] || colors.default;
}

function getNodeBorderColor(type) {
    const colors = {
        'Document': '#2563EB',  // Darker Blue
        'Chunk': '#059669',     // Darker Green
        'Entity': '#D97706',    // Darker Amber
        'Concept': '#7C3AED',   // Darker Purple
        'Person': '#DB2777',    // Darker Pink
        'Organization': '#4F46E5', // Darker Indigo
        'Location': '#0D9488',  // Darker Teal
        'Event': '#EA580C',     // Darker Orange
        'default': '#475569'    // Darker Slate
    };
    return colors[type] || colors.default;
}

function getNodeHighlightColor(type) {
    const colors = {
        'Document': '#60A5FA',  // Lighter Blue
        'Chunk': '#34D399',     // Lighter Green
        'Entity': '#FBBF24',    // Lighter Amber
        'Concept': '#A78BFA',   // Lighter Purple
        'Person': '#F472B6',    // Lighter Pink
        'Organization': '#818CF8', // Lighter Indigo
        'Location': '#2DD4BF',  // Lighter Teal
        'Event': '#FB923C',     // Lighter Orange
        'default': '#94A3B8'    // Lighter Slate
    };
    return colors[type] || colors.default;
}

function getEdgeColor(type) {
    return '#60A5FA'; // Default edge color
}

function getEdgeHighlightColor(type) {
    return '#93C5FD'; // Highlighted edge color
}

function getNodeShape(type) {
    const shapes = {
        'Document': 'dot',
        'Chunk': 'circle',
        'Entity': 'diamond',
        'Concept': 'square',
        'Person': 'triangle',
        'Organization': 'triangleDown',
        'Location': 'star',
        'Event': 'hexagon',
        'default': 'dot'
    };
    return shapes[type] || shapes.default;
}

function getNodeSize(type) {
    const sizes = {
        'Document': 20,
        'Chunk': 16,
        'Entity': 18,
        'Concept': 18,
        'Person': 18,
        'Organization': 18,
        'Location': 18,
        'Event': 18,
        'default': 16
    };
    return sizes[type] || sizes.default;
} 