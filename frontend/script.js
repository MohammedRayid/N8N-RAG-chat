// Configuration
const API_BASE_URL = 'http://localhost:5000';

// Configure marked for better markdown rendering
marked.setOptions({
  breaks: true,
  gfm: true,  // GitHub Flavored Markdown
});

// DOM elements
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const messagesContainer = document.getElementById('messages');
const typingIndicator = document.getElementById('typing-indicator');
const clearChatBtn = document.getElementById('clear-chat-btn');

// State
let conversationHistory = [];

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    messageInput.addEventListener('input', toggleSendButton);
    messageForm.addEventListener('submit', handleSubmit);
    clearChatBtn.addEventListener('click', clearChat);
    scrollToBottom();

    // Show welcome message
    addMessage({
        role: 'assistant',
        content: 'Hello! 👋 I\'m here to help you with N8N questions. Ask me anything about workflows, nodes, integrations, or any other N8N feature.',
        timestamp: new Date()
    });
});

// Toggle send button based on input
function toggleSendButton() {
    const hasText = messageInput.value.trim().length > 0;
    sendBtn.disabled = !hasText;
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();

    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage({
        role: 'user',
        content: message,
        timestamp: new Date()
    });

    // Clear input and disable UI
    messageInput.value = '';
    toggleSendButton();
    setUILoading(true);
    scrollToBottom();

    try {
        const response = await sendMessage(message);
        addMessage({
            role: 'assistant',
            content: response.answer,
            timestamp: new Date()
        });
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage({
            role: 'assistant',
            content: `Sorry, I encountered an error: ${error.message}`,
            timestamp: new Date(),
            error: true
        });
    }

    setUILoading(false);
    scrollToBottom();
}

// Send message to API
async function sendMessage(message) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: message })
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
}

// Add message to chat
function addMessage(message) {
    conversationHistory.push(message);

    const messageElement = document.createElement('div');
    messageElement.className = `message ${message.role}`;

    const avatar = getAvatar(message.role);
    let contentHtml;
    if (message.role === 'bot') {
        contentHtml = marked.parse(message.content);
    } else {
        contentHtml = message.content.replace(/\n/g, '<br>');
    }
    const timestamp = formatTimestamp(message.timestamp);
    const errorClass = message.error ? 'message--error' : '';

    messageElement.innerHTML = `
        <div class="sender">${avatar}</div>
        <div class="message-content ${errorClass}">
            <div>${contentHtml}</div>
            <div class="timestamp">${timestamp}</div>
        </div>
    `;

    messagesContainer.appendChild(messageElement);
}

// Get avatar emoji for role
function getAvatar(role) {
    switch (role) {
        case 'user':
            return '👤';
        case 'assistant':
            return '🤖';
        default:
            return '💬';
    }
}

// Format timestamp
function formatTimestamp(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Set UI loading state
function setUILoading(isLoading) {
    messageInput.disabled = isLoading;
    sendBtn.disabled = isLoading;

    if (isLoading) {
        typingIndicator.style.display = 'flex';
        scrollToBottom();
    } else {
        typingIndicator.style.display = 'none';
    }
}

// Clear chat
function clearChat() {
    if (!confirm('Are you sure you want to clear the entire conversation?')) return;

    conversationHistory = [];
    messagesContainer.innerHTML = '';

    // Re-add welcome message
    addMessage({
        role: 'assistant',
        content: 'Chat cleared! What can I help you with?',
        timestamp: new Date()
    });
}

// Scroll to bottom
function scrollToBottom() {
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 100);
}

// Handle network errors
window.addEventListener('online', () => {
    if (!navigator.onLine) {
        addMessage({
            role: 'assistant',
            content: 'Connection restored.',
            timestamp: new Date()
        });
    }
});

window.addEventListener('offline', () => {
    addMessage({
        role: 'assistant',
        content: 'Connection lost. Please check your internet connection.',
        timestamp: new Date(),
        error: true
    });
});

// Error handling for fetch
window.addEventListener('unhandledrejection', event => {
    console.error('Unhandled promise rejection:', event.reason);
    addMessage({
        role: 'assistant',
        content: 'An unexpected error occurred. Please try again.',
        timestamp: new Date(),
        error: true
    });
    setUILoading(false);
});
