/**
 * RiddlerChat — Main Application Logic
 * Connects to Python FastAPI backend via WebSocket,
 * manages UI state, chat threads, and circuit visualization.
 *
 * 1337_TECH DBA, Austin Texas - 2026
 */

const API_BASE = 'http://127.0.0.1:7576';
const WS_BASE = 'ws://127.0.0.1:7576';

// ═══ STATE ═══
const state = {
  username: null,
  pqFingerprint: null,
  ws: null,
  contacts: [],
  activeContact: null,
  messages: {},        // contact -> [message]
  circuit: null,
  circuitVisible: false,
  algorithms: {},
};

// ═══ DOM REFS ═══
const $ = (id) => document.getElementById(id);
const dom = {};

document.addEventListener('DOMContentLoaded', () => {
  // Cache DOM refs
  dom.loginOverlay    = $('loginOverlay');
  dom.loginUsername    = $('loginUsername');
  dom.loginPassword   = $('loginPassword');
  dom.btnLogin        = $('btnLogin');
  dom.loginError      = $('loginError');
  dom.profileName     = $('profileName');
  dom.profileAlias    = $('profileAlias');
  dom.pqFingerprint   = $('pqFingerprint');
  dom.contactSearch   = $('contactSearch');
  dom.contactList     = $('contactList');
  dom.threadCount     = $('threadCount');
  dom.chatContactName = $('chatContactName');
  dom.chatContactMeta = $('chatContactMeta');
  dom.chatAvatarLetter= $('chatAvatarLetter');
  dom.pqBadge         = $('pqBadge');
  dom.btnCircuit      = $('btnCircuit');
  dom.btnContactSettings = $('btnContactSettings');
  dom.circuitPanel    = $('circuitPanel');
  dom.circuitViz      = $('circuitViz');
  dom.circuitFooter   = $('circuitFooter');
  dom.relayCount      = $('relayCount');
  dom.circuitEncryption = $('circuitEncryption');
  dom.messagesContainer = $('messagesContainer');
  dom.messagesEmpty   = $('messagesEmpty');
  dom.messageInputArea= $('messageInputArea');
  dom.messageInput    = $('messageInput');
  dom.btnSend         = $('btnSend');
  dom.circuitHops     = $('circuitHops');
  dom.circuitRtt      = $('circuitRtt');
  dom.opensslVersion  = $('opensslVersion');
  dom.entropyLabel    = $('entropyLabel');
  dom.entropyBits     = $('entropyBits');
  dom.entropySource   = $('entropySource');
  dom.entropyHealth   = $('entropyHealth');

  // Event listeners
  dom.btnLogin.addEventListener('click', handleLogin);
  dom.loginPassword.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleLogin();
  });
  dom.loginUsername.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') dom.loginPassword.focus();
  });
  dom.btnSend.addEventListener('click', handleSend);
  dom.messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) handleSend();
  });
  dom.btnCircuit.addEventListener('click', toggleCircuit);
  dom.contactSearch.addEventListener('input', filterContacts);
  $('settingsBtn').addEventListener('click', openSettings);
  dom.btnContactSettings.addEventListener('click', openContactSettings);

  // Fetch initial status
  fetchStatus();
});


// ═══ AUTH ═══
async function handleLogin() {
  const username = dom.loginUsername.value.trim();
  const password = dom.loginPassword.value.trim();

  if (!username || !password) {
    dom.loginError.textContent = 'Identity and passphrase required';
    return;
  }

  dom.loginError.textContent = '';
  dom.btnLogin.textContent = 'ESTABLISHING CIRCUIT...';
  dom.btnLogin.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Authentication failed');
    }

    const data = await res.json();
    state.username = data.username;
    state.pqFingerprint = data.pq_fingerprint;

    connectWebSocket();
  } catch (err) {
    dom.loginError.textContent = err.message;
    dom.btnLogin.textContent = 'AUTHENTICATE';
    dom.btnLogin.disabled = false;
  }
}


// ═══ WEBSOCKET ═══
function connectWebSocket() {
  state.ws = new WebSocket(`${WS_BASE}/ws/${state.username}`);

  state.ws.onopen = () => {
    console.log('[RiddlerChat] Circuit established');
  };

  state.ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    handleWsMessage(msg);
  };

  state.ws.onclose = () => {
    console.log('[RiddlerChat] Circuit closed');
    setTimeout(() => {
      if (state.username) connectWebSocket();
    }, 3000);
  };

  state.ws.onerror = (err) => {
    console.error('[RiddlerChat] Circuit error:', err);
  };
}

