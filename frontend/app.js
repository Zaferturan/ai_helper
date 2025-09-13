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

// API Client for backend communication
class APIClient {
    constructor() {
        this.baseURL = CONFIG.BACKEND_URL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    }

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
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        return this.request('/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }

    async updateProfile(profileData) {
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        return this.request('/profile', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(profileData)
        });
    }

    async getSessionStatus() {
        return this.request('/session-status');
    }

    async getSessionDetails(sessionId) {
        return this.request(`/session/${sessionId}`);
    }

    async getUsers() {
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        return this.request('/admin/users', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }

    async getRequests() {
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        return this.request('/requests', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    }

    async createRequest(requestData) {
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        return this.request('/requests', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
    }

    async generateResponse(requestData) {
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        return this.request('/generate', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
    }
}

// Authentication Manager
class AuthManager {
    constructor() {
        this.api = new APIClient();
        this.appState = new AppState();
    }

    async init() {
        console.log('AuthManager initializing...');
        this.appState.loadFromStorage();
        
        if (this.appState.authenticated) {
            await this.validateToken();
        }
    }

    async validateToken() {
        try {
            const profile = await this.api.getProfile();
            if (profile.email) {
                this.appState.userEmail = profile.email;
                this.appState.isAdmin = profile.is_admin || false;
                this.appState.userProfile = profile;
                this.saveToStorage();
                return true;
            }
        } catch (error) {
            console.error('Token validation failed:', error);
            this.logout();
        }
        return false;
    }

    async checkBackendSession() {
        try {
            console.log('Checking backend session...');
            const sessionStatus = await this.api.getSessionStatus();
            
            if (sessionStatus.sessions && sessionStatus.sessions.length > 0) {
                const latestSession = sessionStatus.sessions[0];
                const sessionDetails = await this.api.getSessionDetails(latestSession.session_id);
                
                if (sessionDetails.user_email) {
                    console.log('Backend session found:', sessionDetails.user_email);
                    
                    // Update app state
                    this.appState.authenticated = true;
                    this.appState.userEmail = sessionDetails.user_email;
                    this.appState.isAdmin = sessionDetails.is_admin || false;
                    this.appState.authToken = sessionDetails.access_token;
                    
                    // Save to localStorage
                    this.saveToStorage();
                    
                    // Show main app
                    ui.showMainApp();
                    
                    // Load admin stats if admin
                    if (this.appState.isAdmin) {
                        await this.loadAdminStats();
                    }
                    
                    return true;
                }
            }
            
            console.log('No backend session found');
            return false;
        } catch (error) {
            console.error('Backend session check failed:', error);
            return false;
        }
    }

    async sendCode(email) {
        try {
            const response = await this.api.sendLoginCode(email);
            return response;
        } catch (error) {
            console.error('Send code error:', error);
            throw error;
        }
    }

    async verifyCode(email, code) {
        try {
            const response = await this.api.verifyCode(email, code);
            
            if (response.access_token) {
                this.appState.authenticated = true;
                this.appState.userEmail = email;
                this.appState.isAdmin = response.is_admin || false;
                this.appState.authToken = response.access_token;
                
                this.saveToStorage();
                
                // Check if profile is completed
                if (response.profile_completed) {
                    ui.showMainApp();
                    if (this.appState.isAdmin) {
                        await this.loadAdminStats();
                    }
                } else {
                    ui.showProfileCompletion();
                }
                
                return true;
            }
            return false;
        } catch (error) {
            console.error('Verify code error:', error);
            throw error;
        }
    }

    copyPreviousResponse(responseId) {
        // Gradio app.py mantığı: önceki yanıtı kopyala ve seç
        const response = this.previousResponses.find(r => r.id === responseId);
        if (!response) {
            console.error('Yanıt bulunamadı:', responseId);
            return;
        }

        // Panoya kopyala
        navigator.clipboard.writeText(response.response_text).then(() => {
            console.log('Önceki yanıt kopyalandı:', responseId);
            // Başarı mesajı göster
            ui.showSuccess('Önceki yanıt kopyalandı!');
        }).catch(err => {
            console.error('Kopyalama hatası:', err);
            ui.showError('response-error', 'Kopyalama başarısız.');
        });
    }

    async loadAdminStats() {
        try {
            const usersResponse = await this.api.getUsers();
            
            if (usersResponse.users) {
                const statsHTML = this.generateAdminStatsHTML(usersResponse.users, []);
                document.getElementById('admin-stats-content').innerHTML = statsHTML;
            }
        } catch (error) {
            console.error('Admin stats load error:', error);
        }
    }

    generateAdminStatsHTML(users, requests) {
        const totalUsers = users.length;
        const activeUsers = users.filter(u => u.is_active).length;
        
        // Toplam üretilen yanıt sayısı
        const totalResponses = users.reduce((sum, user) => sum + (user.total_responses || 0), 0);
        
        // Toplam cevaplanan istek sayısı
        const totalAnsweredRequests = users.reduce((sum, user) => sum + (user.answered_requests || 0), 0);
        
        return `
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
                    <div style="background: #f3f4f6; padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #3b82f6;">${totalUsers}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;">Toplam Kullanıcı</div>
                    </div>
                    <div style="background: #f3f4f6; padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #10b981;">${activeUsers}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;">Aktif Kullanıcı</div>
                    </div>
                    <div style="background: #f3f4f6; padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #8b5cf6;">${totalResponses}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;">Toplam Üretilen Yanıt</div>
                    </div>
                    <div style="background: #f3f4f6; padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #f59e0b;">${totalAnsweredRequests}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;">Cevaplanan İstek Sayısı</div>
                    </div>
                </div>
                
                <h4 style="color: #1f2937; margin-bottom: 0.5rem; font-size: 1rem;">👥 Kullanıcı Detayları</h4>
                <div style="background: #f8f9fa; border-radius: 8px; overflow: hidden; border: 1px solid #dee2e6;">
                    <div style="background: #e9ecef; padding: 12px; font-weight: 600; color: #495057; border-bottom: 1px solid #dee2e6;">
                        <div style="display: grid; grid-template-columns: 2fr 2fr 2fr 1fr 1fr; gap: 10px; align-items: center;">
                            <div>Ad Soyad</div>
                            <div>Müdürlük</div>
                            <div>E-posta</div>
                            <div style="text-align: center;">Toplam Ürettiği Yanıt</div>
                            <div style="text-align: center;">Cevapladığı İstek Sayısı</div>
                        </div>
                    </div>
                    
                    <div style="max-height: 400px; overflow-y: auto;">
                        ${users.map(user => `
                            <div style="padding: 12px; border-bottom: 1px solid #dee2e6; display: grid; grid-template-columns: 2fr 2fr 2fr 1fr 1fr; gap: 10px; align-items: center;">
                                <div style="font-weight: 600; color: #333;">${user.full_name || 'Bilinmiyor'}</div>
                                <div style="color: #666; font-size: 0.9rem;">${user.department || 'Bilinmiyor'}</div>
                                <div style="color: #666; font-size: 0.9rem;">${user.email}</div>
                                <div style="text-align: center; font-weight: 600; color: #1976d2;">${user.total_responses || 0}</div>
                                <div style="text-align: center; font-weight: 600; color: #388e3c;">${user.answered_requests || 0}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    saveToStorage() {
        localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, this.appState.authToken);
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER_EMAIL, this.appState.userEmail);
        localStorage.setItem(CONFIG.STORAGE_KEYS.IS_ADMIN, this.appState.isAdmin.toString());
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER_PROFILE, JSON.stringify(this.appState.userProfile));
    }

    logout() {
        this.appState.authenticated = false;
        this.appState.userEmail = null;
        this.appState.isAdmin = false;
        this.appState.userProfile = null;
        this.appState.authToken = null;
        
        // Clear localStorage
        Object.values(CONFIG.STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
        
        ui.showLogin();
    }
}

// UI Manager
class UIManager {
    constructor() {
        this.elements = {};
        this.initializeElements();
    }

    initializeElements() {
        this.elements = {
            loginScreen: document.getElementById('login-screen'),
            profileScreen: document.getElementById('profile-screen'),
            mainScreen: document.getElementById('main-screen'),
            emailInput: document.getElementById('email-input'),
            sendBtn: document.getElementById('send-btn'),
            codeInput: document.getElementById('code-input'),
            verifyBtn: document.getElementById('verify-btn'),
            fullNameInput: document.getElementById('profile-name'),
            departmentInput: document.getElementById('profile-department'),
            saveProfileBtn: document.getElementById('complete-profile-btn'),
            logoutBtn: document.getElementById('logout-btn'),
            adminPanel: document.getElementById('admin-panel'),
            temperature: document.getElementById('temperature'),
            topP: document.getElementById('top-p'),
            repetitionPenalty: document.getElementById('repetition-penalty'),
            // Main app elements
            requestInput: document.getElementById('original-text'),
            responseInput: document.getElementById('custom-input'),
            generateBtn: document.getElementById('generate-btn'),
            mainResponse: document.getElementById('main-response'),
            mainCopyBtn: document.getElementById('main-copy-btn'),
            newRequestBtn: document.getElementById('new-request-btn'),
            previousList: document.getElementById('previous-list'),
            modelSelect: document.getElementById('model-select'),
            maxTokens: document.getElementById('max-tokens'),
            userProfile: document.getElementById('user-profile')
        };
    }

    showLogin() {
        this.hideAllScreens();
        this.elements.loginScreen.classList.remove('hidden');
    }

    showProfileCompletion() {
        this.hideAllScreens();
        this.elements.profileScreen.classList.remove('hidden');
    }

    showMainApp() {
        this.hideAllScreens();
        this.hideLoadingScreen();
        this.elements.mainScreen.classList.remove('hidden');
        
        // Update user info
        const userEmail = localStorage.getItem(CONFIG.STORAGE_KEYS.USER_EMAIL);
        const userProfile = JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE) || 'null');
        
        if (userProfile && this.elements.userProfile) {
            this.elements.userProfile.textContent = `👤 ${userProfile.full_name || 'Kullanıcı'} - ${userProfile.department || 'Departman'}`;
        }
        
        // Show admin panel if admin
        const isAdmin = localStorage.getItem(CONFIG.STORAGE_KEYS.IS_ADMIN) === 'true';
        if (isAdmin) {
            this.elements.adminPanel.classList.remove('hidden');
        }
    }

    hideAllScreens() {
        this.elements.loginScreen.classList.add('hidden');
        this.elements.profileScreen.classList.add('hidden');
        this.elements.mainScreen.classList.add('hidden');
    }

    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
    }

