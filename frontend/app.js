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

        // Debug logging for token
        const hasToken = defaultOptions.headers['Authorization'] || options.headers?.['Authorization'];
        console.log('API Request:', {
            method: options.method || 'GET',
            url,
            hasToken: !!hasToken,
            tokenLength: hasToken ? hasToken.length : 0
        });

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

    async verifyMagicToken(token) {
        return this.request('/auth/verify-magic-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token: token })
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

    async completeProfile(profileData) {
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        console.log('APIClient.completeProfile called:', {
            hasToken: !!token,
            tokenLength: token ? token.length : 0,
            profileData
        });
        
        return this.request('/complete-profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(profileData)
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

    async logout() {
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        return this.request('/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
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
        } else {
            // Authentication yoksa loading screen'i gizle ve login göster
            ui.hideLoadingScreen();
            ui.showLogin();
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
            console.log('=== checkBackendSession START ===');
            
            // Magic link ile geliyorsa (auto_login=true veya token parametresi varsa) çıkış flag'ini kontrol etme
            const urlParams = new URLSearchParams(window.location.search);
            const isMagicLink = urlParams.get('auto_login') === 'true' || urlParams.get('token');
            console.log('URL params:', window.location.search);
            console.log('isMagicLink:', isMagicLink);
            
            // Magic link ile geldiyse çıkış flag'ini temizle ve doğrudan giriş yap
            if (isMagicLink) {
                console.log('Magic link detected, clearing logout flag and forcing login');
                localStorage.removeItem('user_logged_out');
                
                // URL'den magic link parametrelerini temizle
                const url = new URL(window.location);
                url.searchParams.delete('auto_login');
                url.searchParams.delete('token');
                window.history.replaceState({}, document.title, url.pathname + url.search);
                
                // Magic link token'ını backend'e gönder ve kullanıcı bilgilerini al
                const token = urlParams.get('token');
                if (token) {
                    console.log('Magic link token found, verifying with backend...');
                    try {
                        const response = await this.api.verifyMagicToken(token);
                        if (response && response.access_token) {
                            console.log('Magic link verification successful:', response);
                            
                            // Authentication state'i güncelle - Field name consistency
                            this.appState.authenticated = true;
                            this.appState.userEmail = response.email;
                            this.appState.isAdmin = response.is_admin || false;
                            this.appState.accessToken = response.access_token; // ✅ accessToken field
                            this.appState.authToken = response.access_token; // ✅ authToken field (backward compatibility)
                            this.appState.userProfile = {
                                email: response.email,
                                full_name: response.full_name || '',
                                department: response.department || '',
                                profile_completed: response.profile_completed || false
                            };
                            
                            console.log('Authentication state set:', {
                                authenticated: this.appState.authenticated,
                                accessToken: this.appState.accessToken ? 'present' : 'missing',
                                authToken: this.appState.authToken ? 'present' : 'missing',
                                userEmail: this.appState.userEmail,
                                profileCompleted: this.appState.userProfile.profile_completed,
                                tokenValue: this.appState.accessToken ? this.appState.accessToken.substring(0, 20) + '...' : 'null'
                            });
                            
                            // Local storage'a kaydet
                            this.saveToStorage();
                            
                            // Profil tamamlama kontrolü
                            if (!response.profile_completed || !response.full_name || !response.department) {
                                console.log('Profil tamamlanmamış, profil sayfasına yönlendiriliyor');
                                ui.showProfileCompletion();
                            } else {
                                console.log('Profil tamamlanmış, ana sayfaya yönlendiriliyor');
                                ui.showMainApp();
                                if (this.appState.isAdmin) {
                                    await responseManager.loadAdminStats();
                                }
                            }
                            
                            console.log('=== checkBackendSession SUCCESS (Magic Link) ===');
                            return true;
                        }
                    } catch (error) {
                        console.error('Magic link verification failed:', error);
                        // Magic link başarısızsa normal login'e yönlendir
                        ui.hideLoadingScreen();
                        ui.showLogin();
                        return false;
                    }
                }
                
                // Fallback: GELİŞTİRME MODU (token yoksa)
                console.log('Magic link mode: bypassing authentication check');
                this.appState.authenticated = true;
                this.appState.userEmail = 'enginakyildiz@nilufer.bel.tr';
                this.appState.isAdmin = false;
                this.appState.userProfile = {
                    email: 'enginakyildiz@nilufer.bel.tr',
                    full_name: '',
                    department: '',
                    profile_completed: false
                };
                
                // Local storage'a kaydet
                this.saveToStorage();
                
                // Profil tamamlanmamışsa profil sayfasını göster
                console.log('Magic link: showing profile page');
                ui.hideLoadingScreen();
                ui.showProfileCompletion();
                return true;
            }
            
            // Önce session'ı kontrol et
            console.log('Checking session status...');
            const sessionStatus = await this.api.getSessionStatus();
            console.log('Session status:', sessionStatus);
            const hasActiveSession = sessionStatus.sessions && sessionStatus.sessions.length > 0;
            console.log('hasActiveSession:', hasActiveSession);
            
            // Çıkış yapıldıysa ve magic link değilse auto login'i engelle
            if (!isMagicLink && localStorage.getItem('user_logged_out') === 'true') {
                console.log('User logged out, auto login disabled');
                await this.init();
                return;
            }
            
            if (sessionStatus.sessions && sessionStatus.sessions.length > 0) {
                const latestSession = sessionStatus.sessions[0];
                console.log('Latest session:', latestSession);
                const sessionDetails = await this.api.getSessionDetails(latestSession.session_id);
                console.log('Session details:', sessionDetails);
                
                if (sessionDetails.user_email) {
                    console.log('Backend session found:', sessionDetails.user_email);
                    
                    // Update app state
                    this.appState.authenticated = true;
                    this.appState.userEmail = sessionDetails.user_email;
                    this.appState.isAdmin = sessionDetails.is_admin || false;
                    this.appState.authToken = sessionDetails.access_token;
                    
                    // Save to localStorage
                    this.saveToStorage();
                    
                    // Çıkış flag'ini temizle (başarılı giriş)
                    localStorage.removeItem('user_logged_out');
                    
                    // Kullanıcı profil bilgilerini güncelle
                    await this.updateUserProfile();
                    
                    // Show main app
                    console.log('About to show main app. AppState:', this.appState);
                    ui.showMainApp();
                    console.log('Main app shown successfully');
                    
                    // Load admin stats if admin
                    if (this.appState.isAdmin) {
                        await responseManager.loadAdminStats();
                    }
                    
                    console.log('=== checkBackendSession SUCCESS ===');
                    return true;
                }
            }
            
            console.log('No backend session found');
            console.log('=== checkBackendSession FAILED ===');
            // Backend session yoksa loading screen'i gizle ve login göster
            ui.hideLoadingScreen();
            ui.showLogin();
            return false;
        } catch (error) {
            console.error('Backend session check failed:', error);
            console.log('=== checkBackendSession ERROR ===');
            // Hata durumunda loading screen'i gizle ve login göster
            ui.hideLoadingScreen();
            ui.showLogin();
            return false;
        }
    }
    
    async updateUserProfile() {
        try {
            console.log('Kullanıcı profil bilgileri güncelleniyor...');
            
            const response = await this.api.getProfile();
            if (response) {
                const fullName = response.full_name || 'İsimsiz';
                const department = response.department || 'Departman Belirtilmemiş';
                
                // Kullanıcı profil elementini güncelle
                const userProfileElement = document.getElementById('user-profile');
                if (userProfileElement) {
                    userProfileElement.textContent = `👤 ${fullName} - ${department}`;
                }
                
                console.log(`Kullanıcı profil güncellendi: ${fullName} - ${department}`);
            }
        } catch (error) {
            console.error('Kullanıcı profil güncelleme hatası:', error);
            // Hata durumunda varsayılan değer göster
            const userProfileElement = document.getElementById('user-profile');
            if (userProfileElement) {
                userProfileElement.textContent = '👤 Kullanıcı';
            }
        }
    }

    async sendCode(email) {
        try {
            // Spinner'ı göster
            this.showSpinner('send');
            
            const response = await this.api.sendLoginCode(email);
            
            // Başarılı olursa kod girişi ekranını göster
            if (response) {
                ui.showCodeInput(email);
            }
            
            return response;
        } catch (error) {
            console.error('Send code error:', error);
            
            // E-posta domain hatası için özel mesaj
            if (error.message.includes('400')) {
                this.showErrorMessage('❌ Sadece @nilufer.bel.tr e-posta adresleri kullanılabilir!');
            } else {
                this.showErrorMessage('❌ E-posta gönderilirken hata oluştu. Lütfen tekrar deneyin.');
            }
            
            // Spinner'ı gizle
            this.hideSpinner('send');
            
            throw error;
        }
    }

    async verifyCode(email, code) {
        try {
            // Spinner'ı göster
            this.showSpinner('verify');
            
            console.log('Kod doğrulama başlatılıyor:', {
                email: email,
                code: code
            });
            
            const response = await this.api.verifyCode(email, code);
            
            if (response.access_token) {
                console.log('Kod doğrulama başarılı:', response);
                
                // KRITIK: Authentication state'i tam olarak güncelle
                this.appState.authenticated = true;
                this.appState.userEmail = response.email || email;
                this.appState.isAdmin = response.is_admin || false;
                this.appState.authToken = response.access_token;
                this.appState.userProfile = {
                    email: response.email || email,
                    full_name: response.full_name || '',
                    department: response.department || '',
                    profile_completed: response.profile_completed || false
                };
                
                console.log('Authentication state güncellendi:', {
                    authenticated: this.appState.authenticated,
                    userEmail: this.appState.userEmail,
                    profileCompleted: this.appState.userProfile.profile_completed
                });
                
                // Session'ı localStorage'a kaydet
                this.saveToStorage();
                
                // Çıkış flag'ini temizle (başarılı giriş)
                localStorage.removeItem('user_logged_out');
                
                // Kod ekranını gizle
                const codeScreen = document.getElementById('code-screen');
                if (codeScreen) {
                    codeScreen.classList.add('hidden');
                }
                
                // Profil tamamlama kontrolü
                if (!response.profile_completed || !response.full_name || !response.department) {
                    console.log('Profil tamamlanmamış, profil sayfasına yönlendiriliyor');
                    ui.showProfileCompletion();
                } else {
                    console.log('Profil tamamlanmış, ana sayfaya yönlendiriliyor');
                    // Kullanıcı profil bilgilerini güncelle
                    await this.updateUserProfile();
                    ui.showMainApp();
                    if (this.appState.isAdmin) {
                        await responseManager.loadAdminStats();
                    }
                }
                
                return true;
            }
            return false;
        } catch (error) {
            console.error('Verify code error:', error);
            throw error;
        } finally {
            // Spinner'ı gizle
            this.hideSpinner('verify');
        }
    }

    hideSpinner(type) {
        const textElement = document.getElementById(`${type}-text`);
        const spinnerElement = document.getElementById(`${type}-spinner`);
        
        if (textElement) textElement.classList.remove('hidden');
        if (spinnerElement) spinnerElement.classList.add('hidden');
    }

    showSpinner(type) {
        const textElement = document.getElementById(`${type}-text`);
        const spinnerElement = document.getElementById(`${type}-spinner`);
        
        if (textElement) textElement.classList.add('hidden');
        if (spinnerElement) spinnerElement.classList.remove('hidden');
    }

    showErrorMessage(message) {
        // Mevcut hata mesajını temizle
        this.hideErrorMessage();
        
        // Yeni hata mesajı oluştur
        const errorDiv = document.createElement('div');
        errorDiv.id = 'error-message';
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        // E-posta input'unun altına ekle
        const emailInput = document.getElementById('email-input');
        if (emailInput && emailInput.parentNode) {
            emailInput.parentNode.insertBefore(errorDiv, emailInput.nextSibling);
        }
        
        // 5 saniye sonra otomatik gizle
        setTimeout(() => {
            this.hideErrorMessage();
        }, 5000);
    }

    hideErrorMessage() {
        const errorDiv = document.getElementById('error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    async copyPreviousResponse(responseId) {
        // Gradio app.py mantığı: önceki yanıtı kopyala ve seç
        const response = this.previousResponses.find(r => r.id === responseId);
        if (!response) {
            console.error('Yanıt bulunamadı:', responseId);
            return;
        }

        // Durum makinesi kontrolü - eğer zaten kopyalanmışsa hiçbir şey yapma
        if (this.state === 'finalized') {
            console.log('Already copied, ignoring');
            return;
        }

        // Durum makinesini güncelle (Gradio app.py mantığı)
        this.state = 'finalized';
        this.yanitSayisi += 1; // Yanıt sayısını artır

        // Response'u kopyalandı olarak işaretle
        const result = await this.markResponseAsCopied(responseId);
        if (result) {
            // Feedback'i güncelle
            await this.updateResponseFeedback(responseId, true, true);
            console.log('✅ Response kopyalandı olarak işaretlendi');
        } else {
            console.log('⚠️ Response işaretlenemedi, sadece panoya kopyalandı');
        }

        // Gradio app.py mantığı: Seçilen yanıtı ana yanıt yap
        // Seçilen yanıtı history'den çıkar (Gradio app.py satır 1290)
        this.previousResponses = this.previousResponses.filter(resp => resp.id !== responseId);
        
        // Seçilen yanıtı history'nin başına ekle (ana yanıt olarak) - Gradio app.py mantığı
        this.previousResponses.unshift(response);
        
        // Current response ID'yi güncelle (artık seçilen yanıt ana yanıt)
        this.currentResponseId = response.id;

        // Panoya kopyala
        navigator.clipboard.writeText(response.response_text).then(() => {
            console.log('✅ Önceki yanıt panoya kopyalandı!');
            
            // Ana yanıtı göster (seçilen yanıt)
            this.displayResponse(response.response_text);
            
            // Tüm akordiyonları gizle (seçilen yanıt ana alana gittiği için) - Gradio app.py satır 1313
            this.hideAllAccordions();
            this.updatePreviousResponses();
            
            // Gradio app.py mantığı: Yeni istek öneri cevapla butonunu göster
            ui.showNewRequestButton();
            
            // Buton görünürlüğünü güncelle
            this.updateButtonVisibility();
            
            console.log('✅ Önceki yanıt response kopyalandı! Sayı arttı.');
        }).catch(err => {
            console.error('❌ Kopyalama hatası:', err);
        });
    }

    saveToStorage() {
        const token = this.appState.accessToken || this.appState.authToken;
        console.log('Saving to storage:', {
            accessToken: this.appState.accessToken ? 'present' : 'missing',
            authToken: this.appState.authToken ? 'present' : 'missing',
            finalToken: token ? 'present' : 'missing',
            userEmail: this.appState.userEmail,
            tokenValue: token ? token.substring(0, 20) + '...' : 'null',
            appStateKeys: Object.keys(this.appState)
        });
        
        if (!token) {
            console.error('❌ CRITICAL: No token to save!', {
                accessToken: this.appState.accessToken,
                authToken: this.appState.authToken,
                appState: this.appState
            });
            return;
        }
        
        // ✅ Consistent localStorage key naming
        localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, token);
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER_EMAIL, this.appState.userEmail);
        localStorage.setItem(CONFIG.STORAGE_KEYS.IS_ADMIN, this.appState.isAdmin.toString());
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER_PROFILE, JSON.stringify(this.appState.userProfile));
        
        console.log('localStorage after save:', {
            authToken: localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN) ? 'saved' : 'missing',
            userEmail: localStorage.getItem(CONFIG.STORAGE_KEYS.USER_EMAIL),
            savedTokenValue: localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN) ? localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN).substring(0, 20) + '...' : 'null'
        });
    }

    // Authentication state kontrolü için helper fonksiyon
    checkAuthenticationState() {
        const state = {
            authenticated: this.appState.authenticated,
            userEmail: this.appState.userEmail,
            accessToken: this.appState.accessToken ? 'present' : 'missing',
            authToken: this.appState.authToken ? 'present' : 'missing',
            profileCompleted: this.appState.userProfile?.profile_completed
        };
        
        console.log('Current authentication state:', state);
        
        const isValid = this.appState.authenticated && 
                       this.appState.userEmail && 
                       (this.appState.accessToken || this.appState.authToken);
        
        console.log('checkAuthenticationState validation:', {
            authenticated: this.appState.authenticated,
            hasUserEmail: !!this.appState.userEmail,
            hasAccessToken: !!this.appState.accessToken,
            hasAuthToken: !!this.appState.authToken,
            isValid: isValid
        });
        
        if (!isValid) {
            console.error('Authentication state validation failed:', {
                authenticated: this.appState.authenticated,
                hasUserEmail: !!this.appState.userEmail,
                hasAccessToken: !!this.appState.accessToken,
                hasAuthToken: !!this.appState.authToken
            });
        }
        
        return isValid;
    }

    // Debug için comprehensive logging
    debugAuthState() {
        console.log('=== FULL AUTH STATE DEBUG ===');
        console.log('appState:', JSON.stringify(this.appState, null, 2));
        console.log('localStorage items:', {
            authenticated: localStorage.getItem('authenticated'),
            authToken: localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN) ? 'present' : 'missing',
            userEmail: localStorage.getItem(CONFIG.STORAGE_KEYS.USER_EMAIL),
            isAdmin: localStorage.getItem(CONFIG.STORAGE_KEYS.IS_ADMIN),
            userProfile: localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE) ? 'present' : 'missing'
        });
        console.log('checkAuthenticationState():', this.checkAuthenticationState());
        console.log('=============================');
    }

    async completeProfile() {
        try {
            console.log('=== PROFILE COMPLETION START ===');
            this.debugAuthState();
            
            // Authentication state kontrolü
            if (!this.checkAuthenticationState()) {
                console.error('AUTHENTICATION FAILED - Cannot complete profile');
                this.showErrorMessage('❌ Kimlik doğrulama hatası. Lütfen yeniden giriş yapın.');
                ui.showLogin();
                return;
            }
            
            // Form verilerini al
            const fullNameInput = document.getElementById('profile-name');
            const departmentSelect = document.getElementById('profile-department');
            
            if (!fullNameInput || !departmentSelect) {
                console.error('Profil form elementleri bulunamadı');
                this.showErrorMessage('❌ Form elementleri bulunamadı. Sayfayı yenileyin.');
                return;
            }
            
            const fullName = fullNameInput.value.trim();
            const department = departmentSelect.value;
            
            // Validasyon
            if (!fullName) {
                this.showErrorMessage('❌ Ad soyad alanı zorunludur.');
                return;
            }
            
            if (!department) {
                this.showErrorMessage('❌ Birim/Müdürlük seçimi zorunludur.');
                return;
            }
            
            // Spinner göster
            this.showSpinner('profile');
            
            console.log('Profil tamamlama isteği:', {
                email: this.appState.userEmail,
                fullName: fullName,
                department: department
            });
            
            // API'ye gönder - production backend email bekliyor
            const response = await this.api.completeProfile({
                full_name: fullName,
                department: department,
                email: this.appState.userEmail
            });
            
            if (response) {
                console.log('Profil başarıyla tamamlandı');
                
                // App state'i güncelle
                this.appState.userProfile = {
                    ...this.appState.userProfile,
                    full_name: fullName,
                    department: department,
                    profile_completed: true
                };
                
                this.saveToStorage();
                
                // Kullanıcı profil elementini güncelle
                await this.updateUserProfile();
                
                // Ana uygulamayı göster
                ui.showMainApp();
                
                // Admin ise istatistikleri yükle
                if (this.appState.isAdmin) {
                    await responseManager.loadAdminStats();
                }
            }
            
        } catch (error) {
            console.error('Profil tamamlama hatası:', error);
            if (error.message.includes('401')) {
                this.showErrorMessage('❌ Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
                ui.showLogin();
            } else {
                this.showErrorMessage('❌ Profil güncellenirken hata oluştu. Lütfen tekrar deneyin.');
            }
        } finally {
            // Spinner'ı gizle
            this.hideSpinner('profile');
        }
    }

    async logout() {
        try {
            // Backend'e logout isteği gönder
            await this.api.logout();
        } catch (error) {
            console.error('Backend logout failed:', error);
        }
        
        this.appState.authenticated = false;
        this.appState.userEmail = null;
        this.appState.isAdmin = false;
        this.appState.userProfile = null;
        this.appState.authToken = null;
        
        // Clear localStorage
        Object.values(CONFIG.STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
        
        // Çıkış yapıldığını işaretle
        localStorage.setItem('user_logged_out', 'true');
        
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

    showCodeInput(email) {
        this.hideAllScreens();
        
        // E-posta input'unu gizle
        const emailInput = document.getElementById('email-input');
        const sendBtn = document.getElementById('send-btn');
        const emailInstruction = document.querySelector('.email-instruction');
        
        if (emailInput) emailInput.style.display = 'none';
        if (sendBtn) sendBtn.style.display = 'none';
        if (emailInstruction) emailInstruction.style.display = 'none';
        
        // Kod girişi ekranını göster
        const codeScreen = document.getElementById('code-screen');
        const codeInput = document.getElementById('code-input');
        const verifyBtn = document.getElementById('verify-btn');
        
        if (codeScreen) {
            codeScreen.classList.remove('hidden');
        }
        if (codeInput) {
            codeInput.focus();
        }
        if (verifyBtn) {
            verifyBtn.style.display = 'block';
        }
        
        // E-posta bilgisini göster
        const emailInfo = document.querySelector('.email-info');
        if (emailInfo) {
            emailInfo.textContent = `E-posta gönderildi: ${email}`;
            emailInfo.style.display = 'block';
        }
    }

    showMainApp() {
        console.log('=== showMainApp START ===');
        console.log('Elements:', this.elements);
        console.log('mainScreen element:', this.elements.mainScreen);
        
        this.hideAllScreens();
        console.log('After hideAllScreens - mainScreen classes:', this.elements.mainScreen.classList.toString());
        
        this.hideLoadingScreen();
        console.log('After hideLoadingScreen');
        
        this.elements.mainScreen.classList.remove('hidden');
        console.log('After removing hidden - mainScreen classes:', this.elements.mainScreen.classList.toString());
        
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
            document.body.classList.add('admin-user'); // Admin için body'ye class ekle
        } else {
            document.body.classList.remove('admin-user'); // Admin değilse class'ı kaldır
        }
        
        console.log('=== showMainApp END ===');
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

    showNewRequestButton() {
        // Gradio app.py mantığı: Yeni istek öneri cevapla butonunu göster
        const newRequestBtn = document.getElementById('new-request-btn');
        if (newRequestBtn) {
            newRequestBtn.style.display = 'block';
            console.log('✅ Yeni istek öneri cevapla butonu gösterildi');
        }
    }

    showLoading() {
        const responseArea = document.getElementById('main-response');
        if (responseArea) {
            responseArea.innerHTML = `
                <div class="response-loading">
                    <div class="loading-text">İşlem yapılıyor...</div>
                </div>
            `;
        }
    }

    hideLoading() {
        // Loading'i gizlemek için response alanını temizle
        const responseArea = document.getElementById('main-response');
        if (responseArea && responseArea.querySelector('.response-loading')) {
            responseArea.innerHTML = 'Henüz yanıt üretilmedi...';
        }
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
        this.currentResponseId = null; // Ana yanıt için response ID
        this.state = 'draft'; // 'draft' or 'finalized'
        this.yanitSayisi = 0; // Yanıt sayısı (maksimum 5)
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
            if (this.yanitSayisi >= 5) {
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

                // Ana yanıt için response ID'yi set et
                this.currentResponseId = response.id;

                // Gradio app.py mantığı: history'ye başa ekle
                this.previousResponses.unshift(newResponse);
                
                // Yanıt sayısını artır (Gradio app.py'den)
                this.yanitSayisi += 1;
                
                // Ana yanıtı göster (en son üretilen)
                this.displayResponse(response.response_text);
                
                // Önceki yanıtları güncelle (history[1:] - ilk yanıt hariç)
                this.updatePreviousResponses();
                
                // Buton görünürlüğünü güncelle (Gradio app.py mantığı)
                this.updateButtonVisibility();
                
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

    async markResponseAsCopied(responseId) {
        // Gradio app.py mantığı: Response'u kopyalandı olarak işaretle
        try {
            const response = await fetch(`${CONFIG.BACKEND_URL}/responses/${responseId}/mark-copied`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN)}`,
                    'Content-Type': 'application/json'
                }
            });
            return response.ok;
        } catch (error) {
            console.error('Response kopyalandı olarak işaretlenemedi:', error);
            return false;
        }
    }

    async updateResponseFeedback(responseId, isSelected = false, copied = false) {
        // Gradio app.py mantığı: Response feedback'i güncelle
        try {
            const data = {
                response_id: responseId,
                is_selected: isSelected,
                copied: copied
            };
            const response = await fetch(`${CONFIG.BACKEND_URL}/responses/feedback`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN)}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            return response.ok;
        } catch (error) {
            console.error('Geri bildirim güncellenemedi:', error);
            return false;
        }
    }

    async copyResponse() {
        // Gradio app.py mantığı: Ana yanıtı kopyala
        if (ui.elements.mainResponse) {
            const text = ui.elements.mainResponse.textContent;
            
            // Durum makinesi kontrolü - eğer zaten kopyalanmışsa hiçbir şey yapma
            if (this.state === 'finalized') {
                console.log('Already copied, ignoring');
                return;
            }
            
            // Durum makinesini güncelle (Gradio app.py mantığı)
            this.state = 'finalized';
            this.yanitSayisi += 1; // Yanıt sayısını artır
            
            // Veritabanında response'u kopyalandı olarak işaretle
            if (this.currentResponseId) {
                // Response'u kopyalandı olarak işaretle
                const result = await this.markResponseAsCopied(this.currentResponseId);
                if (result) {
                    // Feedback'i güncelle
                    await this.updateResponseFeedback(this.currentResponseId, true, true);
                    console.log('✅ Response kopyalandı olarak işaretlendi');
                } else {
                    console.log('⚠️ Response işaretlenemedi, sadece panoya kopyalandı');
                }
            }
            
            navigator.clipboard.writeText(text).then(() => {
                console.log('✅ Ana yanıt panoya kopyalandı!');
                
                // Kullanıcı isteği: Ana seç ve kopyala ya basınca önceki yanıtların hepsi gizlenir
                this.hideAllAccordions();
                this.hidePreviousResponsesSection();
                this.updatePreviousResponses();
                
                // Ana "Seç ve Kopyala" düğmesini de gizle
                if (ui.elements.mainCopyBtn) {
                    ui.elements.mainCopyBtn.style.display = 'none';
                }
                
                // Buton görünürlüğünü güncelle
                this.updateButtonVisibility();
                
                // Show success feedback
                const btn = ui.elements.mainCopyBtn;
                const originalText = btn.textContent;
                btn.textContent = '✅ Kopyalandı!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
                
                console.log('✅ Ana yanıt response kopyalandı! Sayı arttı.');
            }).catch(err => {
                console.error('❌ Kopyalama hatası:', err);
                ui.showError('response-error', 'Kopyalama başarısız.');
            });
        }
    }

    hidePreviousResponsesSection() {
        // Önceki yanıtlar bölümünü gizle
        const previousResponsesSection = document.querySelector('.previous-responses');
        if (previousResponsesSection) {
            previousResponsesSection.style.display = 'none';
            console.log('✅ Önceki yanıtlar bölümü gizlendi');
        }
    }

    async copyPreviousResponse(responseId) {
        // Gradio app.py mantığı: önceki yanıtı kopyala ve seç
        const response = this.previousResponses.find(r => r.id === responseId);
        if (!response) {
            console.error('Yanıt bulunamadı:', responseId);
            return;
        }

        // Durum makinesi kontrolü - eğer zaten kopyalanmışsa hiçbir şey yapma
        if (this.state === 'finalized') {
            console.log('Already copied, ignoring');
            return;
        }

        // Durum makinesini güncelle (Gradio app.py mantığı)
        this.state = 'finalized';
        this.yanitSayisi += 1; // Yanıt sayısını artır

        // Response'u kopyalandı olarak işaretle
        const result = await this.markResponseAsCopied(responseId);
        if (result) {
            // Feedback'i güncelle
            await this.updateResponseFeedback(responseId, true, true);
            console.log('✅ Önceki yanıt kopyalandı olarak işaretlendi');
        } else {
            console.log('⚠️ Önceki yanıt işaretlenemedi, sadece panoya kopyalandı');
        }

        // Gradio app.py mantığı: Seçilen yanıtı ana yanıt alanına taşı
        // 1. Seçilen yanıtı history'den çıkar
        const selectedIndex = this.previousResponses.findIndex(r => r.id === responseId);
        if (selectedIndex !== -1) {
            const selectedResponse = this.previousResponses.splice(selectedIndex, 1)[0];
            
            // 2. Seçilen yanıtı history'nin başına ekle (ana yanıt olarak)
            this.previousResponses.unshift(selectedResponse);
            
            // 3. Ana yanıt alanını güncelle
            this.displayResponse(selectedResponse.response_text);
            
            // 4. Current response ID'yi güncelle
            this.currentResponseId = selectedResponse.id;
            
            // 5. Panoya kopyala
            navigator.clipboard.writeText(selectedResponse.response_text).then(() => {
                console.log('✅ Önceki yanıt panoya kopyalandı!');
                
                // 6. Önceki yanıtları güncelle (akordiyonları gizlemeden önce)
                this.updatePreviousResponses();
                
                // 7. Tüm akordiyonları gizle (Gradio app.py satır 1313 mantığı)
                this.hideAllAccordions();
                
                // 8. Ana "Seç ve Kopyala" düğmesini de gizle
                if (ui.elements.mainCopyBtn) {
                    ui.elements.mainCopyBtn.style.display = 'none';
                }
                
                // 9. "Yeni İstek Öneri Cevapla" butonunu göster
                ui.showNewRequestButton();
                
                // 10. Buton görünürlüğünü güncelle
                this.updateButtonVisibility();
                
                console.log('✅ Önceki yanıt ana alana taşındı ve kopyalandı!');
            }).catch(err => {
                console.error('❌ Kopyalama hatası:', err);
                ui.showError('response-error', 'Kopyalama başarısız.');
            });
        }
    }

    newRequest() {
        console.log('New request handler called - clearing state');
        
        // State'i temizle (Gradio app.py'den)
        this.previousResponses = [];
        this.currentRequestId = null;
        this.currentResponseId = null;
        this.state = 'draft';
        this.yanitSayisi = 0;
        
        // UI'yi temizle
        this.hideAllAccordions();
        this.updatePreviousResponses();
        this.updateButtonVisibility();
        
        // Ana "Seç ve Kopyala" düğmesini gizli tut (yanıt üretilmeden önce)
        if (ui.elements.mainCopyBtn) {
            ui.elements.mainCopyBtn.style.display = 'none';
        }
        
        // Input alanlarını varsayılan değerlerle doldur
        this.setDefaultTextboxValues();
        
        // Ana yanıt alanını temizle
        const mainResponse = document.getElementById('main-response');
        if (mainResponse) {
            mainResponse.innerHTML = 'Henüz yanıt üretilmedi...';
        }
        
        // Local storage'ı temizle
        localStorage.removeItem('previousResponses');
        
        console.log('New request - state cleared');
    }

    updatePreviousResponses() {
        const container = document.getElementById('previous-responses');
        if (!container) return;

        // "Önceki Yanıtlar" bölümünü tekrar göster (hideAllAccordions'dan sonra)
        container.style.display = 'block';

        // Gradio app.py mantığı: history[1:] - ilk yanıt hariç diğerleri önceki yanıtlar
        // Ana yanıt kopyalandığında da önceki yanıtları göster
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
                
                // İçeriği güncelle (Ana textbox gibi - kopyalanabilir değil)
                // div#prev-text-${responseNumber} div'ini kaldır, textarea'yı doğrudan accordion içeriğine yerleştir
                const accordionContent = accordion.querySelector('.accordion-content');
                if (accordionContent) {
                    accordionContent.innerHTML = `
                        <textarea class="response-textarea" readonly style="width: 100%; height: 300px; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; background: #ffffff; font-size: 14px; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word; overflow-y: auto; resize: vertical; margin: 0; display: block;">${response.response_text}</textarea>
                        <button id="prev-copy-btn-${responseNumber}" class="prev-copy-btn" style="margin-top: 10px; padding: 8px 16px; background: #4b9ac7; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; transition: background-color 0.3s ease;" onmouseover="this.style.background='#e25b6b'" onmouseout="this.style.background='#4b9ac7'">📋 Seç ve Kopyala #${responseNumber}</button>
                    `;
                    
                    // Copy butonunu güncelle
                    const copyBtn = document.getElementById(`prev-copy-btn-${responseNumber}`);
                    if (copyBtn) {
                        copyBtn.onclick = async () => {
                            await responseManager.copyPreviousResponse(response.id);
                        };
                    }
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
        // Tüm akordiyonları gizle
        for (let i = 1; i <= 4; i++) {
            const accordion = document.getElementById(`prev-accordion-${i}`);
            if (accordion) {
                accordion.classList.add('hidden');
            }
        }
        
        // "Önceki Yanıtlar" bölümünün kendisini de gizle
        const previousResponsesContainer = document.getElementById('previous-responses');
        if (previousResponsesContainer) {
            previousResponsesContainer.style.display = 'none';
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

    // Gradio app.py mantığı: Buton görünürlüğünü güncelle
    updateButtonVisibility() {
        const generateBtn = document.getElementById('generate-btn');
        const newRequestBtn = document.getElementById('new-request-btn');
        const mainCopyBtn = document.getElementById('main-copy-btn');
        
        if (generateBtn && newRequestBtn) {
            // Gradio app.py mantığı:
            // generate_visible = user_state['state'] == 'draft' and user_state['yanit_sayisi'] < 5
            // new_request_visible = user_state['state'] == 'finalized' or user_state['yanit_sayisi'] >= 5
            
            const generateVisible = this.state === 'draft' && this.yanitSayisi < 5;
            const newRequestVisible = this.state === 'finalized' || this.yanitSayisi >= 5;
            
            generateBtn.style.display = generateVisible ? 'block' : 'none';
            newRequestBtn.style.display = newRequestVisible ? 'block' : 'none';
            
            // Her zaman textbox'lara varsayılan değerleri doldur
            this.setDefaultTextboxValues();
            
            console.log(`Button visibility updated: generate=${generateVisible}, newRequest=${newRequestVisible}, state=${this.state}, yanitSayisi=${this.yanitSayisi}`);
        }
        
        // Ana "Seç ve Kopyala" düğmesini kontrol et
        if (mainCopyBtn) {
            // Yanıt üretilmeden önce düğmeyi gizle
            // Ama state 'finalized' ise düğmeyi gizle (kopyalandığında)
            const hasResponse = this.previousResponses.length > 0;
            const shouldHide = this.state === 'finalized';
            
            if (shouldHide) {
                mainCopyBtn.style.display = 'none';
            } else {
                mainCopyBtn.style.display = hasResponse ? 'block' : 'none';
            }
            
            console.log(`Main copy button visibility: ${shouldHide ? 'hidden (finalized)' : (hasResponse ? 'visible' : 'hidden')}, state=${this.state}, responses=${this.previousResponses.length}`);
        }
    }
    
    // Textbox'lara varsayılan değerleri doldur
    setDefaultTextboxValues() {
        const requestInput = document.getElementById('original-text');
        const responseInput = document.getElementById('custom-input');
        
        if (requestInput) {
            requestInput.value = 'Bursa Nilüfer\'de bir dükkanım var ve yönetim planından tahsisli otoparkımda bulunan dubaları, belediye ekipleri mafyavari şekilde tahsisli alanımdan alıp götürebiliyor. Geri aradığımda ise belediye zabıtası, görevliyi mahkemeye vermemi söylüyor. Bu nasıl bir hizmet anlayışı? Benim tahsisli alanımdan eşyamı alıyorsunuz, buna ne denir? Herkes biliyordur. Bir yeri koruduğunu zannedip başka bir yeri mağdur etmek mi belediyecilik?';
        }
        
        if (responseInput) {
            responseInput.value = 'Orası size tahsis edilmiş bir yer değil. Nilüfer halkının ortak kullanım alanı. Kaldırımlar da öyle.';
        }
        
        console.log('✅ Textbox\'lara varsayılan değerler dolduruldu');
    }
    
    async loadAdminStats() {
        try {
            console.log('Loading admin stats...');
            
            // Admin istatistiklerini yükle
            const usersResponse = await api.getUsers();
            const users = usersResponse.users;
            
            // İstatistikleri hesapla - Gradio app formatına göre
            let totalGeneratedResponses = 0;
            let totalAnsweredRequests = 0;
            
            for (const user of users) {
                totalGeneratedResponses += user.total_requests || 0;
                totalAnsweredRequests += user.answered_requests || 0;
            }
            
            // HTML'i oluştur - Gradio app formatına göre
            const statsHtml = `
                <div style="background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 4px 8px rgba(0,0,0,0.1);">
                    <div style="display: flex; gap: 2rem; margin-bottom: 2rem;">
                        <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px; text-align: center; flex: 1;">
                            <h4 style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Toplam Üretilen Yanıt</h4>
                            <div style="font-size: 2rem; font-weight: bold; color: #1976d2; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">${totalGeneratedResponses}</div>
                        </div>
                        <div style="background: #e8f5e8; padding: 1rem; border-radius: 8px; text-align: center; flex: 1;">
                            <h4 style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Toplam Cevaplanan İstek Öneri</h4>
                            <div style="font-size: 2rem; font-weight: bold; color: #2e7d32; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">${totalAnsweredRequests}</div>
                        </div>
                    </div>
                    
                    <h3 style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">👥 Kullanıcı Detayları</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
                        <thead>
                            <tr style="background: #f5f5f5;">
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: left; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Ad Soyad</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: left; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Müdürlük</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: left; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">E-posta</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Toplam Ürettiği Yanıt</th>
                                <th style="padding: 12px; border: 1px solid #ddd; text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 600;">Cevapladığı İstek Sayısı</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${users.map(user => `
                                <tr>
                                    <td style="padding: 12px; border: 1px solid #ddd; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">${user.full_name || 'N/A'}</td>
                                    <td style="padding: 12px; border: 1px solid #ddd; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">${user.department || 'N/A'}</td>
                                    <td style="padding: 12px; border: 1px solid #ddd; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">${user.email || 'N/A'}</td>
                                    <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">${user.total_requests || 0}</td>
                                    <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">${user.answered_requests || 0}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    
                </div>
            `;
            
            // İstatistikleri göster
            const content = document.getElementById('admin-stats-content');
            if (content) {
                content.innerHTML = statsHtml;
            }
            
            console.log('Admin stats loaded successfully');
        } catch (error) {
            console.error('Admin stats loading error:', error);
            const content = document.getElementById('admin-stats-content');
            if (content) {
                content.innerHTML = '<div class="error">İstatistikler yüklenirken hata oluştu.</div>';
            }
        }
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
            ui.elements.sendBtn.addEventListener('click', () => {
                const email = ui.elements.emailInput.value;
                authManager.sendCode(email);
            });
        }
        
        if (ui.elements.verifyBtn) {
            ui.elements.verifyBtn.addEventListener('click', () => {
                const email = ui.elements.emailInput.value;
                const code = ui.elements.codeInput.value;
                authManager.verifyCode(email, code);
            });
        }
        
        if (ui.elements.emailInput) {
            ui.elements.emailInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const email = ui.elements.emailInput.value;
                    authManager.sendCode(email);
                }
            });
        }
        
        if (ui.elements.codeInput) {
            ui.elements.codeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const email = ui.elements.emailInput.value;
                    const code = ui.elements.codeInput.value;
                    authManager.verifyCode(email, code);
                }
            });
        }
        
        // Profile events
        if (ui.elements.saveProfileBtn) {
            ui.elements.saveProfileBtn.addEventListener('click', () => authManager.completeProfile());
        }
        
        // Logout event
        if (ui.elements.logoutBtn) {
            ui.elements.logoutBtn.addEventListener('click', async () => await authManager.logout());
        }
        
        // AI Response events
        if (ui.elements.generateBtn) {
            ui.elements.generateBtn.addEventListener('click', () => responseManager.generateResponse());
        }
        
        if (ui.elements.mainCopyBtn) {
            ui.elements.mainCopyBtn.addEventListener('click', async () => await responseManager.copyResponse());
        }
        
        if (ui.elements.newRequestBtn) {
            ui.elements.newRequestBtn.addEventListener('click', () => responseManager.newRequest());
        }
        
        // Admin refresh event
        const refreshAdminBtn = document.getElementById('refresh-admin-btn');
        if (refreshAdminBtn) {
            refreshAdminBtn.addEventListener('click', async () => {
                console.log('Admin stats refresh requested');
                try {
                    // Loading göster
                    const content = document.getElementById('admin-stats-content');
                    if (content) {
                        content.innerHTML = '<div class="loading">İstatistikler yenileniyor...</div>';
                    }
                    
                    // İstatistikleri yeniden yükle
                    await responseManager.loadAdminStats();
                    
                    console.log('Admin stats refreshed successfully');
                } catch (error) {
                    console.error('Admin stats refresh error:', error);
                    const content = document.getElementById('admin-stats-content');
                    if (content) {
                        content.innerHTML = '<div class="error">İstatistikler yüklenirken hata oluştu.</div>';
                    }
                }
            });
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

function toggleAccordion(contentId) {
    const content = document.getElementById(contentId);
    const accordion = content.closest('.previous-accordion');
    const icon = accordion.querySelector('.accordion-icon');
    
    if (content) {
        content.classList.toggle('hidden');
        
        // İkonu güncelle
        if (icon) {
            if (content.classList.contains('hidden')) {
                icon.textContent = '▼';
            } else {
                icon.textContent = '▲';
            }
        }
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
        
        // Sayfa yüklendiğinde state'i sıfırla (Gradio app.py mantığı)
        responseManager.previousResponses = [];
        responseManager.currentRequestId = null;
        responseManager.currentResponseId = null;
        responseManager.state = 'draft';
        responseManager.yanitSayisi = 0;
        
        // UI'yi temizle
        responseManager.hideAllAccordions();
        responseManager.updatePreviousResponses();
        responseManager.updateButtonVisibility();
        
        // Ana "Seç ve Kopyala" düğmesini göster
        if (ui.elements.mainCopyBtn) {
            ui.elements.mainCopyBtn.style.display = 'block';
        }
        
        // Ana yanıt alanını temizle
        const mainResponse = document.getElementById('main-response');
        if (mainResponse) {
            mainResponse.innerHTML = 'Henüz yanıt üretilmedi...';
        }
        
        // Local storage'ı temizle
        localStorage.removeItem('previousResponses');
        
        console.log('Page loaded - state reset to initial state');
        
        // Check for auto_login parameter veya magic link parametreleri
        const urlParams = new URLSearchParams(window.location.search);
        const autoLogin = urlParams.get('auto_login');
        const sessionId = urlParams.get('session_id');
        const userEmail = urlParams.get('user_email');
        const isAdmin = urlParams.get('is_admin');
        const accessToken = urlParams.get('access_token');
        const magicToken = urlParams.get('token'); // Magic link token'ı
        
        // Magic link ile geliyorsa (token parametresi varsa) çıkış flag'ini kontrol etme
        const isMagicLink = autoLogin === 'true' || magicToken;
        
        if (autoLogin === 'true' || sessionId || userEmail || isAdmin || accessToken || magicToken) {
            console.log('Auto login or magic link detected, checking backend session...');
            await authManager.checkBackendSession();
        } else {
            await authManager.init();
        }
        
        // Buton görünürlüğünü başlangıçta güncelle
        responseManager.updateButtonVisibility();
        
        console.log('Application started successfully');
    } catch (error) {
        console.error('Application startup error:', error);
        ui.showError('login-error', 'Uygulama başlatılırken hata oluştu.');
    }
});

