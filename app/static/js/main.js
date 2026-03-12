// --- STATE ---
let cycles = [];
let stats = {};
let globalTimerInstance = null;
let selectedCycleId = null;
let authToken = localStorage.getItem('jyclo_token');

// --- DOM ELEMENTS ---
const cardsContainer = document.getElementById('cards-container');
const themeToggle = document.getElementById('theme-toggle');
const btnLogout = document.getElementById('btn-logout');

// Stats Elements
const statLongest = document.getElementById('stat-longest');
const statStreak = document.getElementById('stat-streak');
const statTotal = document.getElementById('stat-total');
const heatmapContainer = document.getElementById('heatmap-container');

// Modals
const modalLogin = document.getElementById('modal-login');
const modalStart = document.getElementById('modal-start');
const modalClose = document.getElementById('modal-close');
const modalDelete = document.getElementById('modal-delete');

// Buttons
const btnStartFast = document.getElementById('btn-start-fast');
const btnConfirmStart = document.getElementById('btn-confirm-start');
const btnConfirmClose = document.getElementById('btn-confirm-close');
const btnConfirmDelete = document.getElementById('btn-confirm-delete');
const closeButtons = document.querySelectorAll('.close-modal');

// --- INIT ---
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setupEventListeners();
    
    if (authToken) {
        // Logged in
        modalLogin.classList.add('hidden');
        btnLogout.classList.remove('hidden');
        fetchCycles();
    } else {
        // Not logged in
        modalLogin.classList.remove('hidden');
        btnLogout.classList.add('hidden');
    }
});

// --- PWA SERVICE WORKER REGISTRATION ---
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Jyclo SW registrado com sucesso!', reg))
            .catch(err => console.log('Erro ao registrar Jyclo SW:', err));
    });
}

// --- STATE MANAGEMENT ---
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const icon = themeToggle.querySelector('i');
    if (theme === 'dark') {
        icon.className = 'ph ph-sun';
    } else {
        icon.className = 'ph ph-moon';
    }
}

// --- API CALLS ---
async function fetchWithAuth(url, options = {}) {
    if(!options.headers) options.headers = {};
    if(authToken) {
         options.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const res = await fetch(url, options);
    
    if (res.status === 401) {
        logout();
        throw new Error("Unauthorized");
    }
    
    return res;
}

async function loginUser(email, pin) {
    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, pin })
        });
        
        if (res.ok) {
            const data = await res.json();
            authToken = data.access_token;
            localStorage.setItem('jyclo_token', authToken);
            
            modalLogin.classList.add('hidden');
            btnLogout.classList.remove('hidden');
            showToast('Bem-vindo!', 'success');
            fetchCycles();
        } else {
            const errorData = await res.json();
            showToast(errorData.detail || 'Erro ao fazer login. Verifique o PIN.', 'error');
        }
    } catch (error) {
        console.error(error);
        showToast('Erro de conexão.', 'error');
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('jyclo_token');
    
    cycles = [];
    renderDashboard();
    
    modalLogin.classList.remove('hidden');
    btnLogout.classList.add('hidden');
}

async function fetchCycles() {
    try {
        const res = await fetchWithAuth('/api/cycles');
        const data = await res.json();
        cycles = data.checkpoints;
        stats = data.stats;
        renderDashboard();
    } catch (error) {
        if(error.message !== "Unauthorized") {
            showToast('Erro ao carregar os dados.', 'error');
            console.error(error);
        }
    }
}

async function startCycle(payload) {
    try {
        const res = await fetchWithAuth('/api/cycles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            closeAllModals();
            showToast('Jejum iniciado com sucesso!', 'success');
            fetchCycles(); // Refresh all
        }
    } catch (error) {
         if(error.message !== "Unauthorized") showToast('Erro ao iniciar jejum.', 'error');
    }
}

async function closeCycle(id, payload) {
    try {
        const res = await fetchWithAuth(`/api/cycles/${id}/close`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            closeAllModals();
            showToast('Jejum quebrado com sucesso!', 'success');
            fetchCycles();
        }
    } catch (error) {
        if(error.message !== "Unauthorized") showToast('Erro ao quebrar jejum.', 'error');
    }
}

async function deleteCycle(id) {
    try {
        const res = await fetchWithAuth(`/api/cycles/${id}`, { method: 'DELETE' });
        if (res.ok) {
            closeAllModals();
            showToast('Ciclo excluído.', 'success');
            fetchCycles();
        }
    } catch (error) {
        if(error.message !== "Unauthorized") showToast('Erro ao excluir ciclo.', 'error');
    }
}

// --- RENDERING ---
function renderDashboard() {
    // 1. Render Stats
    statTotal.textContent = stats.total;
    statLongest.textContent = stats.longest_window > 0 ? `${stats.longest_window}h` : '0h';
    
    // Calculate frequency (days with activity in last 30 days)
    const activeDaysCount = calculateFrequency(cycles);
    statStreak.textContent = activeDaysCount;

    // 2. Render Heatmap
    renderHeatmap(cycles);

    // Disable start button if there's an active cycle
    const hasActive = cycles.some(c => c.status === 'ativo');
    if(hasActive) {
        btnStartFast.style.display = 'none';
    } else {
        btnStartFast.style.display = 'flex';
    }

    // 2. Render Cards
    renderCards();
}