function handleWsMessage(msg) {
  switch (msg.type) {
    case 'init':
      handleInit(msg.data);
      break;
    case 'message':
      handleIncomingMessage(msg.data);
      break;
    case 'presence':
      handlePresence(msg.data);
      break;
    case 'contacts':
      state.contacts = msg.data;
      renderContacts();
      break;
    case 'thread':
      handleThread(msg.data);
      break;
    case 'circuit':
      state.circuit = msg.data;
      renderCircuit();
      updateStatusBar();
      break;
  }
}

function handleInit(data) {
  state.pqFingerprint = data.pq_fingerprint;
  state.circuit = data.circuit;
  state.contacts = data.contacts;
  state.algorithms = data.algorithms;

  // Update profile
  dom.profileName.textContent = state.username;
  dom.profileAlias.textContent = state.username.toLowerCase();
  dom.pqFingerprint.textContent = data.pq_fingerprint;

  // Update status bar
  if (data.openssl) {
    dom.opensslVersion.textContent = data.openssl.version;
  }
  if (data.entropy) {
    dom.entropyLabel.textContent = data.entropy.label;
    dom.entropyBits.textContent = `${data.entropy.bits}-bit`;
    dom.entropySource.textContent = data.entropy.source;
    dom.entropyHealth.textContent = data.entropy.healthy ? 'healthy' : 'low';
    dom.entropyHealth.className = data.entropy.healthy ? 'text-green' : '';
  }

  updateStatusBar();
  renderContacts();

  // Hide login
  dom.loginOverlay.classList.add('hidden');
}

function handleIncomingMessage(data) {
  const contact = data.sender === state.username ? data.recipient : data.sender;

  if (!state.messages[contact]) {
    state.messages[contact] = [];
  }

  // Avoid duplicates
  const existing = state.messages[contact].find(m => m.id === data.id);
  if (!existing) {
    state.messages[contact].push(data);
  }

  // Update contact list preview
  updateContactPreview(contact, data);

  // If this contact is active, render the message
  if (state.activeContact === contact) {
    renderMessages();
  }
}

function handlePresence(data) {
  // Refresh contacts
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ type: 'get_contacts' }));
  }
}

function handleThread(data) {
  state.messages[data.contact] = data.messages;
  if (state.activeContact === data.contact) {
    renderMessages();
  }
}


// ═══ SEND MESSAGE ═══
function handleSend() {
  const content = dom.messageInput.value.trim();
  if (!content || !state.activeContact) return;

  state.ws.send(JSON.stringify({
    type: 'message',
    data: {
      recipient: state.activeContact,
      content: content,
    }
  }));

  dom.messageInput.value = '';
  dom.messageInput.focus();
}


// ═══ RENDERING ═══

function renderContacts() {
  const search = dom.contactSearch.value.toLowerCase();
  const filtered = state.contacts.filter(c =>
    c.username.toLowerCase().includes(search) ||
    (c.alias && c.alias.toLowerCase().includes(search))
  );

  // Count sealed threads
  const sealedCount = state.contacts.length;
  dom.threadCount.textContent = `${sealedCount} sealed`;

  const colors = ['green', 'purple'];
  dom.contactList.innerHTML = filtered.map((contact, i) => {
    const letter = (contact.alias || contact.username).charAt(0).toUpperCase();
    const colorClass = colors[i % 2];
    const isActive = state.activeContact === contact.username;
    const msgs = state.messages[contact.username] || [];
    const lastMsg = msgs.length > 0 ? msgs[msgs.length - 1] : null;
    const timeStr = lastMsg ? formatTime(lastMsg.timestamp) : '';
    const preview = contact.last_ciphertext_preview || '';
    const unread = msgs.filter(m => m.sender !== state.username).length;

    return `
      <div class="contact-item ${isActive ? 'active' : ''}"
           onclick="selectContact('${contact.username}')"
           data-username="${contact.username}">
        <div class="contact-avatar ${colorClass}">${letter}</div>
        <div class="contact-info">
          <div class="contact-name">${contact.alias || contact.username}</div>
          <div class="contact-preview">
            <span class="lock-icon">🔒</span>
            <span>${preview}</span>
          </div>
        </div>
        <span class="contact-time">${timeStr}</span>
        ${unread > 0 ? `<span class="contact-badge">${unread}</span>` : ''}
      </div>
    `;
  }).join('');
}

