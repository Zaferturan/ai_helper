/**
 * AI Yardımcı Frontend Application
 * HTML+JS frontend for Nilüfer Belediyesi AI Assistant
 * 
 * Features:
 * - Email-based authentication with magic links
 * - Profile completion for new users
 * - AI response generation with customizable parameters
 * - Admin statistics panel for administrators
 * - Multi-user support with localStorage
 */

// Configuration
const CONFIG = {
    BACKEND_URL: 'https://yardimci.niluferyapayzeka.tr/api/v1',
    PRODUCTION_URL: 'https://yardimci.niluferyapayzeka.tr',
    STORAGE_KEYS: {
        AUTH_TOKEN: 'auth_token',
        USER_EMAIL: 'user_email',
        IS_ADMIN: 'is_admin',
        USER_PROFILE: 'user_profile'
    }
};

// Global state management
class AppState {
    constructor() {
        this.authenticated = false;
        this.userEmail = null;
        this.isAdmin = false;
        this.userProfile = null;
        this.authToken = null;
        this.responseHistory = [];
        this.currentResponseId = null;
    }

    // Load state from localStorage
    loadFromStorage() {
        this.authToken = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        this.userEmail = localStorage.getItem(CONFIG.STORAGE_KEYS.USER_EMAIL);
        this.isAdmin = localStorage.getItem(CONFIG.STORAGE_KEYS.IS_ADMIN) === 'true';
        this.userProfile = JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE) || 'null');
        
        this.authenticated = !!(this.authToken && this.userEmail);
        
        console.log('App state loaded:', {
            authenticated: this.authenticated,
            userEmail: this.userEmail,
            isAdmin: this.isAdmin
        });
    }

    // Save state to localStorage
    saveToStorage() {
        if (this.authToken) localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, this.authToken);
        if (this.userEmail) localStorage.setItem(CONFIG.STORAGE_KEYS.USER_EMAIL, this.userEmail);
        localStorage.setItem(CONFIG.STORAGE_KEYS.IS_ADMIN, this.isAdmin.toString());
        if (this.userProfile) localStorage.setItem(CONFIG.STORAGE_KEYS.USER_PROFILE, JSON.stringify(this.userProfile));
    }

    // Clear all state
    clear() {
        this.authenticated = false;
        this.userEmail = null;
        this.isAdmin = false;
        this.userProfile = null;
        this.authToken = null;
        this.responseHistory = [];
        this.currentResponseId = null;
        
        // Clear localStorage
        Object.values(CONFIG.STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
    }
}

// Initialize global state
const appState = new AppState();

// UI Management
class UIManager {
    constructor() {
        this.screens = {
            login: document.getElementById('login-screen'),
            profile: document.getElementById('profile-screen'),
            main: document.getElementById('main-screen')
        };
        
        this.elements = {
            // Login elements
            emailInput: document.getElementById('email-input'),
            sendCodeBtn: document.getElementById('send-code-btn'),
            codeInput: document.getElementById('code-input'),
            verifyBtn: document.getElementById('verify-btn'),
            resendBtn: document.getElementById('resend-btn'),
            backBtn: document.getElementById('back-btn'),
            loginError: document.getElementById('login-error'),
            
            // Profile elements
            profileName: document.getElementById('profile-name'),
            profileDepartment: document.getElementById('profile-department'),
            completeProfileBtn: document.getElementById('complete-profile-btn'),
            profileError: document.getElementById('profile-error'),
            
            // Main app elements
            userProfile: document.getElementById('user-profile'),
            logoutBtn: document.getElementById('logout-btn'),
            adminPanel: document.getElementById('admin-panel'),
            adminStatsContent: document.getElementById('admin-stats-content'),
            refreshAdminBtn: document.getElementById('refresh-admin-btn'),
            
            // Request elements
            originalText: document.getElementById('original-text'),
            customInput: document.getElementById('custom-input'),
            generateBtn: document.getElementById('generate-btn'),
            
            // Response elements
            responseArea: document.getElementById('response-area'),
            mainResponse: document.getElementById('main-response'),
            mainCopyBtn: document.getElementById('main-copy-btn'),
            newRequestBtn: document.getElementById('new-request-btn'),
            previousResponses: document.getElementById('previous-responses'),
            
            // Settings elements
            responseSettings: document.getElementById('response-settings'),
            temperature: document.getElementById('temperature'),
            topP: document.getElementById('top-p'),
            repetitionPenalty: document.getElementById('repetition-penalty'),
            answerType: document.getElementById('answer-type'),
            
            // Loading
            loadingOverlay: document.getElementById('loading-overlay')
        };
    }