function renderCards() {
    cardsContainer.innerHTML = '';
    
    // Clear existing timer if any
    if (globalTimerInstance) {
        clearInterval(globalTimerInstance);
        globalTimerInstance = null;
    }

    if (cycles.length === 0) {
        cardsContainer.innerHTML = `
            <div class="loading-state">
                <i class="ph ph-coffee"></i>
                <p>Nenhum jejum registrado. Comece um agora!</p>
            </div>
        `;
        return;
    }

    cycles.forEach(cycle => {
        const card = document.createElement('div');
        card.className = `cycle-card glass-panel ${cycle.status === 'ativo' ? 'active' : ''}`;
        
        const isAtivo = cycle.status === 'ativo';
        const startDate = new Date(`${cycle.data_inicio}Z`); // ensure UTC parsed correctly depending on backend format
        const formattedDate = startDate.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
        const formatTime = startDate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

        // Build Inner HTML
        let statusHtml = isAtivo 
            ? `<span class="card-status status-active">Em Andamento</span>` 
            : `<span class="card-status status-closed">Encerrado</span>`;
        
        let commentHtml = '';
        if(cycle.comentario_inicio) {
            commentHtml += `<div class="card-comment"><i class="ph ph-arrow-clockwise"></i> ${cycle.comentario_inicio}</div>`;
        }
        if(cycle.comentario_fim) {
            commentHtml += `<div class="card-comment"><i class="ph ph-pause-circle"></i> ${cycle.comentario_fim}</div>`;
        }

        card.innerHTML = `
            <div class="card-header">
                ${statusHtml}
                <span class="card-date">${formattedDate} às ${formatTime}</span>
            </div>
            <div class="card-main">
                <div class="card-duration" id="duration-${cycle.id}" data-start="${cycle.data_inicio}" data-status="${cycle.status}">
                    ${isAtivo ? '00:00:00' : `${cycle.duracao_horas}h`}
                </div>
                
                <div class="card-details">
                    ${commentHtml}
                </div>
                
                <div class="card-actions z-over">
                    <button class="icon-btn danger btn-delete" data-id="${cycle.id}" title="Excluir">
                        <i class="ph ph-trash"></i>
                    </button>
                </div>
            </div>
        `;

        // Click Evens on Card
        card.addEventListener('click', (e) => {
            // Prevent if clicking on delete button
            if(e.target.closest('.btn-delete')) return;
            
            if (isAtivo) {
                openCloseModal(cycle);
            }
        });

        // Click Event on Delete
        const delBtn = card.querySelector('.btn-delete');
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // stop triggering card click
            openDeleteModal(cycle.id);
        });

        cardsContainer.appendChild(card);
    });

    // Start a single global timer if there's any active cycle
    const hasActiveNow = cycles.some(c => c.status === 'ativo');
    if (hasActiveNow) {
        startGlobalTimer();
    }
}

function startGlobalTimer() {
    // Initial update
    updateActiveTimers();
    // Set interval
    globalTimerInstance = setInterval(updateActiveTimers, 1000);
}

function updateActiveTimers() {
    const activeElements = document.querySelectorAll('.card-duration[data-status="ativo"]');
    if (activeElements.length === 0 && globalTimerInstance) {
        clearInterval(globalTimerInstance);
        globalTimerInstance = null;
        return;
    }

    const now = new Date();
    activeElements.forEach(el => {
        const startTimeStr = el.getAttribute('data-start');
        if (!startTimeStr) return;

        // Force UTC parsing
        let isoStr = startTimeStr;
        if (!isoStr.endsWith('Z') && !isoStr.includes('+') && !isoStr.includes('-')) {
            isoStr += 'Z';
        }

        const startObj = new Date(isoStr);
        let diffMs = now.getTime() - startObj.getTime();
        
        if (diffMs < 0) diffMs = 0;

        const hrs = Math.floor(diffMs / 3600000);
        const mins = Math.floor((diffMs % 3600000) / 60000);
        const secs = Math.floor((diffMs % 60000) / 1000);

        const pad = (n) => String(n).padStart(2, '0');
        el.textContent = `${pad(hrs)}:${pad(mins)}:${pad(secs)}`;
    });
}