function filterContacts() {
  renderContacts();
}

function selectContact(username) {
  state.activeContact = username;
  const contact = state.contacts.find(c => c.username === username);

  if (contact) {
    const letter = (contact.alias || contact.username).charAt(0).toUpperCase();
    dom.chatContactName.textContent = contact.alias || contact.username;
    dom.chatAvatarLetter.textContent = letter;
    dom.chatContactMeta.textContent = `@${contact.username.toLowerCase()} · key ${contact.pq_fingerprint || ''}`;
    dom.pqBadge.style.display = contact.pq_verified ? 'inline-block' : 'none';
    dom.btnCircuit.style.display = 'flex';
    dom.btnContactSettings.style.display = 'flex';
    dom.messageInputArea.style.display = 'block';
    dom.messagesEmpty.style.display = 'none';
  }

  renderContacts();
  renderMessages();

  // Request thread history
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({
      type: 'get_thread',
      data: { contact: username }
    }));
  }
}

function renderMessages() {
  const msgs = state.messages[state.activeContact] || [];

  if (msgs.length === 0) {
    dom.messagesContainer.innerHTML = `
      <div class="messages-empty">
        <div class="riddler-icon large">?</div>
        <div class="empty-title">Begin an encrypted thread</div>
        <div class="empty-sub">Messages are sealed with ML-KEM-1024 + AES-256-GCM</div>
      </div>`;
    return;
  }

  dom.messagesContainer.innerHTML = msgs.map((msg, idx) => {
    const isSent = msg.sender === state.username;
    const time = formatTime(msg.timestamp);
    const sealedText = msg.sealed ? '✓ sealed' : '';
    const ciphertextId = `ciphertext-${idx}`;

    return `
      <div class="message-bubble ${isSent ? 'sent' : 'received'}">
        ${msg.content}
      </div>
      <div class="message-meta ${isSent ? 'sent-meta' : ''}">
        <span>${time}</span>
        <span class="view-ciphertext-btn" onclick="toggleCiphertext('${ciphertextId}', this)">◌ view ciphertext</span>
        ${isSent ? `<span class="sealed-tag">${sealedText}</span>` : ''}
      </div>
      <div class="ciphertext-block ${isSent ? 'sent-ct' : ''}" id="${ciphertextId}" style="display:none">
        <div class="ciphertext-header">
          <span class="ciphertext-label">AES-256-GCM CIPHERTEXT</span>
          <span class="ciphertext-size">${msg.ciphertext ? msg.ciphertext.length + ' chars (base64)' : 'not available'}</span>
        </div>
        <div class="ciphertext-data">${msg.ciphertext || 'No ciphertext captured for this message'}</div>
        ${msg.signature ? `
        <div class="ciphertext-header sig-header">
          <span class="ciphertext-label">ML-DSA-87 SIGNATURE</span>
        </div>
        <div class="ciphertext-data">${msg.signature}</div>
        ` : ''}
        ${msg.circuit_id ? `<div class="ciphertext-circuit">circuit ${msg.circuit_id}</div>` : ''}
      </div>
    `;
  }).join('');

  // Scroll to bottom
  dom.messagesContainer.scrollTop = dom.messagesContainer.scrollHeight;
}

function renderCircuit() {
  if (!state.circuit) return;

  const c = state.circuit;
  dom.relayCount.textContent = c.hop_count;
  dom.circuitEncryption.textContent = `${c.encryption} · ${c.sealed}`;

  // Build circuit visualization
  const originNode = `
    <div class="circuit-node">
      <div class="node-circle origin">?</div>
      <div class="node-name">YOU</div>
      <div class="node-meta">origin</div>
    </div>`;

  const relayNodes = c.relays.map(r => `
    <div class="circuit-line"></div>
    <div class="circuit-node">
      <div class="node-circle relay">${r.label}</div>
      <div class="node-name">${r.name}</div>
      <div class="node-meta">${r.latency_ms}ms · ${r.role}</div>
    </div>`
  ).join('');

  const destNode = `
    <div class="circuit-line"></div>
    <div class="circuit-node">
      <div class="node-circle destination">${state.activeContact ? state.activeContact.charAt(0).toUpperCase() : 'O'}</div>
      <div class="node-name">${state.activeContact || 'RECIPIENT'}</div>
      <div class="node-meta">recipient</div>
    </div>`;

  dom.circuitViz.innerHTML = originNode + relayNodes + destNode;
  dom.circuitFooter.textContent = `◌ Circuit established — keys derived via ${c.hybrid}`;
}