    // Show specific screen
    showScreen(screenName) {
        Object.values(this.screens).forEach(screen => {
            screen.classList.add('hidden');
        });
        this.screens[screenName].classList.remove('hidden');
    }

    // Show/hide elements
    show(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) element.classList.remove('hidden');
    }

    hide(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) element.classList.add('hidden');
    }

    // Show error message
    showError(element, message) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.textContent = message;
            element.classList.remove('hidden');
        }
    }

    // Hide error message
    hideError(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.classList.add('hidden');
        }
    }

    // Show loading overlay
    showLoading() {
        this.elements.loadingOverlay.classList.remove('hidden');
    }

    // Hide loading overlay
    hideLoading() {
        this.elements.loadingOverlay.classList.add('hidden');
    }

    // Update user profile display
    updateUserProfile(profile) {
        if (profile) {
            this.elements.userProfile.textContent = `👤 ${profile.full_name} - ${profile.department}`;
        } else {
            this.elements.userProfile.textContent = '👤 Kullanıcı';
        }
    }

    // Show admin panel if user is admin
    updateAdminPanel() {
        if (appState.isAdmin) {
            this.elements.adminPanel.classList.remove('hidden');
        } else {
            this.elements.adminPanel.classList.add('hidden');
        }
    }
}

// Initialize UI manager
const ui = new UIManager();

// API Client
class APIClient {
    constructor() {
        this.baseURL = CONFIG.BACKEND_URL;
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        // Add auth header if token exists
        if (appState.authToken) {
            defaultOptions.headers['Authorization'] = `Bearer ${appState.authToken}`;
        }

        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            console.log(`API Request: ${options.method || 'GET'} ${url}`);
            const response = await fetch(url, finalOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log(`API Response:`, data);
            return data;
        } catch (error) {
            console.error(`API Error:`, error);
            throw error;
        }
    }

    // Authentication methods
    async sendLoginCode(email) {
        return this.request('/send', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    }

    async verifyCode(email, code) {
        return this.request('/verify-code', {
            method: 'POST',
            body: JSON.stringify({ email, code })
        });
    }

    async getProfile() {
        return this.request('/profile');
    }

    async completeProfile(fullName, department) {
        return this.request('/complete-profile', {
            method: 'POST',
            body: JSON.stringify({ full_name: fullName, department })
        });
    }

    async logout() {
        return this.request('/logout', {
            method: 'POST'
        });
    }

    // Admin methods
    async getAdminStats() {
        return this.request('/admin/stats');
    }

    async getAdminUsers() {
        return this.request('/admin/users');
    }

}

// Initialize API client
const api = new APIClient();

// Authentication Manager
class AuthManager {
    constructor() {
        this.currentStep = 'email'; // 'email', 'code', 'profile', 'main'
    }

    // Initialize authentication check
    async init() {
        console.log('AuthManager: Initializing...');
        
        // Load state from storage
        appState.loadFromStorage();
        
        // Check for magic link parameters
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');
        const sessionId = urlParams.get('session_id');
        const userEmail = urlParams.get('user_email');
        const isAdmin = urlParams.get('is_admin') === 'true';
        
        if (token) {
            console.log('Magic link detected, verifying token...');
            await this.handleMagicLink(token);
        } else if (sessionId && userEmail) {
            console.log('Session parameters detected, loading session...');
            await this.handleSessionParams(sessionId, userEmail, isAdmin);
        } else if (appState.authenticated) {
            console.log('Existing session found, verifying...');
            await this.verifyExistingSession();
        } else {
            console.log('No session found, showing login screen');
            this.showLoginScreen();
        }
    }