// --- EVENT LISTENERS & MODALS ---
function setupEventListeners() {
    // Auth & Header
    btnLogout.addEventListener('click', logout);

    document.getElementById('form-login').addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const pin = document.getElementById('login-pin').value;
        loginUser(email, pin);
    });

    // Start Fast setup
    btnStartFast.addEventListener('click', openStartModal);

    // Global Modal Close
    closeButtons.forEach(btn => {
        btn.addEventListener('click', closeAllModals);
    });

    // Form Submits
    btnConfirmStart.addEventListener('click', () => {
        const typeSelect = document.getElementById('start-type');
        const typeValue = typeSelect.value;
        const typeText = typeSelect.options[typeSelect.selectedIndex].text;
        
        const date = document.getElementById('start-date').value;
        const time = document.getElementById('start-time').value;
        
        if(!date || !time) {
            showToast('Data e hora são obrigatórios.', 'error');
            return;
        }

        // Convert Local input to UTC ISO String to send to server
        const localDateTime = new Date(`${date}T${time}`);
        const isoString = localDateTime.toISOString();

        startCycle({
            comentario_inicio: typeText,
            data_inicio: isoString
        });
    });

    btnConfirmClose.addEventListener('click', () => {
        const closeType = document.getElementById('close-type').value;
        
        const date = document.getElementById('close-date').value;
        const time = document.getElementById('close-time').value;
        
        let payload = { comentario_fim: closeType };
        
        if (date && time) {
            const localDateTime = new Date(`${date}T${time}`);
            payload.data_fim = localDateTime.toISOString();
        }

        if(selectedCycleId) {
            closeCycle(selectedCycleId, payload);
        }
    });

    btnConfirmDelete.addEventListener('click', () => {
        if(selectedCycleId) {
            deleteCycle(selectedCycleId);
        }
    });
}

function openStartModal() {
    // defaults
    document.getElementById('start-type').selectedIndex = 0;
    
    // Set current local time
    const now = new Date();
    document.getElementById('start-date').value = now.toISOString().split('T')[0];
    document.getElementById('start-time').value = now.toTimeString().split(' ')[0].slice(0,5);

    modalStart.classList.remove('hidden');
}

function openCloseModal(cycle) {
    selectedCycleId = cycle.id;
    document.getElementById('close-type').selectedIndex = 0;
    
    // Set current local time for closing
    const now = new Date();
    document.getElementById('close-date').value = now.toISOString().split('T')[0];
    document.getElementById('close-time').value = now.toTimeString().split(' ')[0].slice(0,5);
    
    // Copy the current duration into modal
    const liveDurStr = document.getElementById(`duration-${cycle.id}`).textContent;
    document.getElementById('close-duration').textContent = liveDurStr;

    modalClose.classList.remove('hidden');
}

function openDeleteModal(id) {
    selectedCycleId = id;
    modalDelete.classList.remove('hidden');
}

function calculateFrequency(cyclesList) {
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    const activeDays = new Set();
    cyclesList.forEach(c => {
        if (c.status === 'fechado') {
            const date = new Date(c.data_inicio + (c.data_inicio.endsWith('Z') ? '' : 'Z'));
            if (date >= thirtyDaysAgo) {
                activeDays.add(date.toISOString().split('T')[0]);
            }
        }
    });
    return activeDays.size;
}

function renderHeatmap(cyclesList) {
    heatmapContainer.innerHTML = '';
    const today = new Date();
    
    // We want to show ~22 weeks (154 days) to fill the screen
    const daysToShow = 154;
    const startDate = new Date();
    startDate.setDate(today.getDate() - daysToShow + 1);

    // Map activity per day { 'YYYY-MM-DD': totalHours }
    const dailyActivity = {};
    cyclesList.forEach(c => {
        if (c.status === 'fechado' && c.duracao_horas) {
            // Get local date part YYYY-MM-DD from data_inicio string
            // Usually format is "YYYY-MM-DDTHH:MM:SS..."
            const dateKey = c.data_inicio.split('T')[0];
            dailyActivity[dateKey] = (dailyActivity[dateKey] || 0) + parseFloat(c.duracao_horas);
        }
    });

    for (let i = 0; i < daysToShow; i++) {
        const d = new Date(startDate);
        d.setDate(startDate.getDate() + i);
        const dateKey = d.toISOString().split('T')[0];
        const hours = dailyActivity[dateKey] || 0;

        const dayEl = document.createElement('div');
        dayEl.className = 'hm-day';
        
        // Define level based on hours (User suggested thresholds)
        let level = 0;
        if (hours >= 12 && hours < 16) level = 1;
        else if (hours >= 16 && hours < 18) level = 2;
        else if (hours >= 18 && hours < 22) level = 3;
        else if (hours >= 22) level = 4;

        dayEl.classList.add(`hm-level-${level}`);
        // No interaction/title requested anymore
        
        heatmapContainer.appendChild(dayEl);
    }
}

function closeAllModals() {
    modalStart.classList.add('hidden');
    modalClose.classList.add('hidden');
    modalDelete.classList.add('hidden');
    selectedCycleId = null;
}

// --- UTILS ---
function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    const msgEl = document.getElementById('toast-msg');
    const iconEl = document.getElementById('toast-icon');

    msgEl.textContent = msg;
    toast.className = `toast ${type}`;
    
    if (type === 'success') {
        iconEl.className = 'ph ph-check-circle';
    } else {
        iconEl.className = 'ph ph-warning-circle';
    }

    // Hide after 3s
    setTimeout(() => {
        toast.classList.add('hidden');
        toast.className = 'toast hidden';
    }, 3000);
}