    showLoading() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.style.display = 'flex';
        }
    }

    hideLoading() {
        this.hideLoadingScreen();
    }

    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.style.color = '#dc2626';
        }
    }

    clearError(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = '';
        }
    }
}

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

// AI Response Manager
class AIResponseManager {
    constructor() {
        this.previousResponses = [];
        this.currentRequestId = null;
        this.loadPreviousResponses();
    }

    async generateResponse() {
        try {
            ui.showLoading();
            
            const originalText = ui.elements.requestInput.value.trim();
            const customInput = ui.elements.responseInput.value.trim();
            const model = ui.elements.modelSelect.value;
            const temperature = parseFloat(ui.elements.temperature.value);
            const maxTokens = parseInt(ui.elements.maxTokens.value);
            
            if (!originalText) {
                ui.showError('response-error', 'Lütfen gelen istek/öneri metnini girin.');
                return;
            }

            // Maksimum 5 yanıt kontrolü (Gradio app.py'den)
            if (this.previousResponses.length >= 5) {
                ui.showError('response-error', '⚠️ Maksimum 5 yanıt üretildi! Yeni istek öneri için "Yeni İstek" butonuna basın.');
                return;
            }

            // Eğer yeni istekse request oluştur
            if (!this.currentRequestId) {
                const requestData = {
                    original_text: originalText,
                    response_type: "informative",
                    is_new_request: true
                };
                
                const requestResponse = await api.createRequest(requestData);
                if (requestResponse.id) {
                    this.currentRequestId = requestResponse.id;
                } else {
                    throw new Error(requestResponse.detail || 'İstek oluşturulamadı');
                }
            }

            // Yanıt üret
            const generateData = {
                request_id: this.currentRequestId,
                model_name: model,
                custom_input: customInput,
                temperature: temperature,
                top_p: 0.9,
                repetition_penalty: 1.2,
                system_prompt: ""
            };

            const response = await api.generateResponse(generateData);
            
            if (response.response_text) {
                // Yeni yanıtı oluştur (Gradio app.py formatında)
                const newResponse = {
                    id: response.id,
                    response_text: response.response_text,
                    created_at: new Date().toISOString(),
                    latency_ms: response.latency_ms || 0,
                    model_name: model
                };

                // Gradio app.py mantığı: history'ye başa ekle
                this.previousResponses.unshift(newResponse);
                
                // Ana yanıtı göster (en son üretilen)
                this.displayResponse(response.response_text);
                
                // Önceki yanıtları güncelle (history[1:] - ilk yanıt hariç)
                this.updatePreviousResponses();
                
                // Local storage'a kaydet
                this.savePreviousResponses();
                
                console.log('Yanıt başarıyla üretildi:', response.response_text.substring(0, 100) + '...');
                console.log('Toplam yanıt sayısı:', this.previousResponses.length);
            } else {
                throw new Error('Yanıt üretilemedi');
            }

        } catch (error) {
            console.error('Yanıt üretme hatası:', error);
            ui.showError('response-error', 'Yanıt üretilirken hata oluştu: ' + error.message);
        } finally {
            ui.hideLoading();
        }
    }

