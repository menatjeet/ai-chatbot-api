// ApexAI Interactive Client Application

(function () {
  'use strict';

  // State Management
  const state = {
    token: localStorage.getItem('apex_token') || null,
    user: null,
    conversations: [],
    activeConversationId: null,
    isStreaming: true,
    isSubmitting: false,
  };

  // DOM Elements
  const elements = {
    authModal: document.getElementById('authModal'),
    tabLogin: document.getElementById('tabLogin'),
    tabRegister: document.getElementById('tabRegister'),
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    loginEmail: document.getElementById('loginEmail'),
    loginPassword: document.getElementById('loginPassword'),
    loginError: document.getElementById('loginError'),
    regName: document.getElementById('regName'),
    regEmail: document.getElementById('regEmail'),
    regPassword: document.getElementById('regPassword'),
    regError: document.getElementById('regError'),
    btnQuickDemo: document.getElementById('btnQuickDemo'),

    userAvatar: document.getElementById('userAvatar'),
    userNameLabel: document.getElementById('userNameLabel'),
    userEmailLabel: document.getElementById('userEmailLabel'),
    btnLogout: document.getElementById('btnLogout'),

    sidebar: document.getElementById('sidebar'),
    btnToggleSidebar: document.getElementById('btnToggleSidebar'),
    btnNewChat: document.getElementById('btnNewChat'),
    conversationsList: document.getElementById('conversationsList'),
    chatCountBadge: document.getElementById('chatCountBadge'),

    activeChatTitle: document.getElementById('activeChatTitle'),
    streamingToggle: document.getElementById('streamingToggle'),
    messagesContainer: document.getElementById('messagesContainer'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    messagesList: document.getElementById('messagesList'),

    chatForm: document.getElementById('chatForm'),
    messageInput: document.getElementById('messageInput'),
    btnSendMessage: document.getElementById('btnSendMessage'),
  };

  // ---------------------------------------------------------------------------
  // Helper: API Request Wrapper
  // ---------------------------------------------------------------------------
  async function apiRequest(endpoint, options = {}) {
    const headers = options.headers || {};
    if (state.token) {
      headers['Authorization'] = `Bearer ${state.token}`;
    }
    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(endpoint, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      handleUnauthorized();
      throw new Error('Session expired. Please sign in again.');
    }

    return response;
  }

  function handleUnauthorized() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('apex_token');
    showAuthModal();
  }

  // ---------------------------------------------------------------------------
  // Auth Flows
  // ---------------------------------------------------------------------------
  function showAuthModal() {
    elements.authModal.style.display = 'flex';
  }

  function hideAuthModal() {
    elements.authModal.style.display = 'none';
  }

  function switchTab(target) {
    if (target === 'login') {
      elements.tabLogin.classList.add('active');
      elements.tabRegister.classList.remove('active');
      elements.loginForm.style.display = 'flex';
      elements.registerForm.style.display = 'none';
      elements.loginError.style.display = 'none';
    } else {
      elements.tabRegister.classList.add('active');
      elements.tabLogin.classList.remove('active');
      elements.registerForm.style.display = 'flex';
      elements.loginForm.style.display = 'none';
      elements.regError.style.display = 'none';
    }
  }

  async function checkCurrentUser() {
    if (!state.token) {
      showAuthModal();
      return;
    }

    try {
      const res = await apiRequest('/api/auth/me');
      if (res.ok) {
        state.user = await res.json();
        renderUserProfile();
        hideAuthModal();
        await loadConversations();
      } else {
        handleUnauthorized();
      }
    } catch {
      handleUnauthorized();
    }
  }

  function renderUserProfile() {
    if (!state.user) return;
    elements.userNameLabel.textContent = state.user.name;
    elements.userEmailLabel.textContent = state.user.email;
    elements.userAvatar.textContent = state.user.name.charAt(0).toUpperCase();
  }

  async function handleLogin(email, password) {
    elements.loginError.style.display = 'none';
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to sign in');
      }

      state.token = data.access_token;
      localStorage.setItem('apex_token', state.token);
      await checkCurrentUser();
    } catch (err) {
      elements.loginError.textContent = err.message;
      elements.loginError.style.display = 'block';
    }
  }

  async function handleRegister(name, email, password) {
    elements.regError.style.display = 'none';
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Registration failed');
      }

      // Automatically log in newly registered user
      await handleLogin(email, password);
    } catch (err) {
      elements.regError.textContent = err.message;
      elements.regError.style.display = 'block';
    }
  }

  async function handleDemoLogin() {
    const demoEmail = 'demo@apexai.local';
    const demoPassword = 'DemoPassword123!';
    const demoName = 'Demo User';

    try {
      // Attempt login first
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: demoEmail, password: demoPassword }),
      });

      if (res.ok) {
        const data = await res.json();
        state.token = data.access_token;
        localStorage.setItem('apex_token', state.token);
        await checkCurrentUser();
        return;
      }

      // If user doesn't exist, register then log in
      await handleRegister(demoName, demoEmail, demoPassword);
    } catch (err) {
      alert('Demo login failed: ' + err.message);
    }
  }

  function handleLogout() {
    state.token = null;
    state.user = null;
    state.conversations = [];
    state.activeConversationId = null;
    localStorage.removeItem('apex_token');
    elements.conversationsList.innerHTML = '';
    elements.messagesList.innerHTML = '';
    elements.welcomeScreen.style.display = 'block';
    elements.activeChatTitle.textContent = 'ApexAI Chat';
    showAuthModal();
  }

  // ---------------------------------------------------------------------------
  // Conversation Management
  // ---------------------------------------------------------------------------
  async function loadConversations() {
    try {
      const res = await apiRequest('/api/conversations/');
      if (res.ok) {
        state.conversations = await res.json();
        renderConversationsList();

        if (state.conversations.length > 0 && !state.activeConversationId) {
          selectConversation(state.conversations[0].id);
        } else if (state.conversations.length === 0) {
          showWelcome();
        }
      }
    } catch (err) {
      console.error('Error loading conversations:', err);
    }
  }

  function renderConversationsList() {
    elements.conversationsList.innerHTML = '';
    elements.chatCountBadge.textContent = state.conversations.length;

    if (state.conversations.length === 0) {
      elements.conversationsList.innerHTML = `
        <div style="padding: 16px 8px; color: var(--text-muted); font-size: 0.8rem; text-align: center;">
          No conversations yet.<br/>Click <strong>+ New Chat</strong> to begin!
        </div>
      `;
      return;
    }

    state.conversations.forEach((conv) => {
      const item = document.createElement('div');
      item.className = `chat-item ${conv.id === state.activeConversationId ? 'active' : ''}`;
      item.dataset.id = conv.id;

      item.innerHTML = `
        <span class="chat-item-title">${escapeHtml(conv.title)}</span>
        <div class="chat-item-actions">
          <button class="action-btn btn-rename-chat" title="Rename conversation" data-id="${conv.id}">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
            </svg>
          </button>
          <button class="action-btn btn-delete-chat" title="Delete conversation" data-id="${conv.id}">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      `;

      item.addEventListener('click', (e) => {
        if (e.target.closest('.action-btn')) return;
        selectConversation(conv.id);
      });

      const btnRename = item.querySelector('.btn-rename-chat');
      btnRename.addEventListener('click', (e) => {
        e.stopPropagation();
        renameConversation(conv.id, conv.title);
      });

      const btnDelete = item.querySelector('.btn-delete-chat');
      btnDelete.addEventListener('click', (e) => {
        e.stopPropagation();
        deleteConversation(conv.id);
      });

      elements.conversationsList.appendChild(item);
    });
  }

  async function createNewConversation(title = 'New conversation') {
    try {
      const res = await apiRequest('/api/conversations/', {
        method: 'POST',
        body: JSON.stringify({ title }),
      });

      if (res.ok) {
        const newChat = await res.json();
        state.conversations.unshift(newChat);
        state.activeConversationId = newChat.id;
        renderConversationsList();
        selectConversation(newChat.id);
      }
    } catch (err) {
      alert('Error creating conversation: ' + err.message);
    }
  }

  async function renameConversation(id, currentTitle) {
    const newTitle = prompt('Rename conversation:', currentTitle);
    if (!newTitle || newTitle.trim() === '' || newTitle === currentTitle) return;

    try {
      const res = await apiRequest(`/api/conversations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ title: newTitle.trim() }),
      });

      if (res.ok) {
        const updated = await res.json();
        const idx = state.conversations.findIndex((c) => c.id === id);
        if (idx !== -1) {
          state.conversations[idx].title = updated.title;
        }
        if (state.activeConversationId === id) {
          elements.activeChatTitle.textContent = updated.title;
        }
        renderConversationsList();
      }
    } catch (err) {
      alert('Failed to rename: ' + err.message);
    }
  }

  async function deleteConversation(id) {
    if (!confirm('Are you sure you want to delete this conversation?')) return;

    try {
      const res = await apiRequest(`/api/conversations/${id}`, {
        method: 'DELETE',
      });

      if (res.status === 204) {
        state.conversations = state.conversations.filter((c) => c.id !== id);
        if (state.activeConversationId === id) {
          if (state.conversations.length > 0) {
            selectConversation(state.conversations[0].id);
          } else {
            state.activeConversationId = null;
            showWelcome();
          }
        }
        renderConversationsList();
      }
    } catch (err) {
      alert('Failed to delete conversation: ' + err.message);
    }
  }

  async function selectConversation(id) {
    state.activeConversationId = id;
    const conv = state.conversations.find((c) => c.id === id);
    if (conv) {
      elements.activeChatTitle.textContent = conv.title;
    }

    renderConversationsList();

    // Close mobile sidebar if open
    elements.sidebar.classList.remove('open');

    // Fetch messages
    try {
      const res = await apiRequest(`/api/conversations/${id}/messages`);
      if (res.ok) {
        const messages = await res.json();
        renderMessages(messages);
      }
    } catch (err) {
      console.error('Error fetching messages:', err);
    }
  }

  function showWelcome() {
    elements.welcomeScreen.style.display = 'block';
    elements.messagesList.innerHTML = '';
    elements.activeChatTitle.textContent = 'ApexAI Chat';
  }

  function renderMessages(messages) {
    if (messages.length === 0) {
      showWelcome();
      return;
    }

    elements.welcomeScreen.style.display = 'none';
    elements.messagesList.innerHTML = '';

    messages.forEach((msg) => {
      appendMessageToUI(msg.role, msg.content, msg.created_at);
    });

    scrollToBottom();
  }

  function appendMessageToUI(role, content, timestamp = null) {
    elements.welcomeScreen.style.display = 'none';

    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const timeStr = timestamp
      ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const avatarText = role === 'user' ? (state.user ? state.user.name.charAt(0).toUpperCase() : 'U') : 'AI';

    row.innerHTML = `
      <div class="msg-avatar">${avatarText}</div>
      <div class="msg-bubble-wrap">
        <div class="msg-bubble">${formatContent(content)}</div>
        <span class="msg-time">${timeStr}</span>
      </div>
    `;

    elements.messagesList.appendChild(row);
    scrollToBottom();
    return row;
  }

  function scrollToBottom() {
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
  }

  // ---------------------------------------------------------------------------
  // Messaging & Real-Time Streaming
  // ---------------------------------------------------------------------------
  async function sendMessage(text) {
    if (!text || text.trim() === '' || state.isSubmitting) return;

    // If no active conversation, create one automatically
    if (!state.activeConversationId) {
      const initialTitle = text.slice(0, 30) + (text.length > 30 ? '...' : '');
      const res = await apiRequest('/api/conversations/', {
        method: 'POST',
        body: JSON.stringify({ title: initialTitle }),
      });
      if (res.ok) {
        const newChat = await res.json();
        state.conversations.unshift(newChat);
        state.activeConversationId = newChat.id;
        renderConversationsList();
        elements.activeChatTitle.textContent = newChat.title;
      } else {
        return;
      }
    }

    const conversationId = state.activeConversationId;
    const promptText = text.trim();
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';

    // Optimistically render user message
    appendMessageToUI('user', promptText);

    state.isSubmitting = true;
    elements.btnSendMessage.disabled = true;

    const useStreaming = elements.streamingToggle.checked;

    if (useStreaming) {
      await streamMessage(conversationId, promptText);
    } else {
      await postMessageSync(conversationId, promptText);
    }

    state.isSubmitting = false;
    elements.btnSendMessage.disabled = false;
  }

  async function postMessageSync(convId, promptText) {
    // Show temporary typing indicator
    const typingRow = appendTypingIndicator();

    try {
      const res = await apiRequest(`/api/conversations/${convId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ content: promptText }),
      });

      typingRow.remove();

      if (res.ok) {
        const data = await res.json();
        appendMessageToUI('assistant', data.assistant_message.content, data.assistant_message.created_at);
      } else {
        const err = await res.json();
        appendMessageToUI('assistant', `⚠️ *Error:* ${err.detail || 'Service unavailable'}`);
      }
    } catch (err) {
      typingRow.remove();
      appendMessageToUI('assistant', `⚠️ *Error:* ${err.message}`);
    }
  }

  async function streamMessage(convId, promptText) {
    // Append assistant row with streaming cursor
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.innerHTML = `
      <div class="msg-avatar">AI</div>
      <div class="msg-bubble-wrap">
        <div class="msg-bubble"><span class="stream-content"></span><span class="streaming-cursor"></span></div>
        <span class="msg-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
    `;
    elements.messagesList.appendChild(row);
    scrollToBottom();

    const streamContentSpan = row.querySelector('.stream-content');
    const cursor = row.querySelector('.streaming-cursor');

    let fullText = '';

    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
      }

      const response = await fetch(`/api/conversations/${convId}/messages/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ content: promptText }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Streaming failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep last incomplete line

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const dataStr = trimmed.slice(6);
            try {
              const data = JSON.parse(dataStr);
              if (data.type === 'delta') {
                fullText += data.content;
                streamContentSpan.innerHTML = formatContent(fullText);
                scrollToBottom();
              } else if (data.type === 'error') {
                fullText += `\n⚠️ [${data.detail}]`;
                streamContentSpan.innerHTML = formatContent(fullText);
              }
            } catch {
              // Ignore invalid JSON chunks
            }
          }
        }
      }

      // Remove cursor when finished
      if (cursor) cursor.remove();
    } catch (err) {
      if (cursor) cursor.remove();
      streamContentSpan.innerHTML = formatContent(`⚠️ *Streaming Error:* ${err.message}`);
    }
  }

  function appendTypingIndicator() {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.innerHTML = `
      <div class="msg-avatar">AI</div>
      <div class="msg-bubble-wrap">
        <div class="msg-bubble">
          <div class="typing-dots">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
      </div>
    `;
    elements.messagesList.appendChild(row);
    scrollToBottom();
    return row;
  }

  // ---------------------------------------------------------------------------
  // Markdown & Text Formatting
  // ---------------------------------------------------------------------------
  function formatContent(text) {
    if (!text) return '';

    let formatted = escapeHtml(text);

    // Code blocks: ```code```
    formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Inline code: `code`
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold: **text** or *text*
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Line breaks
    formatted = formatted.replace(/\n/g, '<br/>');

    return formatted;
  }

  function escapeHtml(string) {
    const entityMap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    };
    return String(string).replace(/[&<>"']/g, (s) => entityMap[s]);
  }

  // ---------------------------------------------------------------------------
  // Event Listeners
  // ---------------------------------------------------------------------------
  function bindEvents() {
    // Auth tabs
    elements.tabLogin.addEventListener('click', () => switchTab('login'));
    elements.tabRegister.addEventListener('click', () => switchTab('register'));

    // Forms
    elements.loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleLogin(elements.loginEmail.value.trim(), elements.loginPassword.value);
    });

    elements.registerForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleRegister(
        elements.regName.value.trim(),
        elements.regEmail.value.trim(),
        elements.regPassword.value
      );
    });

    elements.btnQuickDemo.addEventListener('click', handleDemoLogin);
    elements.btnLogout.addEventListener('click', handleLogout);

    // Sidebar & Navigation
    elements.btnNewChat.addEventListener('click', () => createNewConversation());
    elements.btnToggleSidebar.addEventListener('click', () => {
      elements.sidebar.classList.toggle('open');
    });

    // Chat form input & auto-expanding textarea
    elements.messageInput.addEventListener('input', () => {
      elements.messageInput.style.height = 'auto';
      elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 160) + 'px';
    });

    elements.messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        elements.chatForm.requestSubmit();
      }
    });

    elements.chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      sendMessage(elements.messageInput.value);
    });

    // Suggestion Cards
    document.querySelectorAll('.suggestion-card').forEach((card) => {
      card.addEventListener('click', () => {
        const prompt = card.getAttribute('data-prompt');
        if (prompt) {
          sendMessage(prompt);
        }
      });
    });
  }

  // Initialization
  bindEvents();
  checkCurrentUser();
})();