    // Handle magic link authentication
    async handleMagicLink(token) {
        try {
            ui.showLoading();
            
            const response = await api.request('/auth/verify-magic-link', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.success) {
                appState.authToken = response.access_token;
                appState.userEmail = response.user_email;
                appState.isAdmin = response.is_admin;
                appState.userProfile = {
                    full_name: response.full_name,
                    department: response.department
                };
                
                appState.saveToStorage();
                
                if (response.profile_completed) {
                    this.showMainScreen();
                } else {
                    this.showProfileScreen();
                }
            } else {
                throw new Error(response.message || 'Magic link verification failed');
            }
        } catch (error) {
            console.error('Magic link error:', error);
            ui.showError('login-error', 'Magic link doğrulaması başarısız oldu.');
            this.showLoginScreen();
        } finally {
            ui.hideLoading();
        }
    }

    // Handle session parameters
    async handleSessionParams(sessionId, userEmail, isAdmin) {
        try {
            ui.showLoading();
            
            // Get session details from backend
            const sessionResponse = await api.request(`/auth/session/${sessionId}`);
            
            if (sessionResponse.user_email === userEmail) {
                appState.authToken = sessionResponse.access_token;
                appState.userEmail = userEmail;
                appState.isAdmin = isAdmin;
                appState.userProfile = {
                    full_name: sessionResponse.full_name,
                    department: sessionResponse.department
                };
                
                appState.saveToStorage();
                
                if (sessionResponse.profile_completed) {
                    this.showMainScreen();
                } else {
                    this.showProfileScreen();
                }
            } else {
                throw new Error('Session verification failed');
            }
        } catch (error) {
            console.error('Session params error:', error);
            ui.showError('login-error', 'Session doğrulaması başarısız oldu.');
            this.showLoginScreen();
        } finally {
            ui.hideLoading();
        }
    }

    // Verify existing session
    async verifyExistingSession() {
        try {
            ui.showLoading();
            
            const profile = await api.getProfile();
            
            if (profile.success) {
                appState.userProfile = profile;
                appState.isAdmin = profile.is_admin;
                appState.saveToStorage();
                
                if (profile.profile_completed) {
                    this.showMainScreen();
                } else {
                    this.showProfileScreen();
                }
            } else {
                throw new Error('Session verification failed');
            }
        } catch (error) {
            console.error('Session verification error:', error);
            appState.clear();
            this.showLoginScreen();
        } finally {
            ui.hideLoading();
        }
    }

    // Show login screen
    showLoginScreen() {
        this.currentStep = 'email';
        ui.showScreen('login');
        ui.hide('code-section');
        ui.show('email-section');
        ui.hideError('login-error');
        
        // Clear form
        ui.elements.emailInput.value = '';
        ui.elements.codeInput.value = '';
    }

    // Show profile completion screen
    showProfileScreen() {
        this.currentStep = 'profile';
        ui.showScreen('profile');
        ui.hideError('profile-error');
        
        // Pre-fill if available
        if (appState.userProfile) {
            ui.elements.profileName.value = appState.userProfile.full_name || '';
            ui.elements.profileDepartment.value = appState.userProfile.department || '';
        }
    }

    // Show main application screen
    showMainScreen() {
        this.currentStep = 'main';
        ui.showScreen('main');
        
        // Update UI with user info
        ui.updateUserProfile(appState.userProfile);
        ui.updateAdminPanel();
        
        // Load admin stats if admin
        if (appState.isAdmin) {
            this.loadAdminStats();
        }
    }