    displayResponse(text) {
        if (ui.elements.mainResponse) {
            ui.elements.mainResponse.textContent = text;
        }
    }

    copyResponse() {
        if (ui.elements.mainResponse) {
            const text = ui.elements.mainResponse.textContent;
            navigator.clipboard.writeText(text).then(() => {
                // Show success feedback
                const btn = ui.elements.mainCopyBtn;
                const originalText = btn.textContent;
                btn.textContent = '✅ Kopyalandı!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            }).catch(err => {
                console.error('Copy failed:', err);
                ui.showError('response-error', 'Kopyalama başarısız.');
            });
        }
    }

    newRequest() {
        // Gradio app.py mantığı: state'i temizle
        this.previousResponses = [];
        this.currentRequestId = null;
        
        // Input'ları temizle
        ui.elements.requestInput.value = '';
        ui.elements.responseInput.value = '';
        ui.elements.mainResponse.textContent = '';
        
        // Önceki yanıtları temizle
        const container = document.getElementById('previous-responses');
        if (container) {
            container.innerHTML = '<div class="no-responses">Henüz önceki yanıt yok</div>';
        }
        
        // Tüm accordion'ları gizle
        this.hideAllAccordions();
        
        // Local storage'ı temizle
        localStorage.removeItem('previousResponses');
        
        console.log('Yeni istek başlatıldı - tüm state temizlendi');
    }