function toggleCircuit() {
  state.circuitVisible = !state.circuitVisible;
  dom.circuitPanel.style.display = state.circuitVisible ? 'block' : 'none';
  if (state.circuitVisible) {
    renderCircuit();
  }
}

function updateStatusBar() {
  if (state.circuit) {
    dom.circuitHops.textContent = `${state.circuit.hop_count}-hop circuit`;
    dom.circuitRtt.textContent = `${state.circuit.total_rtt_ms}ms rtt`;
  }
}

function updateContactPreview(contact, msg) {
  const contactData = state.contacts.find(c => c.username === contact);
  if (contactData) {
    contactData.last_ciphertext_preview = msg.ciphertext
      ? msg.ciphertext.substring(0, 16) + ' …'
      : 'encrypted';
  }
  renderContacts();
}


// ═══ UTILITIES ═══

function formatTime(timestamp) {
  if (!timestamp) return '';
  const d = new Date(timestamp * 1000);
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

// ═══ CIPHERTEXT TOGGLE ═══

function toggleCiphertext(id, btnEl) {
  const block = document.getElementById(id);
  if (!block) return;

  const isVisible = block.style.display !== 'none';
  block.style.display = isVisible ? 'none' : 'block';
  btnEl.textContent = isVisible ? '◌ view ciphertext' : '◌ hide ciphertext';
  btnEl.classList.toggle('active', !isVisible);

  if (!isVisible) {
    block.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}


// ═══ SETTINGS PANEL ═══

function openSettings() {
  // Remove existing panel if open
  const existing = document.getElementById('settingsPanel');
  if (existing) {
    existing.remove();
    return;
  }

  const panel = document.createElement('div');
  panel.id = 'settingsPanel';
  panel.className = 'settings-overlay';

  const algorithms = state.algorithms || {};
  const circuit = state.circuit || {};
  const strategyInfo = state._strategyInfo || {};

  panel.innerHTML = `
    <div class="settings-card">
      <div class="settings-header">
        <span class="settings-title">SYSTEM CONFIGURATION</span>
        <button class="settings-close" onclick="closeSettings()">×</button>
      </div>

      <div class="settings-section">
        <div class="settings-section-title">IDENTITY</div>
        <div class="settings-row">
          <span class="settings-key">Username</span>
          <span class="settings-value">${state.username || 'not connected'}</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">PQ Fingerprint</span>
          <span class="settings-value text-green">${state.pqFingerprint || '—'}</span>
        </div>
      </div>

      <div class="settings-section">
        <div class="settings-section-title">CRYPTOGRAPHIC ALGORITHMS</div>
        <div class="settings-row">
          <span class="settings-key">Key Encapsulation</span>
          <span class="settings-value">${algorithms.kem || 'ML-KEM-1024'}</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">Digital Signature</span>
          <span class="settings-value">${algorithms.sig || 'ML-DSA-87'}</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">Symmetric Cipher</span>
          <span class="settings-value">${algorithms.symmetric || 'AES-256-GCM'}</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">Forward Secrecy</span>
          <span class="settings-value text-green">${algorithms.forward_secrecy ? 'Enabled' : 'Disabled'}</span>
        </div>
      </div>

      <div class="settings-section">
        <div class="settings-section-title">ONION CIRCUIT</div>
        <div class="settings-row">
          <span class="settings-key">Circuit ID</span>
          <span class="settings-value mono">${circuit.circuit_id || '—'}</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">Hop Count</span>
          <span class="settings-value">${circuit.hop_count || '3'} relays</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">Total RTT</span>
          <span class="settings-value">${circuit.total_rtt_ms || '—'}ms</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">Layer Encryption</span>
          <span class="settings-value">${circuit.encryption || 'AES-256-GCM per layer'}</span>
        </div>
        <div class="settings-row action-row">
          <button class="settings-btn" onclick="requestNewCircuit()">ROTATE CIRCUIT</button>
        </div>
      </div>

      <div class="settings-section">
        <div class="settings-section-title">BACKEND</div>
        <div class="settings-row">
          <span class="settings-key">OpenSSL</span>
          <span class="settings-value" id="settingsOpenssl">—</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">PQ Strategy</span>
          <span class="settings-value" id="settingsStrategy">—</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">Entropy Source</span>
          <span class="settings-value" id="settingsEntropy">—</span>
        </div>
      </div>

      <div class="settings-footer">RiddlerChat v2.0.0 · 1337_TECH DBA</div>
    </div>
  `;

  document.body.appendChild(panel);

  // Fetch live status to populate backend info
  fetchSettingsStatus();
}

function closeSettings() {
  const panel = document.getElementById('settingsPanel');
  if (panel) panel.remove();
}

async function fetchSettingsStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    if (!res.ok) return;
    const data = await res.json();

    const elOpenssl = document.getElementById('settingsOpenssl');
    const elStrategy = document.getElementById('settingsStrategy');
    const elEntropy = document.getElementById('settingsEntropy');

    if (elOpenssl && data.openssl) {
      elOpenssl.textContent = data.openssl.version;
    }
    if (elStrategy) {
      const strat = data.pq_strategy || {};
      elStrategy.textContent = `${data.pq_backend || '—'} (${strat.strategy || '—'})`;
    }
    if (elEntropy && data.entropy) {
      elEntropy.textContent = `${data.entropy.source} · ${data.entropy.healthy ? 'healthy' : 'low'}`;
    }
  } catch {
    // Backend unavailable
  }
}