    // Send login code
    async sendLoginCode() {
        console.log('sendLoginCode called');
        console.log('ui.elements.emailInput:', ui.elements.emailInput);
        
        const email = ui.elements.emailInput.value.trim();
        console.log('email value:', email);
        
        if (!email) {
            ui.showError('login-error', 'Lütfen e-posta adresinizi girin.');
            return;
        }
        
        if (!email.includes('@nilufer.bel.tr')) {
            ui.showError('login-error', 'Lütfen geçerli bir Nilüfer Belediyesi e-posta adresi girin.');
            return;
        }
        
        try {
            ui.showLoading();
            ui.hideError('login-error');
            
            await api.sendLoginCode(email);
            
            this.currentStep = 'code';
            ui.hide('email-section');
            ui.show('code-section');
            
        } catch (error) {
            console.error('Send code error:', error);
            ui.showError('login-error', 'Kod gönderilirken hata oluştu. Lütfen tekrar deneyin.');
        } finally {
            ui.hideLoading();
        }
    }

    // Verify code
    async verifyCode() {
        const email = ui.elements.emailInput.value.trim();
        const code = ui.elements.codeInput.value.trim();
        
        if (!code) {
            ui.showError('login-error', 'Lütfen doğrulama kodunu girin.');
            return;
        }
        
        try {
            ui.showLoading();
            ui.hideError('login-error');
            
            const response = await api.verifyCode(email, code);
            
            if (response.access_token) {
                appState.authToken = response.access_token;
                appState.userEmail = email;
                appState.isAdmin = response.is_admin;
                appState.userProfile = {
                    full_name: response.full_name,
                    department: response.department
                };
                
                appState.saveToStorage();
                
                if (response.profile_completed) {
                    this.showMainScreen();
                } else {
                    this.showProfileScreen();
                }
            } else {
                throw new Error(response.message || 'Kod doğrulaması başarısız');
            }
        } catch (error) {
            console.error('Verify code error:', error);
            ui.showError('login-error', 'Kod doğrulaması başarısız. Lütfen tekrar deneyin.');
        } finally {
            ui.hideLoading();
        }
    }

    // Complete profile
    async completeProfile() {
        const fullName = ui.elements.profileName.value.trim();
        const department = ui.elements.profileDepartment.value.trim();
        
        if (!fullName) {
            ui.showError('profile-error', 'Lütfen ad soyadınızı girin.');
            return;
        }
        
        if (!department) {
            ui.showError('profile-error', 'Lütfen birim/müdürlüğünüzü seçin.');
            return;
        }
        
        try {
            ui.showLoading();
            ui.hideError('profile-error');
            
            const response = await api.completeProfile(fullName, department);
            
            if (response.success) {
                appState.userProfile.full_name = fullName;
                appState.userProfile.department = department;
                appState.saveToStorage();
                
                this.showMainScreen();
            } else {
                throw new Error(response.message || 'Profil tamamlama başarısız');
            }
        } catch (error) {
            console.error('Complete profile error:', error);
            ui.showError('profile-error', 'Profil tamamlama başarısız. Lütfen tekrar deneyin.');
        } finally {
            ui.hideLoading();
        }
    }

    // Logout
    async logout() {
        try {
            ui.showLoading();
            
            // Call backend logout
            await api.logout();
            
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local state regardless of backend response
            appState.clear();
            this.showLoginScreen();
            ui.hideLoading();
        }
    }