    updatePreviousResponses() {
        const container = document.getElementById('previous-responses');
        if (!container) return;

        // Gradio app.py mantığı: history[1:] - ilk yanıt hariç diğerleri önceki yanıtlar
        if (this.previousResponses.length <= 1) {
            container.innerHTML = '<div class="no-responses">Henüz önceki yanıt yok</div>';
            // Tüm accordion'ları gizle
            this.hideAllAccordions();
            return;
        }

        // İlk yanıt hariç diğerlerini göster (Gradio app.py mantığı)
        const previousResponses = this.previousResponses.slice(1);
        
        // Başlık ekle (Gradio app.py'den)
        container.innerHTML = '<h3 style="font-family: \'Segoe UI\', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600; margin-bottom: 1rem;">📚 Önceki Yanıtlar</h3>';
        
        // Maksimum 4 önceki yanıt göster (Gradio app.py'den)
        const maxPrevious = Math.min(previousResponses.length, 4);
        
        for (let i = 0; i < maxPrevious; i++) {
            const response = previousResponses[i];
            const responseNumber = i + 1;
            const createdAt = new Date(response.created_at).toLocaleString('tr-TR');
            
            // Accordion'ı göster
            const accordion = document.getElementById(`prev-accordion-${responseNumber}`);
            if (accordion) {
                accordion.classList.remove('hidden');
                
                // Başlığı güncelle
                const title = accordion.querySelector('.accordion-title');
                if (title) {
                    title.textContent = `📄 Yanıt #${responseNumber} - ${createdAt}`;
                }
                
                // İçeriği güncelle
                const textarea = document.getElementById(`prev-text-${responseNumber}`);
                if (textarea) {
                    textarea.textContent = response.response_text;
                    textarea.onclick = () => {
                        textarea.style.border = '2px solid #3B82F6';
                        textarea.style.background = '#f0f9ff';
                        setTimeout(() => {
                            textarea.style.border = '';
                            textarea.style.background = '';
                        }, 2000);
                    };
                }
                
                // Copy butonunu güncelle
                const copyBtn = document.getElementById(`prev-copy-btn-${responseNumber}`);
                if (copyBtn) {
                    copyBtn.onclick = () => this.copyPreviousResponse(response.id);
                }
            }
        }
        
        // Kullanılmayan accordion'ları gizle
        for (let i = maxPrevious + 1; i <= 4; i++) {
            const accordion = document.getElementById(`prev-accordion-${i}`);
            if (accordion) {
                accordion.classList.add('hidden');
            }
        }
    }

    hideAllAccordions() {
        for (let i = 1; i <= 4; i++) {
            const accordion = document.getElementById(`prev-accordion-${i}`);
            if (accordion) {
                accordion.classList.add('hidden');
            }
        }
    }

