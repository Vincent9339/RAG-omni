/**
 * RAG Chatbot Application
 * 
 * This script handles:
 * - Sending/receiving messages
 * - Chat history management
 * - UI interactions
 * - Theme management
 */

// Configuration
const serverPort = window.location.port || 5000;
const apiUrl = `http://${window.location.hostname}:${serverPort}/api/ask`;
let isWaitingForResponse = false;

// DOM Elements
const chatbox = document.getElementById('chatbox');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const settingsMenu = document.getElementById('settingsMenu');

// Initialize the chat when DOM is loaded
document.addEventListener('DOMContentLoaded', initChat);

/**
 * Initializes the chat interface
 */
function initChat() {
  loadConversation();
  userInput.focus();
  
  // Event listeners
  userInput.addEventListener('keypress', handleInputKeypress);
  document.addEventListener('click', handleOutsideClick);
}

/**
 * Handles sending a question to the chatbot
 */
async function sendQuestion() {
  if (isWaitingForResponse) return;
  
  const question = userInput.value.trim();
  if (!question) return;

  // Display user message
  appendMessage('user', question);
  userInput.value = '';
  isWaitingForResponse = true;
  sendButton.disabled = true;
  
  // Show loading indicator
  const loadingMsg = appendMessage('bot', createLoadingDots());
  
  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
    const data = await response.json();
    
    // Handle response
    if (data.error) {
      showErrorMessage(loadingMsg, data.error);
    } else {
      showBotMessage(loadingMsg, data.answer);
    }
  } catch (err) {
    console.error('Fetch error:', err);
    showErrorMessage(loadingMsg, 'Connection error. Please try again later.');
  } finally {
    isWaitingForResponse = false;
    sendButton.disabled = false;
    saveConversation();
  }
}

/**
 * Creates loading dots animation HTML
 */
function createLoadingDots() {
  return '<div class="loading-dots"><span></span><span></span><span></span></div>';
}

/**
 * Appends a message to the chat
 * @param {string} sender - 'user' or 'bot'
 * @param {string} text - Message content
 * @returns {HTMLElement} The created message element
 */
function appendMessage(sender, text) {
  const msgWrapper = document.createElement('div');
  msgWrapper.className = `message ${sender}`;

  // Create avatar
  const avatar = document.createElement('img');
  avatar.className = 'avatar';
  avatar.alt = `${sender} avatar`;
  avatar.src = sender === 'user'
    ? 'https://api.iconify.design/mdi/account.svg'
    : 'https://api.iconify.design/fluent-emoji-flat/robot.svg';

  // Create message bubble
  const msg = document.createElement('div');
  msg.className = `${sender}-msg`;
  if (typeof text === 'string' && text.startsWith('<')) {
    msg.innerHTML = text;
  } else {
    msg.textContent = text;
  }

  // Arrange elements based on sender
  if (sender === 'user') {
    msgWrapper.appendChild(msg);
    msgWrapper.appendChild(avatar);
  } else {
    msgWrapper.appendChild(avatar);
    msgWrapper.appendChild(msg);
  }

  chatbox.appendChild(msgWrapper);
  chatbox.scrollTop = chatbox.scrollHeight;
  return msgWrapper;
}

/**
 * Formats answer text with simple markdown
 * @param {string} text - Raw text to format
 * @returns {string} Formatted HTML
 */
function formatAnswer(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
    .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic
    .replace(/`(.*?)`/g, '<code>$1</code>')           // Code
    .replace(/\n/g, '<br>');                          // Line breaks
}

/**
 * Displays a bot message, replacing loading indicator
 */
function showBotMessage(loadingMsg, answer) {
  loadingMsg.querySelector('.bot-msg').innerHTML = formatAnswer(answer);
}

/**
 * Displays an error message
 */
function showErrorMessage(loadingMsg, error) {
  const msgElement = loadingMsg.querySelector('.bot-msg');
  msgElement.innerHTML = `❗ ${formatAnswer(error)}`;
  msgElement.style.backgroundColor = 'var(--error)';
}

/**
 * Toggles dark mode
 */
function toggleDarkMode() {
  document.body.classList.toggle('dark');
  localStorage.setItem('darkMode', document.body.classList.contains('dark'));
  toggleSettings();
}

/**
 * Toggles settings menu visibility
 */
function toggleSettings() {
  settingsMenu.style.display = settingsMenu.style.display === 'flex' ? 'none' : 'flex';
}

/**
 * Clears chat history
 */
function clearHistory() {
  if (confirm('Are you sure you want to clear all chat history?')) {
    localStorage.removeItem('chatHistory');
    chatbox.innerHTML = '';
    toggleSettings();
  }
}

/**
 * Exports chat to a text file
 */