function requestNewCircuit() {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ type: 'new_circuit' }));
    closeSettings();
  }
}

function openContactSettings() {
  if (!state.activeContact) return;

  const existing = document.getElementById('contactSettingsPanel');
  if (existing) {
    existing.remove();
    return;
  }

  const contact = state.contacts.find(c => c.username === state.activeContact);
  if (!contact) return;

  const msgs = state.messages[state.activeContact] || [];
  const sealedCount = msgs.filter(m => m.sealed).length;
  const totalCount = msgs.length;

  const panel = document.createElement('div');
  panel.id = 'contactSettingsPanel';
  panel.className = 'settings-overlay';

  panel.innerHTML = `
    <div class="settings-card">
      <div class="settings-header">
        <span class="settings-title">THREAD DETAILS</span>
        <button class="settings-close" onclick="closeContactSettings()">×</button>
      </div>

      <div class="settings-section">
        <div class="settings-section-title">CONTACT</div>
        <div class="settings-row">
          <span class="settings-key">Alias</span>
          <span class="settings-value">${contact.alias || contact.username}</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">Username</span>
          <span class="settings-value">@${contact.username}</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">PQ Verified</span>
          <span class="settings-value text-green">${contact.pq_verified ? '✓ Verified' : '✗ Unverified'}</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">PQ Fingerprint</span>
          <span class="settings-value text-green">${contact.pq_fingerprint || '—'}</span>
        </div>
      </div>

      <div class="settings-section">
        <div class="settings-section-title">THREAD STATS</div>
        <div class="settings-row">
          <span class="settings-key">Total Messages</span>
          <span class="settings-value">${totalCount}</span>
        </div>
        <div class="settings-row">
          <span class="settings-key">Sealed (E2E)</span>
          <span class="settings-value text-green">${sealedCount} / ${totalCount}</span>
        </div>
      </div>

      <div class="settings-footer">End-to-end encrypted with ML-KEM-1024 + AES-256-GCM</div>
    </div>
  `;

  document.body.appendChild(panel);
}

function closeContactSettings() {
  const panel = document.getElementById('contactSettingsPanel');
  if (panel) panel.remove();
}


async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    if (res.ok) {
      const data = await res.json();
      if (data.openssl) {
        dom.opensslVersion.textContent = data.openssl.version;
      }
    }
  } catch {
    // Backend not ready yet — will connect via WebSocket later
  }
}
