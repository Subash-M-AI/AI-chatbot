// CONFIGURATION: Set your Render backend URL here once deployed.
// Example: const BACKEND_URL = 'https://ai-chatbot-backend.onrender.com';
const BACKEND_URL = ''; 

document.addEventListener('DOMContentLoaded', () => {
    // Map Configuration
    const INDIA_CENTER = [22.5937, 78.9629];
    const DEFAULT_ZOOM = 5;
    
    // Initialize map
    const map = L.map('map', {
        zoomControl: false // We will customize controls or rely on defaults later
    }).setView(INDIA_CENTER, DEFAULT_ZOOM);
    
    // Add custom zoom control at the bottom right
    L.control.zoom({
        position: 'bottomright'
    }).addTo(map);

    // Using high-resolution Esri World Imagery (Satellite) with road/place labels overlay
    const satelliteTiles = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        maxZoom: 19
    });
    const labelTiles = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Labels &copy; Esri'
    });
    satelliteTiles.addTo(map);
    labelTiles.addTo(map);

    // Marker Layer Group
    const markerGroup = L.layerGroup().addTo(map);

    // DOM Elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const suggestionChips = document.querySelectorAll('.suggestion-chip');
    const resetMapBtn = document.getElementById('reset-map-view');
    const mapStatus = document.getElementById('map-status');
    const mapViewToggle = document.getElementById('map-view-toggle');
    const mapWrapperPanel = document.getElementById('map-wrapper-panel');

    // Chat History State
    let chatHistory = [];
    const MAX_HISTORY = 10; // Keep last 10 messages for context

    // Safe Markdown Parser Helper
    function parseMarkdown(text) {
        try {
            if (typeof marked.parse === 'function') {
                return marked.parse(text);
            } else if (typeof marked === 'function') {
                return marked(text);
            }
        } catch (e) {
            console.error("Markdown rendering error:", e);
        }
        // Simple fallback parser if library fails
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/### (.*?)\n/g, '<h3>$1</h3>')
            .replace(/## (.*?)\n/g, '<h2>$1</h2>')
            .replace(/\n/g, '<br>');
    }

    // Scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Reset map view to national view
    function resetMapView() {
        map.flyTo(INDIA_CENTER, DEFAULT_ZOOM, {
            animate: true,
            duration: 1.5
        });
    }

    resetMapBtn.addEventListener('click', resetMapView);

    // Toggle Map on Mobile
    mapViewToggle.addEventListener('click', () => {
        mapWrapperPanel.classList.toggle('mobile-visible');
        // Trigger a map resize to fix map canvas issues on visibility change
        setTimeout(() => {
            map.invalidateSize();
        }, 300);
        
        // Update toggle icon
        const icon = mapViewToggle.querySelector('i');
        if (mapWrapperPanel.classList.contains('mobile-visible')) {
            icon.className = 'fa-solid fa-message';
            mapViewToggle.title = "View Chat";
        } else {
            icon.className = 'fa-solid fa-map';
            mapViewToggle.title = "View Map";
        }
    });

    // Handle suggestion chips clicks
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            userInput.value = query;
            chatForm.dispatchEvent(new Event('submit'));
        });
    });

    // Create a typing indicator element
    function createTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message assistant-message typing-loader message-fade-in';
        indicator.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        return indicator;
    }

    // Add a message bubble to chat UI
    function appendMessageBubble(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message message-fade-in`;
        
        const avatarHTML = role === 'user' 
            ? '<div class="avatar"><i class="fa-solid fa-user"></i></div>' 
            : '<div class="avatar"><i class="fa-solid fa-robot"></i></div>';
            
        const contentHTML = role === 'user' 
            ? `<div class="message-content"><p>${escapeHTML(content)}</p></div>`
            : `<div class="message-content">${parseMarkdown(content)}</div>`;

        messageDiv.innerHTML = avatarHTML + contentHTML;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Helper to escape HTML for user messages
    function escapeHTML(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Manage Map Markers dynamically based on AI API response
    function updateMapLocations(locations) {
        // Clear previous markers
        markerGroup.clearLayers();

        if (!locations || locations.length === 0) {
            mapStatus.innerText = "No specific locations marked for this discussion.";
            return;
        }

        const bounds = [];
        
        locations.forEach(loc => {
            if (typeof loc.lat === 'number' && typeof loc.lng === 'number') {
                const marker = L.marker([loc.lat, loc.lng]);
                
                // Construct premium dark-mode popup content
                const popupContent = `
                    <div class="map-popup-card">
                        <h4>${loc.name}</h4>
                        <p>${loc.description}</p>
                    </div>
                `;
                
                marker.bindPopup(popupContent);
                markerGroup.addLayer(marker);
                
                bounds.push([loc.lat, loc.lng]);
            }
        });

        // Dynamic viewport adjusting based on marker density
        if (bounds.length === 1) {
            map.flyTo(bounds[0], 12, {
                animate: true,
                duration: 1.5
            });
            // Open popup for the single marker automatically after flying
            setTimeout(() => {
                const layers = markerGroup.getLayers();
                if (layers.length > 0) {
                    layers[0].openPopup();
                }
            }, 1600);
            mapStatus.innerText = `Marked: ${locations[0].name}`;
        } else if (bounds.length > 1) {
            const latLngBounds = L.latLngBounds(bounds);
            map.fitBounds(latLngBounds, {
                padding: [50, 50],
                maxZoom: 14,
                animate: true,
                duration: 1.5
            });
            mapStatus.innerText = `Marked ${bounds.length} locations on the map. Click on markers for details!`;
        }
    }

    // Submit Chat Form
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const messageText = userInput.value.trim();
        if (!messageText) return;

        // Clear input field immediately
        userInput.value = '';

        // Add user message to UI
        appendMessageBubble('user', messageText);

        // Add typing indicator
        const typingIndicator = createTypingIndicator();
        chatMessages.appendChild(typingIndicator);
        scrollToBottom();

        try {
            // Send request to Django chat API
            const fetchUrl = BACKEND_URL ? `${BACKEND_URL}/api/chat/` : '/api/chat/';
            const response = await fetch(fetchUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: messageText,
                    history: chatHistory
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Remove typing indicator
            typingIndicator.remove();

            if (data.error) {
                appendMessageBubble('assistant', `⚠️ **Error:** ${data.error}`);
                return;
            }

            // Append assistant response to UI
            appendMessageBubble('assistant', data.response);

            // Update map pins and move camera
            updateMapLocations(data.locations);

            // Update local chat history
            chatHistory.push({ role: 'user', content: messageText });
            chatHistory.push({ role: 'assistant', content: data.response });

            // Truncate history if exceeding maximum
            if (chatHistory.length > MAX_HISTORY * 2) {
                chatHistory = chatHistory.slice(-MAX_HISTORY * 2);
            }

        } catch (error) {
            console.error('Fetch Error:', error);
            typingIndicator.remove();
            appendMessageBubble('assistant', '⚠️ Sorry, I encountered an issue connecting to the server. Please check your internet connection or backend server status.');
        }
    });
});