    loadPreviousResponses() {
        const saved = localStorage.getItem('previousResponses');
        if (saved) {
            try {
                this.previousResponses = JSON.parse(saved);
                this.updatePreviousResponses();
            } catch (error) {
                console.error('Error loading previous responses:', error);
            }
        }
    }

    savePreviousResponses() {
        localStorage.setItem('previousResponses', JSON.stringify(this.previousResponses));
    }
}

// Event Manager
class EventManager {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Login events
        if (ui.elements.sendBtn) {
            ui.elements.sendBtn.addEventListener('click', () => authManager.sendCode());
        }
        
        if (ui.elements.verifyBtn) {
            ui.elements.verifyBtn.addEventListener('click', () => authManager.verifyCode());
        }
        
        if (ui.elements.emailInput) {
            ui.elements.emailInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    authManager.sendCode();
                }
            });
        }
        
        if (ui.elements.codeInput) {
            ui.elements.codeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    authManager.verifyCode();
                }
            });
        }
        
        // Profile events
        if (ui.elements.profileBtn) {
            ui.elements.profileBtn.addEventListener('click', () => authManager.completeProfile());
        }
        
        // Logout event
        if (ui.elements.logoutBtn) {
            ui.elements.logoutBtn.addEventListener('click', () => authManager.logout());
        }
        
        // AI Response events
        if (ui.elements.generateBtn) {
            ui.elements.generateBtn.addEventListener('click', () => responseManager.generateResponse());
        }
        
        if (ui.elements.mainCopyBtn) {
            ui.elements.mainCopyBtn.addEventListener('click', () => responseManager.copyResponse());
        }
        
        if (ui.elements.newRequestBtn) {
            ui.elements.newRequestBtn.addEventListener('click', () => responseManager.newRequest());
        }
        
        // Settings events
        if (ui.elements.temperature) {
            ui.elements.temperature.addEventListener('input', (e) => {
                if (ui.elements.temperatureValue) {
                    ui.elements.temperatureValue.textContent = e.target.value;
                }
            });
        }
        
        if (ui.elements.maxTokens) {
            ui.elements.maxTokens.addEventListener('input', (e) => {
                if (ui.elements.maxTokensValue) {
                    ui.elements.maxTokensValue.textContent = e.target.value;
                }
            });
        }
    }
}

// Global functions

function showCopySuccess(textarea) {
    const originalBorder = textarea.style.border;
    const originalBackground = textarea.style.background;
    textarea.style.border = '2px solid #3B82F6';
    textarea.style.background = '#f0f9ff';
    
    // Geçici mesaj göster
    const parent = textarea.parentElement;
    const successMsg = document.createElement('div');
    successMsg.innerHTML = '<p style="color: #3B82F6; font-weight: bold; margin: 5px 0;">✅ Kopyalandı!</p>';
    parent.appendChild(successMsg);
    
    setTimeout(() => {
        textarea.style.border = originalBorder;
        textarea.style.background = originalBackground;
        if (parent.contains(successMsg)) {
            parent.removeChild(successMsg);
        }
    }, 2000);
}

function toggleAdminPanel() {
    const content = document.querySelector('#admin-panel .accordion-content');
    if (content) {
        content.classList.toggle('open');
    }
}

function toggleAccordion(id) {
    const element = document.getElementById(id);
    if (element) {
        element.classList.toggle('hidden');
    }
}

function toggleSettings() {
    const content = document.querySelector('#response-settings .accordion-content');
    if (content) {
        content.classList.toggle('open');
    }
}

// Initialize global state
const appState = new AppState();
const api = new APIClient();
const authManager = new AuthManager();
const responseManager = new AIResponseManager();
const ui = new UIManager();
const eventManager = new EventManager();


// Start application when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('Application starting...');
        
        // Check for auto_login parameter
        const urlParams = new URLSearchParams(window.location.search);
        const autoLogin = urlParams.get('auto_login');
        
        if (autoLogin === 'true') {
            console.log('Auto login detected, checking backend session...');
            await authManager.checkBackendSession();
        } else {
            await authManager.init();
        }
        
        console.log('Application started successfully');
    } catch (error) {
        console.error('Application startup error:', error);
        ui.showError('login-error', 'Uygulama başlatılırken hata oluştu.');
    }
});

// Export for global access
window.authManager = authManager;
window.responseManager = responseManager;
window.toggleAdminPanel = toggleAdminPanel;
window.toggleAccordion = toggleAccordion;