function exportChat() {
  const messages = Array.from(document.querySelectorAll('.message')).map(msg => 
    `${msg.classList.contains('user') ? 'You' : 'Bot'}: ${msg.querySelector('.user-msg, .bot-msg').textContent}`
  ).join('\n\n');
  
  const blob = new Blob([messages], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `chat-export-${new Date().toISOString().slice(0,10)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  toggleSettings();
}

/**
 * Saves conversation to localStorage
 */
function saveConversation() {
  const messages = Array.from(document.querySelectorAll('.message')).map(msg => ({
    sender: msg.classList.contains('user') ? 'user' : 'bot',
    text: msg.querySelector('.user-msg, .bot-msg').textContent,
    timestamp: new Date().toISOString()
  }));
  localStorage.setItem('chatHistory', JSON.stringify(messages));
}

/**
 * Loads conversation from localStorage
 */
function loadConversation() {
  // Load theme preference
  if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark');
  }
  
  // Load chat history
  const history = JSON.parse(localStorage.getItem('chatHistory'));
  if (history) {
    history.forEach(msg => appendMessage(msg.sender, msg.text));
  }
}

/**
 * Handles Enter key in input field
 */
function handleInputKeypress(e) {
  if (e.key === 'Enter' && !isWaitingForResponse) sendQuestion();
}

/**
 * Closes settings when clicking outside
 */
function handleOutsideClick(e) {
  const settingsIcon = document.querySelector('.settings-icon');
  if (settingsMenu && settingsIcon && 
      !settingsMenu.contains(e.target) && 
      !settingsIcon.contains(e.target)) {
    settingsMenu.style.display = 'none';
  }
}

// Add this at the top with other DOM elements
const sidebar = document.getElementById('sidebar');
const historyList = document.getElementById('historyList');
const overlay = document.createElement('div');
overlay.className = 'overlay';
document.body.appendChild(overlay);

// Add this to your initChat function
overlay.addEventListener('click', toggleSidebar);

/**
 * Toggles the sidebar visibility
 */
function toggleSidebar() {
  sidebar.classList.toggle('active');
  overlay.classList.toggle('active');
  
  if (sidebar.classList.contains('active')) {
    loadHistoryList();
  }
}

/**
 * Loads the chat history into the sidebar
 */
function loadHistoryList() {
  const history = JSON.parse(localStorage.getItem('chatHistory')) || [];
  
  // Group conversations by date
  const groupedHistory = groupConversationsByDate(history);
  
  historyList.innerHTML = '';
  
  // Create date sections
  for (const [date, conversations] of Object.entries(groupedHistory)) {
    const dateHeader = document.createElement('div');
    dateHeader.className = 'history-date-header';
    dateHeader.textContent = date;
    historyList.appendChild(dateHeader);
    
    // Add each conversation
    conversations.forEach((conversation, index) => {
      const historyItem = document.createElement('div');
      historyItem.className = 'history-item';
      historyItem.innerHTML = `
        <div class="history-item-title">Chat ${conversations.length - index}</div>
        <div class="history-item-preview">${conversation.messages[0].text.substring(0, 30)}...</div>
      `;
      
      historyItem.addEventListener('click', () => {
        loadConversationFromHistory(conversation);
        toggleSidebar();
      });
      
      historyList.appendChild(historyItem);
    });
  }
}

/**
 * Groups conversations by date
 */
function groupConversationsByDate(history) {
  // First, we need to restructure how we save history to group messages by conversation
  // This assumes you'll update your saveConversation function (shown below)
  const conversations = [];
  let currentConversation = [];
  
  for (const message of history) {
    if (message.sender === 'user' && currentConversation.length > 0) {
      conversations.push(currentConversation);
      currentConversation = [];
    }
    currentConversation.push(message);
  }
  
  if (currentConversation.length > 0) {
    conversations.push(currentConversation);
  }
  
  // Group by date
  const grouped = {};
  
  conversations.forEach(conversation => {
    const date = new Date(conversation[0].timestamp).toLocaleDateString();
    if (!grouped[date]) {
      grouped[date] = [];
    }
    
    grouped[date].push({
      timestamp: conversation[0].timestamp,
      messages: conversation
    });
  });
  
  return grouped;
}

/**
 * Loads a specific conversation from history
 */
function loadConversationFromHistory(conversation) {
  chatbox.innerHTML = '';
  conversation.messages.forEach(msg => {
    appendMessage(msg.sender, msg.text);
  });
}

/**
 * Updated save function to better organize conversations
 */
function saveConversation() {
  const messages = Array.from(document.querySelectorAll('.message')).map(msg => ({
    sender: msg.classList.contains('user') ? 'user' : 'bot',
    text: msg.querySelector('.user-msg, .bot-msg').textContent,
    timestamp: new Date().toISOString()
  }));
  
  // Get existing history or initialize
  const existingHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
  
  // Add new messages
  const updatedHistory = [...existingHistory, ...messages];
  localStorage.setItem('chatHistory', JSON.stringify(updatedHistory));
}