    // Load admin statistics
    async loadAdminStats() {
        if (!appState.isAdmin) return;
        
        try {
            const usersResponse = await api.getAdminUsers();
            
            if (usersResponse.success) {
                const users = usersResponse.users;
                const totalGenerated = users.reduce((sum, user) => sum + (user.total_requests || 0), 0);
                const totalAnswered = users.reduce((sum, user) => sum + (user.answered_requests || 0), 0);
                
                const statsHTML = `
                    <div class="admin-stats">
                        <h3>📈 Genel İstatistikler</h3>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-number">${totalGenerated}</div>
                                <div class="stat-label">Toplam Üretilen Yanıt</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${totalAnswered}</div>
                                <div class="stat-label">Cevaplanan İstek</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">${users.length}</div>
                                <div class="stat-label">Aktif Kullanıcı</div>
                            </div>
                        </div>
                        
                        <h3>👥 Kullanıcı Detayları</h3>
                        <div class="users-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Kullanıcı</th>
                                        <th>Birim</th>
                                        <th>Üretilen Yanıt</th>
                                        <th>Cevaplanan İstek</th>
                                        <th>Son Giriş</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${users.map(user => `
                                        <tr>
                                            <td>${user.full_name || 'N/A'}</td>
                                            <td>${user.department || 'N/A'}</td>
                                            <td>${user.total_requests || 0}</td>
                                            <td>${user.answered_requests || 0}</td>
                                            <td>${user.last_login ? new Date(user.last_login).toLocaleDateString('tr-TR') : 'N/A'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
                
                ui.elements.adminStatsContent.innerHTML = statsHTML;
            }
        } catch (error) {
            console.error('Load admin stats error:', error);
            ui.elements.adminStatsContent.innerHTML = '<div class="error">İstatistikler yüklenirken hata oluştu.</div>';
        }
    }
}

// Initialize auth manager
const authManager = new AuthManager();

// AI Response Manager
class ResponseManager {
    constructor() {
        this.currentResponse = null;
        this.responseHistory = [];
    }

    // Generate AI response
    async generateResponse() {
        const originalText = ui.elements.originalText.value.trim();
        const customInput = ui.elements.customInput.value.trim();
        
        if (!originalText && !customInput) {
            alert('Lütfen en az bir istek metni girin.');
            return;
        }
        
        const requestText = customInput || originalText;
        
        try {
            ui.showLoading();
            
            // Step 1: Create request
            const requestResponse = await api.request('/requests', {
                method: 'POST',
                body: JSON.stringify({
                    original_text: requestText,
                    response_type: ui.elements.answerType.value,
                    is_new_request: true
                })
            });
            
            if (!requestResponse.id) {
                throw new Error('Request oluşturulamadı');
            }
            
            // Step 2: Generate response
            const generateResponse = await api.request('/generate', {
                method: 'POST',
                body: JSON.stringify({
                    request_id: requestResponse.id,
                    model_name: 'gpt-4o-mini', // Default model
                    custom_input: customInput,
                    temperature: parseFloat(ui.elements.temperature.value),
                    top_p: parseFloat(ui.elements.topP.value),
                    repetition_penalty: parseFloat(ui.elements.repetitionPenalty.value),
                    system_prompt: ""
                })
            });
            
            if (generateResponse.response_text) {
                this.currentResponse = generateResponse.response_text;
                this.displayResponse(generateResponse.response_text);
                this.addToHistory(generateResponse.response_text);
            } else {
                throw new Error('Yanıt üretimi başarısız');
            }
        } catch (error) {
            console.error('Generate response error:', error);
            alert('Yanıt üretilirken hata oluştu. Lütfen tekrar deneyin.');
        } finally {
            ui.hideLoading();
        }
    }

    // Display response
    displayResponse(response) {
        ui.elements.mainResponse.innerHTML = `<div class="response-text">${response}</div>`;
        ui.show('response-area');
        ui.show('previous-responses');
    }

    // Add response to history
    addToHistory(response) {
        this.responseHistory.unshift(response);
        
        // Keep only last 4 responses
        if (this.responseHistory.length > 4) {
            this.responseHistory = this.responseHistory.slice(0, 4);
        }
        
        this.updatePreviousResponses();
    }

    // Update previous responses display
    updatePreviousResponses() {
        for (let i = 0; i < 4; i++) {
            const responseText = this.responseHistory[i];
            const textElement = document.getElementById(`prev-text-${i + 1}`);
            const contentElement = document.getElementById(`prev-${i + 1}-content`);
            
            if (responseText) {
                textElement.innerHTML = `<div class="response-text">${responseText}</div>`;
                contentElement.parentElement.classList.remove('hidden');
            } else {
                contentElement.parentElement.classList.add('hidden');
            }
        }
    }