// Debug fonksiyonları
function debugAuthState() {
    console.log('=== AUTH STATE DEBUG ===');
    console.log('appState:', authManager.appState);
    console.log('localStorage auth:', localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN) ? 'present' : 'missing');
    console.log('localStorage email:', localStorage.getItem(CONFIG.STORAGE_KEYS.USER_EMAIL));
    console.log('localStorage profile:', localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE));
    console.log('========================');
}

// Debug için son request detayları
function debugLastRequest() {
    console.log('=== LAST REQUEST DEBUG ===');
    console.log('URL:', 'https://yardimci.niluferyapayzeka.tr/api/v1/complete-profile');
    console.log('Method:', 'POST');
    console.log('Expected Headers:', {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer [token]'
    });
    console.log('Expected Body:', {
        full_name: '[form value]',
        department: '[form value]'
    });
    console.log('========================');
}

// Test için manuel authentication set
function setTestAuth(email, token) {
    authManager.appState.authenticated = true;
    authManager.appState.userEmail = email;
    authManager.appState.authToken = token;
    authManager.appState.userProfile = {
        email: email,
        full_name: '',
        department: '',
        profile_completed: false
    };
    
    authManager.saveToStorage();
    
    console.log('Test authentication set for:', email);
    ui.showProfileCompletion();
}

// Export for global access
window.authManager = authManager;
window.responseManager = responseManager;
window.toggleAdminPanel = toggleAdminPanel;
window.toggleAccordion = toggleAccordion;
window.debugAuthState = debugAuthState;
window.debugLastRequest = debugLastRequest;
window.setTestAuth = setTestAuth;