    // Copy response to clipboard
    async copyResponse(responseElement) {
        try {
            const text = responseElement.textContent || responseElement.innerText;
            await navigator.clipboard.writeText(text);
            
            // Show success feedback
            const button = event.target;
            const originalText = button.textContent;
            button.textContent = '✅ Kopyalandı!';
            button.classList.add('success');
            
            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('success');
            }, 2000);
            
        } catch (error) {
            console.error('Copy error:', error);
            alert('Kopyalama başarısız. Lütfen metni manuel olarak seçin.');
        }
    }

    // Start new request
    newRequest() {
        ui.elements.originalText.value = '';
        ui.elements.customInput.value = '';
        ui.hide('response-area');
        ui.hide('previous-responses');
        this.currentResponse = null;
    }
}

// Initialize response manager
const responseManager = new ResponseManager();

// Event Listeners
class EventManager {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Login events
        ui.elements.sendCodeBtn.addEventListener('click', () => authManager.sendLoginCode());
        ui.elements.verifyBtn.addEventListener('click', () => authManager.verifyCode());
        ui.elements.resendBtn.addEventListener('click', () => authManager.sendLoginCode());
        ui.elements.backBtn.addEventListener('click', () => authManager.showLoginScreen());
        
        // Profile events
        ui.elements.completeProfileBtn.addEventListener('click', () => authManager.completeProfile());
        
        // Main app events
        ui.elements.logoutBtn.addEventListener('click', () => authManager.logout());
        ui.elements.refreshAdminBtn.addEventListener('click', () => authManager.loadAdminStats());
        
        // Response events
        ui.elements.generateBtn.addEventListener('click', () => responseManager.generateResponse());
        ui.elements.mainCopyBtn.addEventListener('click', () => responseManager.copyResponse(ui.elements.mainResponse));
        ui.elements.newRequestBtn.addEventListener('click', () => responseManager.newRequest());
        
        // Previous response copy events
        for (let i = 1; i <= 4; i++) {
            const copyBtn = document.getElementById(`prev-copy-btn-${i}`);
            const textElement = document.getElementById(`prev-text-${i}`);
            if (copyBtn && textElement) {
                copyBtn.addEventListener('click', () => responseManager.copyResponse(textElement));
            }
        }
        
        // Settings events
        ui.elements.temperature.addEventListener('input', (e) => {
            document.getElementById('temperature-value').textContent = e.target.value;
        });
        
        ui.elements.topP.addEventListener('input', (e) => {
            document.getElementById('top-p-value').textContent = e.target.value;
        });
        
        ui.elements.repetitionPenalty.addEventListener('input', (e) => {
            document.getElementById('repetition-penalty-value').textContent = e.target.value;
        });
        
        // Enter key events
        ui.elements.emailInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') authManager.sendLoginCode();
        });
        
        ui.elements.codeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') authManager.verifyCode();
        });
        
        ui.elements.profileName.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') authManager.completeProfile();
        });
        
        ui.elements.profileDepartment.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') authManager.completeProfile();
        });
    }
}

// Initialize event manager
const eventManager = new EventManager();

// Utility functions for accordion
function toggleAdminPanel() {
    const panel = document.getElementById('admin-panel');
    const content = panel.querySelector('.accordion-content');
    const icon = panel.querySelector('.accordion-icon');
    
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        icon.textContent = '▲';
    } else {
        content.classList.add('hidden');
        icon.textContent = '▼';
    }
}

function toggleAccordion(id) {
    const content = document.getElementById(`${id}-content`);
    const icon = content.parentElement.querySelector('.accordion-icon');
    
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        icon.textContent = '▲';
    } else {
        content.classList.add('hidden');
        icon.textContent = '▼';
    }
}

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    console.log('AI Yardımcı Frontend initialized');
    
    try {
        await authManager.init();
    } catch (error) {
        console.error('App initialization error:', error);
        ui.showError('login-error', 'Uygulama başlatılırken hata oluştu.');
    }
});

// Export for global access
window.authManager = authManager;
window.responseManager = responseManager;
window.toggleAdminPanel = toggleAdminPanel;
window.toggleAccordion = toggleAccordion;
