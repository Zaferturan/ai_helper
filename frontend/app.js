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
// Backend URL'i dinamik olarak belirle:
// - Production domain'inde ise PRODUCTION_URL kullan
// - localhost'ta ise localhost:12000 kullan
// - Network IP'de ise aynı hostname:12000 kullan
function getBackendURL() {
    const hostname = window.location.hostname;
    const PRODUCTION_URL = 'https://yardimci.niluferyapayzeka.tr';
    const PRODUCTION_URL_V2 = 'https://yardimci2.niluferyapayzeka.tr';
    
    // Production domain kontrolü (yardimci ve yardimci2)
    if (hostname === 'yardimci.niluferyapayzeka.tr' || hostname.includes('yardimci.niluferyapayzeka.tr')) {
        return `${PRODUCTION_URL}/api/v1`;
    }
    if (hostname === 'yardimci2.niluferyapayzeka.tr' || hostname.includes('yardimci2.niluferyapayzeka.tr')) {
        return `${PRODUCTION_URL_V2}/api/v1`;
    }
    
    // localhost kontrolü
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000/api/v1';
    }
    
    // Network IP veya diğer durumlar için aynı hostname'i kullan
    return `http://${hostname}:8000/api/v1`;
}

const CONFIG = {
    BACKEND_URL: getBackendURL(),
    PRODUCTION_URL: 'https://yardimci.niluferyapayzeka.tr',
    STORAGE_KEYS: {
        AUTH_TOKEN: 'auth_token',
        USER_EMAIL: 'user_email',
        IS_ADMIN: 'is_admin',
        USER_PROFILE: 'user_profile'
    }
};

// Template Save Manager for saving templates from response
class TemplateSaveManager {
    constructor() {
        this.categories = [];
        this.isNewCategoryMode = false;
    }

    async loadCategories() {
        try {
            const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
            const response = await fetch(`${CONFIG.BACKEND_URL}/categories`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.categories = data.categories || [];
            this.updateCategoryDropdown();
            
            return this.categories;
        } catch (error) {
            console.error('❌ Kategori yükleme hatası:', error);
            this.showToast('❌ Kategoriler yüklenirken hata oluştu', 'error');
            return [];
        }
    }

    updateCategoryDropdown() {
        const categorySelect = document.getElementById('template-category-select');
        if (!categorySelect) return;

        // Mevcut seçimi sakla
        const currentValue = categorySelect.value;
        
        // Seçenekleri temizle (ilk seçenek hariç)
        while (categorySelect.children.length > 1) {
            categorySelect.removeChild(categorySelect.lastChild);
        }

        // Kategorileri ekle
        this.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            // Admin tüm müdürlükleri görür; karışıklığı önlemek için departman adı da yazılsın
            option.textContent = category.department
                ? `${category.name} (${category.department})`
                : category.name;
            categorySelect.appendChild(option);
        });

        // Önceki seçimi geri yükle
        categorySelect.value = currentValue;
    }

    showTemplateSaveSection() {
        const saveSection = document.getElementById('save-template-section');
        const checkbox = document.getElementById('save-as-template');
        if (saveSection) {
            saveSection.style.display = 'block';
        }
        if (checkbox) {
            checkbox.style.display = 'block';
        }
    }

    hideTemplateSaveSection() {
        const saveSection = document.getElementById('save-template-section');
        const checkbox = document.getElementById('save-as-template');
        if (saveSection) {
            saveSection.style.display = 'none';
        }
        if (checkbox) {
            checkbox.style.display = 'none';
        }
        this.hideCategorySection();
    }

    showCategorySection() {
        const categorySection = document.getElementById('template-category-section');
        if (categorySection) {
            categorySection.classList.remove('hidden');
        }
    }

    hideCategorySection() {
        const categorySection = document.getElementById('template-category-section');
        if (categorySection) {
            categorySection.classList.add('hidden');
        }
    }

    showNewCategoryInput() {
        const inputGroup = document.getElementById('new-category-input-group');
        const newCategoryBtn = document.getElementById('new-category-btn');
        const categoryInput = document.getElementById('new-category-name');
        
        if (inputGroup) {
            inputGroup.classList.remove('hidden');
            this.isNewCategoryMode = true;
        }
        
        if (newCategoryBtn) {
            newCategoryBtn.classList.add('hidden');
        }
        
        if (categoryInput) {
            categoryInput.focus();
        }
    }

    hideNewCategoryInput() {
        const inputGroup = document.getElementById('new-category-input-group');
        const newCategoryBtn = document.getElementById('new-category-btn');
        const categoryInput = document.getElementById('new-category-name');
        
        if (inputGroup) {
            inputGroup.classList.add('hidden');
            this.isNewCategoryMode = false;
        }
        
        if (newCategoryBtn) {
            newCategoryBtn.classList.remove('hidden');
        }
        
        if (categoryInput) {
            categoryInput.value = '';
        }
    }

    async createCategory(categoryName) {
        try {
            const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
            console.log('Creating category with token:', token ? 'present' : 'missing');
            const response = await fetch(`${CONFIG.BACKEND_URL}/categories`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ name: categoryName })
            });

            if (!response.ok) {
                if (response.status === 403) {
                    this.showToast('⚠️ Bu işlem için yetkiniz yok', 'warning');
                    return null;
                } else if (response.status === 401) {
                    this.showToast('ℹ️ Oturum süreniz dolmuş, lütfen tekrar giriş yapın', 'info');
                    return null;
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
                }
            }

            const newCategory = await response.json();
            
            // Kategorileri yeniden yükle
            await this.loadCategories();
            
            // Yeni kategoriyi seç
            const categorySelect = document.getElementById('template-category-select');
            if (categorySelect) {
                categorySelect.value = newCategory.id;
            }
            
            this.hideNewCategoryInput();
            this.showToast('✅ Kategori eklendi', 'success');
            
            // Analitik tracking
            if (templatesManager) {
                templatesManager.trackEvent('category_created');
            }
            
            return newCategory;
        } catch (error) {
            console.error('❌ Kategori oluşturma hatası:', error);
            this.showToast(error.message || 'Kategori oluşturulurken hata oluştu', 'error');
            return null;
        }
    }

    async saveTemplate(content, categoryId, isSMS = false) {
        try {
            const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
            const response = await fetch(`${CONFIG.BACKEND_URL}/templates`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    content: content,
                    category_id: categoryId || null,
                    is_sms: isSMS
                })
            });

            if (!response.ok) {
                if (response.status === 403) {
                    this.showToast('⚠️ Bu işlem için yetkiniz yok', 'warning');
                    return null;
                } else if (response.status === 401) {
                    this.showToast('ℹ️ Oturum süreniz dolmuş, lütfen tekrar giriş yapın', 'info');
                    return null;
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
                }
            }

            const newTemplate = await response.json();
            this.showToast('✅ Şablon kaydedildi', 'success');
            
            // Analitik tracking
            if (templatesManager) {
                templatesManager.trackEvent('template_saved');
            }
            
            return newTemplate;
        } catch (error) {
            console.error('❌ Şablon kaydetme hatası:', error);
            this.showToast(error.message || 'Şablon kaydedilirken hata oluştu', 'error');
            return null;
        }
    }

    validateTemplateSave() {
        const saveCheckbox = document.getElementById('save-as-template');
        const categorySelect = document.getElementById('template-category-select');
        const responseContent = document.getElementById('main-response');
        const editor = document.getElementById('main-response-editor');
        
        if (!saveCheckbox || !saveCheckbox.checked) {
            return { valid: true }; // Şablon kaydetme istenmiyor
        }
        
        // Yanıt içeriği kontrolü (varsa textarea.value, yoksa container text)
        const contentText = editor ? (editor.value || '').trim() : ((responseContent?.textContent || '').trim());
        if (!contentText || contentText === 'Henüz yanıt üretilmedi...') {
            return { 
                valid: false, 
                message: 'Önce yanıt üretin' 
            };
        }
        
        // Kategori seçimi kontrolü
        if (!categorySelect || !categorySelect.value) {
            return { 
                valid: false, 
                message: 'Lütfen bir kategori seçin' 
            };
        }
        
        return { 
            valid: true, 
            content: contentText,
            categoryId: parseInt(categorySelect.value)
        };
    }

    resetTemplateSaveForm() {
        const saveCheckbox = document.getElementById('save-as-template');
        const categorySelect = document.getElementById('template-category-select');
        
        if (saveCheckbox) {
            saveCheckbox.checked = false;
        }
        
        if (categorySelect) {
            categorySelect.value = '';
        }
        
        this.hideCategorySection();
        this.hideNewCategoryInput();
    }

    // Toast notification system
    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icons[type] || icons.success}</span>
                <span class="toast-message">${this.escapeHtml(message)}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
        `;

        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('hiding');
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Setup event listeners
    setupEventListeners() {
        const saveCheckbox = document.getElementById('save-as-template');
        const newCategoryBtn = document.getElementById('new-category-btn');
        const createCategoryBtn = document.getElementById('create-category-btn');
        const cancelCategoryBtn = document.getElementById('cancel-category-btn');
        const categoryInput = document.getElementById('new-category-name');

        // Checkbox change event
        if (saveCheckbox) {
            saveCheckbox.addEventListener('change', () => {
                if (saveCheckbox.checked) {
                    this.showCategorySection();
                    this.loadCategories();
                } else {
                    this.hideCategorySection();
                    this.hideNewCategoryInput();
                }
            });
        }

        // New category button
        if (newCategoryBtn) {
            newCategoryBtn.addEventListener('click', () => {
                this.showNewCategoryInput();
            });
        }

        // Create category button
        if (createCategoryBtn) {
            createCategoryBtn.addEventListener('click', async () => {
                if (categoryInput && categoryInput.value.trim()) {
                    await this.createCategory(categoryInput.value.trim());
                }
            });
        }

        // Cancel category button
        if (cancelCategoryBtn) {
            cancelCategoryBtn.addEventListener('click', () => {
                this.hideNewCategoryInput();
            });
        }

        // Enter key in category input
        if (categoryInput) {
            categoryInput.addEventListener('keypress', async (e) => {
                if (e.key === 'Enter' && categoryInput.value.trim()) {
                    await this.createCategory(categoryInput.value.trim());
                }
            });
        }
    }
}

// Templates Manager for template operations
class TemplatesManager {
    constructor() {
        this.categories = [];
        this.templates = [];
        this.departments = [];
        this.currentFilters = {
            category_id: '',
            only_mine: false,
            is_sms: null, // SMS filtresi (null = tümü, true = sadece SMS, false = SMS değil)
            q: '',
            department: '' // Admin için departman filtresi
        };
        this.selectedTemplate = null;
        this.searchTimeout = null;
        this.isLoading = false;
        this.hasMore = false; // Tüm liste tek sayfa
        this.currentPage = 0;
        this.pageSize = 100; // Backend limitine uygun
        this.isProcessing = false; // Çift tıklama koruması
        
        // Basit analitik sistemi
        this.analytics = {
            template_saved: 0,
            template_used: 0,
            template_deleted: 0,
            category_created: 0,
            load_more_count: 0
        };
        
        this.loadAnalytics();
    }

    // Analitik yönetimi
    loadAnalytics() {
        const saved = localStorage.getItem('template_analytics');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                const today = new Date().toDateString();
                
                // Günlük reset kontrolü
                if (data.date !== today) {
                    this.analytics = {
                        template_saved: 0,
                        template_used: 0,
                        template_deleted: 0,
                        category_created: 0,
                        load_more_count: 0
                    };
                    this.saveAnalytics();
                } else {
                    this.analytics = data.analytics || this.analytics;
                }
            } catch (e) {
                console.error('Analytics load error:', e);
            }
        }
    }

    saveAnalytics() {
        const data = {
            date: new Date().toDateString(),
            analytics: this.analytics
        };
        localStorage.setItem('template_analytics', JSON.stringify(data));
    }

    trackEvent(event, data = {}) {
        switch(event) {
            case 'template_saved':
                this.analytics.template_saved++;
                break;
            case 'template_used':
                this.analytics.template_used++;
                break;
            case 'template_deleted':
                this.analytics.template_deleted++;
                break;
            case 'category_created':
                this.analytics.category_created++;
                break;
            case 'load_more':
                this.analytics.load_more_count++;
                break;
        }
        this.saveAnalytics();
        console.log(`📊 Analytics: ${event}`, data);
    }

    async loadCategories() {
        try {
            console.log('📂 Kategoriler yükleniyor...');
            const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
            const params = new URLSearchParams();
            
            // Admin ise departman filtresi ekle
            if (this.getCurrentUserAdminStatus() && this.currentFilters.department) {
                params.append('department', this.currentFilters.department);
            }
            
            const response = await fetch(`${CONFIG.BACKEND_URL}/categories?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 403) {
                    this.showToast('⚠️ Bu işlem için yetkiniz yok', 'warning');
                    return [];
                } else if (response.status === 401) {
                    this.showToast('ℹ️ Oturum süreniz dolmuş, lütfen tekrar giriş yapın', 'info');
                    return [];
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }

            const data = await response.json();
            this.categories = data.categories || [];
            
            console.log('✅ Kategoriler yüklendi:', this.categories.length);
            this.updateCategoryFilter();
            
            return this.categories;
        } catch (error) {
            console.error('❌ Kategori yükleme hatası:', error);
            this.showToast('❌ Kategoriler yüklenirken hata oluştu', 'error');
            return [];
        }
    }

    async loadTemplates(filters = {}, isLoadMore = false) {
        try {
            if (this.isLoading) return; // Prevent multiple simultaneous requests
            
            console.log('📋 Şablonlar yükleniyor...', filters, 'loadMore:', isLoadMore);
            
            if (!isLoadMore) {
                this.showLoading();
                this.currentPage = 0;
                this.templates = [];
            } else {
                this.showLoadMoreLoading();
            }
            
            this.isLoading = true;
            
            const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
            console.log('Loading templates with token:', token ? 'present' : 'missing');
            const params = new URLSearchParams();
            
            // Filtreleri ekle
            if (filters.q) params.append('q', filters.q);
            if (filters.category_id) params.append('category_id', filters.category_id);
            if (filters.only_mine) params.append('only_mine', 'true');
            if (filters.is_sms !== null && filters.is_sms !== undefined) params.append('is_sms', filters.is_sms.toString());
            if (filters.department) params.append('department', filters.department);
            params.append('limit', this.pageSize.toString());
            params.append('offset', (this.currentPage * this.pageSize).toString());

            const response = await fetch(`${CONFIG.BACKEND_URL}/templates?${params}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 403) {
                    this.showToast('⚠️ Bu işlem için yetkiniz yok', 'warning');
                    return [];
                } else if (response.status === 401) {
                    this.showToast('ℹ️ Oturum süreniz dolmuş, lütfen tekrar giriş yapın', 'info');
                    return [];
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }

            const data = await response.json();
            console.log('Backend response:', data);
            const newTemplates = data.templates || [];
            console.log('New templates:', newTemplates);
            
            if (isLoadMore) {
                this.templates = [...this.templates, ...newTemplates];
            } else {
                this.templates = newTemplates;
            }
            
            // Has more kontrolü
            this.hasMore = newTemplates.length === this.pageSize;
            this.currentPage++;
            
            // Load more analitik
            if (isLoadMore) {
                this.trackEvent('load_more');
            }
            
            console.log('✅ Şablonlar yüklendi:', this.templates.length, 'hasMore:', this.hasMore);
            this.updateTemplatesList();
            this.updateTemplatesCount();
            this.updateLoadMoreButton();
            
            return this.templates;
        } catch (error) {
            console.error('❌ Şablon yükleme hatası:', error);
            
            if (!isLoadMore) {
                this.showErrorState('Şablonlar yüklenirken hata oluştu');
            } else {
                this.showToast('❌ Şablonlar yüklenirken hata oluştu', 'error');
            }
            return [];
        } finally {
            this.isLoading = false;
        }
    }

    updateCategoryFilter() {
        const categorySelect = document.getElementById('category-filter');
        if (!categorySelect) return;

        // Mevcut seçimi sakla
        const currentValue = categorySelect.value;
        
        // Seçenekleri temizle (ilk seçenek hariç)
        while (categorySelect.children.length > 1) {
            categorySelect.removeChild(categorySelect.lastChild);
        }

        // Kategorileri ekle
        this.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.name;
            categorySelect.appendChild(option);
        });

        // Önceki seçimi geri yükle
        categorySelect.value = currentValue;
    }

    updateTemplatesList() {
        console.log('updateTemplatesList called, templates.length:', this.templates.length);
        const templatesList = document.getElementById('templates-list');
        const emptyState = document.getElementById('templates-empty-state');
        const categoriesEmptyState = document.getElementById('categories-empty-state');
        
        if (!templatesList) {
            console.log('templatesList element not found');
            return;
        }

        // Boş durumları gizle
        emptyState.classList.add('hidden');
        categoriesEmptyState.classList.add('hidden');

        // Önceki şablonları temizle
        templatesList.innerHTML = '';
        templatesList.classList.remove('hidden');

        if (this.templates.length === 0) {
            console.log('No templates, showing empty state');
            templatesList.classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }

        // Liste var: boş kartları gizle (değişken yeniden tanımlama yok)
        if (emptyState) emptyState.classList.add('hidden');
        const categoriesEmpty = document.getElementById('categories-empty-state');
        if (categoriesEmpty) categoriesEmpty.classList.add('hidden');

        // Performans optimizasyonu: DocumentFragment kullan
        const fragment = document.createDocumentFragment();
        this.templates.forEach(template => {
            const card = this.createTemplateCard(template);
            fragment.appendChild(card);
        });

        templatesList.appendChild(fragment);
        
        // Loading state'i gizle
        this.hideLoading();
        this.hideLoadMoreLoading();
    }

    createTemplateCard(template) {
        const card = document.createElement('div');
        card.className = 'template-card';
        card.dataset.templateId = template.id;

        const templateOwnerId = Number(template.owner_user_id);
        const currentUserId = this.getCurrentUserId();
        const userProfile = JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE) || 'null');
        const isAdmin = this.getCurrentUserAdminStatus();
        
        console.log('🔑 Template ID:', template.id);
        console.log('👤 Owner ID:', templateOwnerId, 'Type:', typeof templateOwnerId);
        console.log('👤 Current User ID:', currentUserId, 'Type:', typeof currentUserId);
        console.log('👑 Is Admin:', isAdmin);
        
        const isOwner = templateOwnerId === currentUserId;
        
        console.log('✅ Is Owner:', isOwner);
        console.log('👑 Is Admin:', isAdmin);
        console.log('→ Show Delete Button:', isOwner || isAdmin);

        const snippet = template.content ? this.escapeHtml(template.content).slice(0, 300) : '';
        // title attribute için özel escape: HTML entity'leri kullan ama tırnak işaretlerini düzelt
        const titleContent = template.content ? template.content.replace(/"/g, '&quot;').replace(/'/g, '&#39;') : '';
        // SMS etiketi (ID'nin altında)
        const smsLabel = template.is_sms ? '<div class="template-sms-label">SMS</div>' : '';
        
        card.innerHTML = `
            <div class="template-id-column">
                <div>ID: ${template.id}</div>
                ${smsLabel}
            </div>
            <div class="template-snippet" title="${titleContent}">${snippet}${template.content && template.content.length > 300 ? '...' : ''}</div>
            <div class="template-actions">
                <button class="btn btn-primary btn-sm copy-template-btn" data-template-id="${template.id}" aria-label="Şablonu kopyala">📄 Seç ve Kopyala</button>
                <button class="btn btn-secondary btn-sm edit-template-btn" data-template-id="${template.id}" aria-label="Şablonu düzenle">✏️ Düzenle</button>
                ${(isOwner || isAdmin) ? `<button class="btn btn-danger btn-sm delete-template-btn" data-template-id="${template.id}" aria-label="Şablonu sil">🗑️ Sil</button>` : ''}
            </div>
        `;

        return card;
    }

    updateTemplatesCount() {
        const countElement = document.getElementById('templates-count');
        if (countElement) {
            countElement.textContent = `Şablonlar (${this.templates.length})`;
        }
    }

    showLoading() {
        const loading = document.getElementById('templates-loading');
        const list = document.getElementById('templates-list');
        const emptyState = document.getElementById('templates-empty-state');
        const loadMoreBtn = document.getElementById('load-more-btn');
        
        if (loading) loading.classList.remove('hidden');
        if (list) list.classList.add('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        if (loadMoreBtn) loadMoreBtn.classList.add('hidden');
    }

    hideLoading() {
        const loading = document.getElementById('templates-loading');
        const list = document.getElementById('templates-list');
        const loadMoreBtn = document.getElementById('load-more-btn');
        
        if (loading) loading.classList.add('hidden');
        if (list) list.classList.remove('hidden');
        if (loadMoreBtn) loadMoreBtn.classList.remove('hidden');
    }

    showSkeletonLoading() {
        const list = document.getElementById('templates-list');
        if (!list) return;

        // Skeleton kartları oluştur
        const skeletonCards = Array.from({ length: 3 }, () => this.createSkeletonCard());
        
        list.innerHTML = '';
        skeletonCards.forEach(card => list.appendChild(card));
        list.classList.remove('hidden');
    }

    createSkeletonCard() {
        const card = document.createElement('div');
        card.className = 'skeleton-card';
        
        card.innerHTML = `
            <div class="skeleton-header">
                <div>
                    <div class="skeleton-title"></div>
                    <div class="skeleton-category"></div>
                </div>
                <div class="template-actions">
                    <div class="skeleton-title" style="width: 80px; height: 32px;"></div>
                    <div class="skeleton-title" style="width: 80px; height: 32px;"></div>
                </div>
            </div>
            <div class="skeleton-content"></div>
            <div class="skeleton-meta">
                <div class="skeleton-owner"></div>
                <div class="skeleton-date"></div>
            </div>
        `;
        
        return card;
    }

    showEmptyState() {
        const loading = document.getElementById('templates-loading');
        const list = document.getElementById('templates-list');
        const emptyState = document.getElementById('templates-empty-state');
        const loadMoreBtn = document.getElementById('load-more-btn');
        
        if (loading) loading.classList.add('hidden');
        if (list) list.classList.add('hidden');
        if (emptyState) {
            emptyState.classList.remove('hidden');
            
            // Boş durum mesajını güncelle
            const emptyTitle = emptyState.querySelector('h2');
            const emptyMessage = emptyState.querySelector('p');
            
            if (emptyTitle && emptyMessage) {
                // Filtre var mı kontrol et
                const hasFilters = this.currentFilters.q || 
                                 this.currentFilters.category_id || 
                                 this.currentFilters.only_mine || 
                                 this.currentFilters.department;
                
                if (hasFilters) {
                    emptyTitle.textContent = 'Sonuç bulunamadı';
                    emptyMessage.textContent = 'Bu filtrelerle eşleşen şablon bulunamadı. Filtreleri temizleyip tekrar deneyin.';
                } else {
                    emptyTitle.textContent = 'Henüz şablon yok';
                    emptyMessage.textContent = 'Üretim ekranında "Şablon olarak sakla" seçeneğiyle bir şablon ekleyebilirsiniz.';
                }
            }
        }
        if (loadMoreBtn) loadMoreBtn.classList.add('hidden');
    }

    showErrorState(message) {
        const loading = document.getElementById('templates-loading');
        const list = document.getElementById('templates-list');
        const emptyState = document.getElementById('templates-empty-state');
        const loadMoreBtn = document.getElementById('load-more-btn');
        
        if (loading) loading.classList.add('hidden');
        if (list) {
            list.classList.remove('hidden');
            list.innerHTML = `
                <div class="error-state">
                    <div class="error-icon">⚠️</div>
                    <h3>Bağlantı sorunu</h3>
                    <p>${message}</p>
                    <button class="btn btn-primary retry-btn" onclick="templatesManager.retryLastRequest()">
                        🔄 Tekrar Dene
                    </button>
                </div>
            `;
        }
        if (emptyState) emptyState.classList.add('hidden');
        if (loadMoreBtn) loadMoreBtn.classList.add('hidden');
    }

    retryLastRequest() {
        // Son isteği tekrarla
        this.loadTemplates(this.currentFilters);
    }

    showLoadMoreLoading() {
        const loadMoreBtn = document.getElementById('load-more-btn');
        const loadMoreSpinner = document.getElementById('load-more-spinner');
        
        if (loadMoreBtn) {
            loadMoreBtn.disabled = true;
            loadMoreBtn.innerHTML = '⏳ Yükleniyor...';
        }
        
        if (loadMoreSpinner) {
            loadMoreSpinner.classList.remove('hidden');
        }
    }

    hideLoadMoreLoading() {
        const loadMoreBtn = document.getElementById('load-more-btn');
        const loadMoreSpinner = document.getElementById('load-more-spinner');
        
        if (loadMoreBtn) {
            loadMoreBtn.disabled = false;
            loadMoreBtn.innerHTML = '📄 Daha Fazla Yükle';
        }
        
        if (loadMoreSpinner) {
            loadMoreSpinner.classList.add('hidden');
        }
    }

    updateLoadMoreButton() {
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (!loadMoreBtn) return;

        if (this.hasMore && this.templates.length > 0) {
            loadMoreBtn.classList.remove('hidden');
        } else {
            loadMoreBtn.classList.add('hidden');
        }
        
        this.hideLoadMoreLoading();
    }

    showError(message) {
        console.error('Templates Error:', message);
        this.showToast(message, 'error');
    }

    // Toast notification system with deduplication
    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        // Deduplication: Check if same message exists in last 3 seconds
        const existingToasts = container.querySelectorAll('.toast');
        const now = Date.now();
        
        for (let toast of existingToasts) {
            const toastMessage = toast.querySelector('.toast-message')?.textContent;
            const toastTime = parseInt(toast.dataset.timestamp || '0');
            
            if (toastMessage === message && (now - toastTime) < 3000) {
                // Same message within 3 seconds, don't show duplicate
                return;
            }
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.dataset.timestamp = now.toString();
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icons[type] || icons.success}</span>
                <span class="toast-message">${this.escapeHtml(message)}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
        `;

        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('hiding');
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 5000);
    }

    // Utility functions
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('tr-TR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    getCurrentUserId() {
        const userProfile = localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE);
        if (userProfile) {
            try {
                const profile = JSON.parse(userProfile);
                console.log('🔍 Profile data:', profile);
                
                const userId = profile?.id || profile?.user_id;
                console.log('🆔 User ID:', userId, 'Type:', typeof userId);
                
                if (!userId) {
                    console.error('❌ User ID bulunamadı!');
                    return null;
                }
                
                return Number(userId);
            } catch (e) {
                console.error('Profile parse error:', e);
            }
        }
        return null;
    }

    getCurrentUserAdminStatus() {
        return localStorage.getItem(CONFIG.STORAGE_KEYS.IS_ADMIN) === 'true';
    }

    shouldShowDepartmentBadge(template) {
        const isAdmin = this.getCurrentUserAdminStatus();
        const userDept = this.getCurrentUserDepartment();
        
        // Admin ise ve şablon farklı departmandaysa göster
        if (isAdmin && template.department && template.department !== userDept) {
            return true;
        }
        
        // Admin seçili departman filtresi varsa ve şablon o departmandaysa göster
        if (isAdmin && this.currentFilters.department && template.department === this.currentFilters.department) {
            return true;
        }
        
        return false;
    }

    getCurrentUserDepartment() {
        const userProfile = localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE);
        if (userProfile) {
            try {
                const profile = JSON.parse(userProfile);
                return profile.department;
            } catch (e) {
                console.error('Profile parse error:', e);
            }
        }
        return null;
    }

    async loadDepartments() {
        try {
            console.log('🏢 Departmanlar yükleniyor...');
            const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
            const response = await fetch(`${CONFIG.BACKEND_URL}/admin/departments`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 403) {
                    this.showToast('⚠️ Bu işlem için yetkiniz yok', 'warning');
                    return [];
                } else if (response.status === 401) {
                    this.showToast('ℹ️ Oturum süreniz dolmuş, lütfen tekrar giriş yapın', 'info');
                    return [];
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }

            const data = await response.json();
            this.departments = data.departments || [];
            
            console.log('✅ Departmanlar yüklendi:', this.departments.length);
            this.updateDepartmentFilter();
            
            return this.departments;
        } catch (error) {
            console.error('❌ Departman yükleme hatası:', error);
            this.showToast('❌ Departmanlar yüklenirken hata oluştu', 'error');
            return [];
        }
    }

    updateDepartmentFilter() {
        const departmentSelect = document.getElementById('department-filter');
        const adminGroup = document.getElementById('admin-department-group');
        const departmentInfo = document.getElementById('department-info');
        const currentDepartmentSpan = document.getElementById('current-department');
        
        if (!departmentSelect || !adminGroup) return;

        // Admin kontrolü
        const isAdmin = this.getCurrentUserAdminStatus();
        if (isAdmin) {
            adminGroup.classList.remove('hidden');
        } else {
            adminGroup.classList.add('hidden');
            return;
        }

        // Mevcut seçimi sakla
        const currentValue = departmentSelect.value;
        
        // Seçenekleri temizle (ilk seçenek hariç)
        while (departmentSelect.children.length > 1) {
            departmentSelect.removeChild(departmentSelect.lastChild);
        }

        // Departmanları ekle
        this.departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            option.textContent = dept;
            departmentSelect.appendChild(option);
        });

        // Önceki seçimi geri yükle
        departmentSelect.value = currentValue;
        
        // Departman bilgisi güncelle
        this.updateDepartmentInfo();
    }

    updateDepartmentInfo() {
        const departmentSelect = document.getElementById('department-filter');
        const departmentInfo = document.getElementById('department-info');
        const currentDepartmentSpan = document.getElementById('current-department');
        
        if (!departmentSelect || !departmentInfo || !currentDepartmentSpan) return;

        const selectedDept = departmentSelect.value;
        const userDept = this.getCurrentUserDepartment();
        
        if (selectedDept) {
            currentDepartmentSpan.textContent = selectedDept;
            departmentInfo.classList.remove('hidden');
        } else {
            currentDepartmentSpan.textContent = userDept || 'Bilinmeyen';
            departmentInfo.classList.remove('hidden');
        }
    }

    // Filter functions
    applyFilters() {
        const categoryFilter = document.getElementById('category-filter');
        const onlyMineFilter = document.getElementById('only-mine-filter');
        const onlySmsFilter = document.getElementById('only-sms-filter');
        const searchFilter = document.getElementById('search-filter');
        const departmentFilter = document.getElementById('department-filter');

        this.currentFilters = {
            category_id: categoryFilter ? categoryFilter.value : '',
            only_mine: onlyMineFilter ? onlyMineFilter.checked : false,
            is_sms: onlySmsFilter && onlySmsFilter.checked ? true : null,
            q: searchFilter ? searchFilter.value.trim() : '',
            department: departmentFilter ? departmentFilter.value : ''
        };

        // Departman değiştiğinde kategorileri de yeniden yükle
        if (departmentFilter && departmentFilter.value !== this.currentFilters.department) {
            this.loadCategories();
        }

        this.loadTemplates(this.currentFilters);
        this.updateDepartmentInfo();
    }

    clearFilters() {
        const categoryFilter = document.getElementById('category-filter');
        const onlyMineFilter = document.getElementById('only-mine-filter');
        const onlySmsFilter = document.getElementById('only-sms-filter');
        const searchFilter = document.getElementById('search-filter');
        const departmentFilter = document.getElementById('department-filter');

        if (categoryFilter) categoryFilter.value = '';
        if (onlyMineFilter) onlyMineFilter.checked = false;
        if (onlySmsFilter) onlySmsFilter.checked = false;
        if (searchFilter) searchFilter.value = '';
        if (departmentFilter) departmentFilter.value = '';

        this.currentFilters = {
            category_id: '',
            only_mine: false,
            is_sms: null,
            q: '',
            department: ''
        };

        this.loadTemplates(this.currentFilters);
        this.updateDepartmentInfo();
    }

    async copyTemplateAsResponse(templateId) {
        console.log('🔄 copyTemplateAsResponse başlatıldı:', templateId);
        
        // Çift tıklama koruması
        if (this.isProcessing) {
            console.log('⚠️ İşlem zaten devam ediyor, çift tıklama engellendi');
            return;
        }
        this.isProcessing = true;
        
        const template = this.templates.find(t => t.id == templateId);
        if (!template) {
            console.log('❌ Template bulunamadı:', templateId);
            this.isProcessing = false;
            return;
        }
        
        console.log('✅ Template bulundu:', template.title);
        
        try {
            // 1. Şablon içeriğini panoya kopyala
            await navigator.clipboard.writeText(template.content);
            console.log('✅ Şablon panoya kopyalandı');
            
            // 2. Ana sayfaya dön
            navigationManager.showHomeScreen();
            
            // 3. Şablon içeriğini "Son Üretilen Yanıt" alanına sabitle (readonly textarea)
            if (responseManager && responseManager.displayResponse) {
                responseManager.displayResponse(template.content, true);
            } else {
                const mainResponse = document.getElementById('main-response');
                if (mainResponse) {
                    mainResponse.innerHTML = `<textarea id=\"main-response-editor\" class=\"response-textarea\" readonly style=\"width:100%; height:300px; padding:12px; border:2px solid #e5e7eb; border-radius:8px; background:#f5f5f5; font-size:14px; line-height:1.5; white-space:pre-wrap; word-wrap:break-word; overflow-y:auto; resize:vertical; margin:0; display:block;\">${this.escapeHtml ? this.escapeHtml(template.content) : template.content}</textarea>`;
                }
            }
            
            // 4. Backend'e şablon kullanımını kaydet
            try {
                const useResponse = await fetch(`${CONFIG.BACKEND_URL}/templates/${templateId}/use`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN)}`,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (useResponse.ok) {
                    console.log('✅ Şablon kullanımı backend\'e kaydedildi');
                } else {
                    console.log('⚠️ Şablon kullanımı backend\'e kaydedilemedi');
                }
            } catch (error) {
                console.error('❌ Şablon kullanımı kaydetme hatası:', error);
            }
            
            // 5. State'i güncelle (sayac backend'de artırıldı)
            if (responseManager) {
                responseManager.state = 'finalized'; // State'i finalized yap
                console.log('✅ State finalized yapıldı');
            }
            
            // 6. Tüm "Şablon olarak sakla" UI'larını gizle
            if (responseManager && responseManager.hideAllTemplateSaveUIs) {
                responseManager.hideAllTemplateSaveUIs();
            }
            
            // 7. Button visibility'yi güncelle
            if (responseManager && responseManager.updateButtonVisibility) {
                responseManager.updateButtonVisibility();
            }
            
            // 8. "Yeni İstek Öneri Cevapla" düğmesini doğrudan göster
            const newRequestBtn = document.getElementById('new-request-btn');
            if (newRequestBtn) {
                newRequestBtn.style.display = 'block';
                console.log('✅ Yeni İstek Öneri Cevapla düğmesi gösterildi');
            }
            
            // 9. Toast bildirimi
            if (templateSaveManager) {
                templateSaveManager.showToast('✅ Şablon kopyalandı ve ana sayfaya eklendi', 'success');
            }
            
            // 10. Analitik tracking
            this.trackEvent('template_used', { action: 'copy_as_response' });
            
        } catch (error) {
            console.error('❌ Şablon kopyalama hatası:', error);
            if (templateSaveManager) {
                templateSaveManager.showToast('❌ Şablon kopyalama hatası', 'error');
            }
        } finally {
            // İşlem tamamlandı, çift tıklama korumasını kaldır
            this.isProcessing = false;
            console.log('✅ İşlem tamamlandı, çift tıklama koruması kaldırıldı');
        }
    }

    openEditModal(templateId) {
        console.log('openEditModal çağrıldı:', templateId);
        const template = this.templates.find(t => t.id == templateId);
        if (!template) return;
        this.editingTemplateId = templateId;
        const modal = document.getElementById('template-edit-modal');
        const titleInput = document.getElementById('template-edit-title');
        const textarea = document.getElementById('template-edit-text');
        const saveCheckbox = document.getElementById('template-edit-save-checkbox');
        const categorySection = document.getElementById('template-edit-category-section');
        const categorySelect = document.getElementById('template-edit-category-select');
        if (!modal || !titleInput || !textarea) {
            console.warn('Edit modal elementleri bulunamadı', { modal: !!modal, title: !!titleInput, textarea: !!textarea });
            return;
        }
        titleInput.value = template.title || '';
        textarea.value = template.content || '';
        if (saveCheckbox) saveCheckbox.checked = false;
        if (categorySection) categorySection.classList.add('hidden');
        if (categorySelect) categorySelect.value = '';
        // Yeni kategori input'unu temizle
        this.hideEditNewCategoryInput();
        // Kategori listesini doldur
        this.populateEditCategories();
        modal.classList.remove('hidden');
        modal.classList.add('show');
        setTimeout(() => { (titleInput || textarea).focus(); }, 0);
    }

    populateEditCategories() {
        const select = document.getElementById('template-edit-category-select');
        if (!select || !templateSaveManager) return;
        // temizle
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        const categories = templateSaveManager.categories || [];
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat.id;
            opt.textContent = cat.name;
            select.appendChild(opt);
        });
    }

    closeEditModal() {
        const modal = document.getElementById('template-edit-modal');
        if (modal) modal.classList.add('hidden');
        this.editingTemplateId = null;
        // Yeni kategori input'unu da temizle
        this.hideEditNewCategoryInput();
    }

    showEditNewCategoryInput() {
        const inputGroup = document.getElementById('template-edit-new-category-input-group');
        const newCategoryBtn = document.getElementById('template-edit-new-category-btn');
        const categoryInput = document.getElementById('template-edit-new-category-name');
        
        if (inputGroup) {
            inputGroup.classList.remove('hidden');
        }
        
        if (newCategoryBtn) {
            newCategoryBtn.classList.add('hidden');
        }
        
        if (categoryInput) {
            categoryInput.value = '';
            categoryInput.focus();
        }
    }

    hideEditNewCategoryInput() {
        const inputGroup = document.getElementById('template-edit-new-category-input-group');
        const newCategoryBtn = document.getElementById('template-edit-new-category-btn');
        const categoryInput = document.getElementById('template-edit-new-category-name');
        
        if (inputGroup) {
            inputGroup.classList.add('hidden');
        }
        
        if (newCategoryBtn) {
            newCategoryBtn.classList.remove('hidden');
        }
        
        if (categoryInput) {
            categoryInput.value = '';
        }
    }

    async createEditCategory() {
        const categoryInput = document.getElementById('template-edit-new-category-name');
        const categoryName = categoryInput ? categoryInput.value.trim() : '';
        
        if (!categoryName) {
            if (templateSaveManager) {
                templateSaveManager.showToast('⚠️ Kategori adı boş olamaz', 'warning');
            }
            return;
        }
        
        try {
            const newCategory = await templateSaveManager.createCategory(categoryName);
            if (newCategory) {
                // Kategorileri yeniden yükle ve dropdown'ı güncelle
                await templateSaveManager.loadCategories();
                this.populateEditCategories();
                
                // Yeni kategoriyi seç
                const categorySelect = document.getElementById('template-edit-category-select');
                if (categorySelect) {
                    categorySelect.value = newCategory.id;
                }
                
                this.hideEditNewCategoryInput();
            }
        } catch (error) {
            console.error('Kategori oluşturma hatası:', error);
        }
    }

    async confirmEditAndCopy() {
        if (this.isProcessing) return;
        this.isProcessing = true;
        try {
            const titleInput = document.getElementById('template-edit-title');
            const textarea = document.getElementById('template-edit-text');
            const saveCheckbox = document.getElementById('template-edit-save-checkbox');
            const categorySelect = document.getElementById('template-edit-category-select');
            const editedTitle = titleInput ? titleInput.value.trim() : '';
            const editedContent = textarea ? textarea.value : '';
            if (!editedContent) {
                templateSaveManager.showToast('⚠️ İçerik boş olamaz', 'warning');
                this.isProcessing = false;
                return;
            }

            // Şablon saklama seçiliyse kategori kontrolü
            if (saveCheckbox && saveCheckbox.checked) {
                if (!categorySelect || !categorySelect.value) {
                    templateSaveManager.showToast('⚠️ Şablon olarak kaydetmek için lütfen bir kategori seçin', 'warning');
                    this.isProcessing = false;
                    return;
                }
            }

            // 1) Panoya kopyala
            await navigator.clipboard.writeText(editedContent);

            // 2) Ana sayfaya dön ve sabitle (readonly)
            navigationManager.showHomeScreen();
            if (responseManager && responseManager.displayResponse) {
                responseManager.displayResponse(editedContent, true);
            }

            // 3) Backend'e şablon kullanımını kaydet
            if (this.editingTemplateId) {
                try {
                    const useResponse = await fetch(`${CONFIG.BACKEND_URL}/templates/${this.editingTemplateId}/use`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN)}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    if (!useResponse.ok) {
                        console.log('⚠️ Şablon kullanımı backend\'e kaydedilemedi');
                    }
                } catch (err) {
                    console.error('❌ Şablon kullanımı kaydetme hatası:', err);
                }
            }

            // 4) İsteğe bağlı şablon olarak kaydet (kategori kontrolü zaten yapıldı)
            if (saveCheckbox && saveCheckbox.checked && templateSaveManager && categorySelect && categorySelect.value) {
                const isSMS = responseManager.currentIsSMS || false;
                await templateSaveManager.saveTemplate(editedContent, parseInt(categorySelect.value), isSMS);
            }

            // 5) UI state ve butonlar
            if (responseManager) {
                responseManager.state = 'finalized';
                if (responseManager.hideAllTemplateSaveUIs) responseManager.hideAllTemplateSaveUIs();
                if (responseManager.updateButtonVisibility) responseManager.updateButtonVisibility();
            }
            const newRequestBtn = document.getElementById('new-request-btn');
            if (newRequestBtn) newRequestBtn.style.display = 'block';

            // 6) Toast
            if (templateSaveManager) {
                templateSaveManager.showToast('✅ Düzenlenen şablon kopyalandı ve eklendi', 'success');
            }

            // 7) Modalı kapat
            this.closeEditModal();

            // 8) Analitik
            this.trackEvent('template_used', { action: 'edit_and_copy' });
        } catch (error) {
            console.error('❌ Düzenle/kopyala hatası:', error);
            if (templateSaveManager) templateSaveManager.showToast('❌ Düzenle/kopyala hatası', 'error');
        } finally {
            this.isProcessing = false;
        }
    }

    showDeleteModal(templateId) {
        // Güvenlik: Geçersiz çağrılarda açma
        const idNum = Number(templateId);
        if (!idNum || Number.isNaN(idNum)) {
            return;
        }
        this.selectedTemplateId = idNum;
        const modal = document.getElementById('delete-template-modal');
        if (modal) {
            modal.classList.add('show');
            modal.classList.remove('hidden');
            // Focus trap
            const confirmBtn = document.getElementById('confirm-delete');
            if (confirmBtn) confirmBtn.focus();
        }
    }

    hideDeleteModal() {
        const modal = document.getElementById('delete-template-modal');
        if (modal) {
            modal.classList.remove('show');
            modal.classList.add('hidden');
        }
        this.selectedTemplateId = null;
    }

    async confirmDelete() {
        if (!this.selectedTemplateId) return;
        
        const confirmBtn = document.getElementById('confirm-delete');
        const btnText = confirmBtn.querySelector('.btn-text');
        const btnSpinner = confirmBtn.querySelector('.btn-spinner');
        
        // Loading state
        confirmBtn.disabled = true;
        btnText.classList.add('hidden');
        btnSpinner.classList.remove('hidden');
        
        try {
            const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
            const response = await fetch(`${CONFIG.BACKEND_URL}/templates/${this.selectedTemplateId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                if (response.status === 403) {
                    this.showToast('⚠️ Bu işlem için yetkiniz yok', 'warning');
                    return;
                } else if (response.status === 404) {
                    this.showToast('❌ Şablon bulunamadı', 'error');
                    return;
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }

            console.log('✅ Şablon silindi');
            this.showToast('✅ Şablon silindi', 'success');
            this.trackEvent('template_deleted');
            this.hideDeleteModal();
            this.loadTemplates(this.currentFilters);
        } catch (error) {
            console.error('❌ Şablon silme hatası:', error);
            this.showToast('❌ Şablon silinirken hata oluştu', 'error');
        } finally {
            // Reset button state
            confirmBtn.disabled = false;
            btnText.classList.remove('hidden');
            btnSpinner.classList.add('hidden');
        }
    }

    async deleteTemplate(templateId) {
        // Sadece kullanıcı karttaki Sil'e tıklarsa çağrılacak. Otomatik tetiklenmemesi için ek koruma.
        if (!templateId) return;
        this.showDeleteModal(templateId);
    }

    // Initialize templates screen
    async initializeTemplatesScreen() {
        console.log('📂 Templates screen başlatılıyor...');
        // Güvenlik: ekrana girerken tüm modalları kapalı tut
        this.hideUseModal();
        this.hideDeleteModal();
        this.selectedTemplate = null;
        this.selectedTemplateId = null;
        
        // Admin ise departmanları yükle
        if (this.getCurrentUserAdminStatus()) {
            await this.loadDepartments();
        } else {
            // Admin değilse departman filtresi grubunu gizle
            const deptGroup = document.getElementById('admin-department-group');
            if (deptGroup) deptGroup.classList.add('hidden');
        }
        
        // Kategorileri ve şablonları yükle
        await this.loadCategories();
        
        // Event listener'ları ekle (şablon yüklemeden önce, çünkü applyFilters içinde loadTemplates çağrılacak)
        this.setupEventListeners();
        
        // Checkbox'ların durumuna göre filtreleri uygula (sayfa yüklendiğinde)
        this.applyFilters();
    }

    setupEventListeners() {
        // Filtre event listener'ları
        const categoryFilter = document.getElementById('category-filter');
        const onlyMineFilter = document.getElementById('only-mine-filter');
        const searchFilter = document.getElementById('search-filter');
        const departmentFilter = document.getElementById('department-filter');
        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        const refreshBtn = document.getElementById('refresh-templates-btn');

        if (categoryFilter) {
            categoryFilter.addEventListener('change', () => this.applyFilters());
        }

        if (onlyMineFilter) {
            onlyMineFilter.addEventListener('change', () => this.applyFilters());
        }
        
        const onlySmsFilter = document.getElementById('only-sms-filter');
        if (onlySmsFilter) {
            onlySmsFilter.addEventListener('change', () => this.applyFilters());
        }

        if (departmentFilter) {
            departmentFilter.addEventListener('change', () => this.applyFilters());
        }

        if (searchFilter) {
            searchFilter.addEventListener('input', () => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.applyFilters();
                }, 300); // 300ms debounce
            });
            
            // Enter tuşu ile anında arama
            searchFilter.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    clearTimeout(this.searchTimeout);
                    this.applyFilters();
                }
            });
        }

        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadTemplates(this.currentFilters));
        }

        // Load More button
        const loadMoreBtn = document.getElementById('load-more-btn');
        // Load More kaldırıldı: buton event'i bağlama

        // Template action event listener'ları
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('copy-template-btn')) {
                const templateId = e.target.dataset.templateId;
                this.copyTemplateAsResponse(templateId);
            } else if (e.target.classList.contains('edit-template-btn')) {
                const templateId = e.target.dataset.templateId;
                console.log('✏️ Düzenle tıklandı:', templateId);
                this.openEditModal(templateId);
            } else if (e.target.classList.contains('delete-template-btn')) {
                const templateId = e.target.dataset.templateId;
                this.selectedTemplate = templateId;
                // Koruma: geçersiz id varsa açma
                if (templateId) {
                    this.showDeleteModal(templateId);
                }
            }
        });

        // Edit modal controls
        document.addEventListener('click', async (e) => {
            if (e.target.id === 'template-edit-cancel' || e.target.id === 'close-template-edit-modal') {
                this.closeEditModal();
            } else if (e.target.id === 'template-edit-copy') {
                await this.confirmEditAndCopy();
            } else if (e.target.id === 'template-edit-save-checkbox') {
                const checked = e.target.checked;
                const section = document.getElementById('template-edit-category-section');
                if (section) section.classList.toggle('hidden', !checked);
                if (checked && templateSaveManager && (!templateSaveManager.categories || templateSaveManager.categories.length === 0)) {
                    await templateSaveManager.loadCategories();
                    this.populateEditCategories();
                }
            } else if (e.target.id === 'template-edit-new-category-btn') {
                this.showEditNewCategoryInput();
            } else if (e.target.id === 'template-edit-create-category-btn') {
                await this.createEditCategory();
            } else if (e.target.id === 'template-edit-cancel-category-btn') {
                this.hideEditNewCategoryInput();
            }
        });
    }

    showUseModal() {
        const modal = document.getElementById('use-template-modal');
        if (modal) {
            modal.classList.remove('hidden');
            
            // Klavye kısayolları için event listener ekle
            this.setupUseModalKeyboard();
        }
    }

    setupUseModalKeyboard() {
        const modal = document.getElementById('use-template-modal');
        if (!modal) return;

        const handleKeydown = (e) => {
            if (modal.classList.contains('hidden')) return;
            
            switch(e.key) {
                case '1':
                    e.preventDefault();
                    this.useTemplate(this.selectedTemplate, 'request');
                    break;
                case '2':
                    e.preventDefault();
                    this.useTemplate(this.selectedTemplate, 'response');
                    break;
                case '3':
                    e.preventDefault();
                    this.useTemplate(this.selectedTemplate, 'clipboard');
                    break;
                case 'Enter':
                    e.preventDefault();
                    // Varsayılan olarak ilk seçeneği kullan
                    this.useTemplate(this.selectedTemplate, 'request');
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.hideUseModal();
                    break;
            }
        };

        // Event listener'ı ekle
        document.addEventListener('keydown', handleKeydown);
        
        // Modal kapanınca event listener'ı kaldır
        const originalHide = this.hideUseModal;
        this.hideUseModal = () => {
            document.removeEventListener('keydown', handleKeydown);
            originalHide.call(this);
        };
    }

    hideUseModal() {
        const modal = document.getElementById('use-template-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // Remove duplicate definitions (use the earlier implementations with templateId)
}

// Navigation Manager for screen switching
class NavigationManager {
    constructor() {
        this.currentScreen = 'home'; // 'home' or 'templates'
    }

    showHomeScreen() {
        console.log('🏠 Ana Sayfa gösteriliyor...');
        
        // Screens
        const mainScreen = document.getElementById('main-screen');
        const templatesScreen = document.getElementById('templates-screen');
        
        // Buttons
        const homeBtn = document.getElementById('home-btn');
        const templatesBtn = document.getElementById('templates-btn');
        const homeBtnTemplates = document.getElementById('home-btn-templates');
        const templatesBtnTemplates = document.getElementById('templates-btn-templates');
        
        // Show/hide screens
        if (mainScreen) mainScreen.classList.remove('hidden');
        if (templatesScreen) templatesScreen.classList.add('hidden');
        
        // Update button states
        if (homeBtn) homeBtn.classList.add('active');
        if (templatesBtn) templatesBtn.classList.remove('active');
        if (homeBtnTemplates) homeBtnTemplates.classList.add('active');
        if (templatesBtnTemplates) templatesBtnTemplates.classList.remove('active');
        
        this.currentScreen = 'home';
        
        // Update user profile in both screens
        this.updateUserProfile();
    }

    async showTemplatesScreen() {
        console.log('📂 Şablonlarım ekranı gösteriliyor...');
        
        // Screens
        const mainScreen = document.getElementById('main-screen');
        const templatesScreen = document.getElementById('templates-screen');
        
        // Buttons
        const homeBtn = document.getElementById('home-btn');
        const templatesBtn = document.getElementById('templates-btn');
        const homeBtnTemplates = document.getElementById('home-btn-templates');
        const templatesBtnTemplates = document.getElementById('templates-btn-templates');
        
        // Show/hide screens
        if (mainScreen) mainScreen.classList.add('hidden');
        if (templatesScreen) templatesScreen.classList.remove('hidden');
        
        // Update button states
        if (homeBtn) homeBtn.classList.remove('active');
        if (templatesBtn) templatesBtn.classList.add('active');
        if (homeBtnTemplates) homeBtnTemplates.classList.remove('active');
        if (templatesBtnTemplates) templatesBtnTemplates.classList.add('active');
        
        this.currentScreen = 'templates';
        
        // Update user profile in both screens
        this.updateUserProfile();
        
        // Initialize templates screen (modallar reset ile birlikte)
        await templatesManager.initializeTemplatesScreen();
    }

    updateUserProfile() {
        const userProfile = localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE);
        if (userProfile) {
            try {
                const profile = JSON.parse(userProfile);
                const profileText = `👤 ${profile.full_name || 'Kullanıcı'}`;
                
                // Update both screens - user name
                const userProfileMain = document.getElementById('user-profile');
                const userProfileTemplates = document.getElementById('user-profile-templates');
                
                if (userProfileMain) userProfileMain.textContent = profileText;
                if (userProfileTemplates) userProfileTemplates.textContent = profileText;
            } catch (e) {
                console.error('Profile update error:', e);
            }
        }
    }

    getCurrentScreen() {
        return this.currentScreen;
    }
}

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

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                // Response body'yi oku (JSON parse edilebilirse)
                let errorDetail = response.statusText;
                try {
                    const errorBody = await response.json();
                    if (errorBody.detail) {
                        errorDetail = errorBody.detail;
                    }
                } catch (e) {
                    // JSON parse edilemezse statusText kullan
                }
                
                // Güvenlik hataları için özel mesajlar
                if (response.status === 403) {
                    throw new Error('Bu işlem için yetkiniz yok');
                } else if (response.status === 401) {
                    throw new Error('Oturum süreniz dolmuş, lütfen tekrar giriş yapın');
                } else if (response.status === 404) {
                    throw new Error('İstenen kaynak bulunamadı');
                } else if (response.status === 500) {
                    throw new Error(`Sunucu hatası: ${errorDetail}`);
                } else {
                    throw new Error(`HTTP ${response.status}: ${errorDetail}`);
                }
            }
            
            return response.json();
        } catch (error) {
            // Network hataları veya diğer fetch hataları
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError') || error.message.includes('Network request failed')) {
                console.error('Network error:', error);
                throw new Error('Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin.');
            }
            throw error;
        }
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

    async verifyMagicLink(token) {
        // Magic link için backend'e POST request yap
        return this.request('/verify-magic-link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: token })
        });
    }

    async completeProfile(profileData) {
        const token = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
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
        
        // Magic link kontrolü için checkBackendSession çağır
        const hasSession = await this.checkBackendSession();
        
        if (!hasSession) {
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
                // Profile'ı tam olarak kaydet - id dahil
                this.appState.userProfile = {
                    id: profile.id,
                    email: profile.email,
                    full_name: profile.full_name || '',
                    department: profile.department || '',
                    is_active: profile.is_active || false,
                    profile_completed: profile.profile_completed || false,
                    created_at: profile.created_at,
                    last_login: profile.last_login
                };
                console.log('✅ Profile kaydedildi:', this.appState.userProfile);
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
            
            // Magic link ile geliyorsa (auto_login=true varsa) çıkış flag'ini kontrol etme
            const urlParams = new URLSearchParams(window.location.search);
            const isMagicLink = urlParams.get('auto_login') === 'true';
            console.log('URL params:', window.location.search);
            console.log('isMagicLink:', isMagicLink);
            
            // Magic link ile geldiyse gerçek authentication yap
            if (isMagicLink) {
                console.log('Magic link detected, processing real authentication');
                localStorage.removeItem('user_logged_out');
                
                // URL'den token'ı al
                const urlParams = new URLSearchParams(window.location.search);
                const magicToken = urlParams.get('token') || urlParams.get('auth_token');
                
                if (magicToken) {
                    console.log('Magic token found, processing authentication:', magicToken);
                    const authResult = await this.handleMagicLinkAuth(magicToken);
                    if (authResult) {
                        return true;
                    }
                }
                
                // Token yoksa veya authentication başarısızsa login göster
                console.log('Magic link authentication failed, showing login');
                ui.hideLoadingScreen();
                ui.showLogin();
                return false;
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
                ui.hideLoadingScreen();
                ui.showLogin();
                return false;
            }
            
            // Magic link değilse: aktif session veya geçerli token varsa kullanıcıyı otomatik içeri al
            if (!isMagicLink) {
                // localStorage'da auth token var mı?
                const hasToken = !!localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
                if (hasActiveSession || hasToken) {
                    console.log('Existing session/token found, resuming session');
                    // Kullanıcı profilini yükle ve ana uygulamayı göster
                    await this.updateUserProfile();
                    ui.hideLoadingScreen();
                    ui.showMainApp();
                    return true;
                }
                console.log('No active session, showing login screen');
                ui.hideLoadingScreen();
                ui.showLogin();
                return false;
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
                this.appState.accessToken = response.access_token; // Eksik olan bu!
                this.appState.userProfile = {
                    id: response.user_id || null,  // CodeVerifyResponse'dan user_id geliyor
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
                
                // Profil tamamlama kontrolü - DEBUG LOGLARI
                console.log('=== PROFIL KONTROL DEBUG ===');
                console.log('response.profile_completed:', response.profile_completed, typeof response.profile_completed);
                console.log('response.full_name:', response.full_name);
                console.log('response.department:', response.department);
                console.log('Kontrol sonucu:', !response.profile_completed || !response.full_name || !response.department);
                
                if (!response.profile_completed || !response.full_name || !response.department) {
                    console.log('❌ Profil tamamlanmamış, profil sayfasına yönlendiriliyor');
                    ui.showProfileCompletion();
                } else {
                    console.log('✅ Profil tamamlanmış, ana sayfaya yönlendiriliyor');
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

    async copyPreviousResponse(responseId, editedText = null) {
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
        const textToCopy = editedText !== null ? editedText : response.response_text;
            navigator.clipboard.writeText(textToCopy).then(() => {
            console.log('✅ Önceki yanıt panoya kopyalandı!');
            
            // Ana yanıtı göster (seçilen yanıt) ve düzenlemeyi kilitle
            this.displayResponse(textToCopy, true);
            
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
            templateSaveManager.showToast('❌ Kopyalama başarısız.', 'error');
        });
    }

    saveToStorage() {
        localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, this.appState.authToken);
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER_EMAIL, this.appState.userEmail);
        localStorage.setItem(CONFIG.STORAGE_KEYS.IS_ADMIN, this.appState.isAdmin.toString());
        localStorage.setItem(CONFIG.STORAGE_KEYS.USER_PROFILE, JSON.stringify(this.appState.userProfile));
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
        
        const validation = {
            authenticated: this.appState.authenticated,
            hasUserEmail: !!this.appState.userEmail,
            hasAccessToken: !!this.appState.accessToken,
            hasAuthToken: !!this.appState.authToken,
            isValid: null  // Bu satır problemi gösteriyor
        };
        
        console.log('checkAuthenticationState validation:', validation);
        
        // KRITIK DÜZELTME: Boolean değer döndür
        const isValid = this.appState.authenticated && 
                       this.appState.userEmail && 
                       (this.appState.accessToken || this.appState.authToken);
        
        if (!isValid) {
            console.error('Authentication state validation failed:', {
                authenticated: this.appState.authenticated,
                hasUserEmail: !!this.appState.userEmail,
                hasAccessToken: !!this.appState.accessToken,
                hasAuthToken: !!this.appState.authToken
            });
        }
        
        console.log('checkAuthenticationState() result:', isValid, typeof isValid);
        
        // KRITIK: Boolean değer return et
        return isValid;  // true veya false döndür, null değil
    }

    async handleMagicLinkAuth(token) {
        try {
            console.log('Magic link authentication başlatılıyor:', token);
            
            // Magic link token'ını doğrula
            const response = await this.api.verifyMagicLink(token);
            
            if (response.access_token) {
                console.log('Magic link doğrulama başarılı:', response);
                
                // Authentication state'i güncelle
                this.appState.authenticated = true;
                this.appState.userEmail = response.email;
                this.appState.isAdmin = response.is_admin || false;
                this.appState.authToken = response.access_token;
                this.appState.accessToken = response.access_token; // Eksik olan bu!
                this.appState.userProfile = {
                    id: response.user_id || null,  // TokenConsumeResponse'dan user_id geliyor
                    email: response.email,
                    full_name: response.full_name || '',
                    department: response.department || '',
                    profile_completed: response.profile_completed || false
                };
                
                console.log('Magic link authentication state güncellendi:', {
                    authenticated: this.appState.authenticated,
                    userEmail: this.appState.userEmail,
                    profileCompleted: this.appState.userProfile.profile_completed
                });
                
                // Session'ı localStorage'a kaydet
                this.saveToStorage();
                
                // Çıkış flag'ini temizle
                localStorage.removeItem('user_logged_out');
                
                // Loading screen'i gizle
                ui.hideLoadingScreen();
                
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
                
                return true;
            }
            return false;
        } catch (error) {
            console.error('Magic link authentication hatası:', error);
            ui.hideLoadingScreen();
            this.showErrorMessage('❌ Magic link doğrulama hatası. Lütfen tekrar deneyin.');
            ui.showLogin();
            return false;
        }
    }

    async completeProfile() {
        try {
            console.log('Profil tamamlama başlatılıyor...');
            
            // Authentication state kontrolü - KRITIK: Boolean karşılaştırma yap
            const isAuthenticated = this.checkAuthenticationState();
            console.log('checkAuthenticationState() result:', isAuthenticated, typeof isAuthenticated);
            
            if (!isAuthenticated) {  // Boolean check
                console.error('AUTHENTICATION FAILED - Cannot complete profile');
                console.error('Authentication check returned:', isAuthenticated);
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

        // Profil ekranı açıldığında müdürlük listesini veritabanından yükle
        try {
            this.loadProfileDepartments();
        } catch (e) {
            console.error('Profil departmanları yüklenirken hata:', e);
        }
    }

    async loadProfileDepartments() {
        const select = document.getElementById('profile-department');
        if (!select) return;

        try {
            console.log('🏢 Profil için departmanlar yükleniyor...');
            const response = await fetch(`${CONFIG.BACKEND_URL}/departments`);
            if (!response.ok) {
                console.error('Departman isteği başarısız:', response.status, response.statusText);
                return;
            }

            const data = await response.json();
            const departments = data.departments || [];

            // Var olan seçenekleri (ilk placeholder hariç) temizle
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }

            departments.forEach((dept) => {
                const option = document.createElement('option');
                option.value = dept;
                option.textContent = dept;
                select.appendChild(option);
            });

            console.log('✅ Profil departmanları yüklendi:', departments.length);
        } catch (error) {
            console.error('❌ Profil departmanları yüklenirken hata oluştu:', error);
        }
    }

    // Alias for compatibility
    showProfileUpdate() {
        this.showProfileCompletion();
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
        
        // Ana sayfayı göster ve navigation state'i ayarla
        navigationManager.showHomeScreen();
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
            this.elements.adminPanel.classList.add('hidden');
            document.body.classList.remove('admin-user'); // Admin değilse class'ı kaldır
        }
        
        // Show response settings only for admin users
        const responseSettings = document.getElementById('response-settings');
        if (responseSettings) {
            if (isAdmin) {
                responseSettings.style.display = 'block';
            } else {
                responseSettings.style.display = 'none';
            }
        }
        
        console.log('=== showMainApp END ===');
    }

    hideAllScreens() {
        this.elements.loginScreen.classList.add('hidden');
        this.elements.profileScreen.classList.add('hidden');
        this.elements.mainScreen.classList.add('hidden');
        
        // Templates screen'i de gizle
        const templatesScreen = document.getElementById('templates-screen');
        if (templatesScreen) {
            templatesScreen.classList.add('hidden');
        }
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
        this.accessToken = null; // Eksik olan bu!
        this.responseHistory = [];
        this.currentResponseId = null;
    }

    // Load state from localStorage
    loadFromStorage() {
        this.authToken = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
        this.accessToken = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN); // accessToken = authToken
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

    async generateResponse(isSMS = false) {
        try {
            ui.showLoading();
            
            const originalText = ui.elements.requestInput.value.trim();
            const customInput = ui.elements.responseInput.value.trim();
            const model = ui.elements.modelSelect.value;
            const temperature = parseFloat(ui.elements.temperature.value);
            const maxTokens = parseInt(ui.elements.maxTokens.value);
            
            // Boş alan kontrolü - ikisinden biri boşsa uyarı ver
            if (!originalText || !customInput) {
                // Her durumda iki alanın adını birlikte belirt
                templateSaveManager.showToast('❌ Lütfen "Gelen İstek/Öneri" ve "Hazırladığınız Cevap Taslağı" alanlarını doldurun.', 'error');
                ui.hideLoading();
                return;
            }

            // Maksimum 5 yanıt kontrolü (Gradio app.py'den)
            if (this.yanitSayisi >= 5) {
                templateSaveManager.showToast('⚠️ Maksimum 5 yanıt üretildi! Yeni istek için "Yeni İstek"e basın.', 'warning');
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
                system_prompt: "",
                is_sms: isSMS
            };

            const response = await api.generateResponse(generateData);
            
            // SMS yanıtı için is_sms flag'ini sakla
            if (isSMS) {
                this.currentIsSMS = true;
            } else {
                this.currentIsSMS = false;
            }
            
            if (response && response.response_text) {
                // Yeni yanıtı oluştur (Gradio app.py formatında)
                const newResponse = {
                    id: response.id,
                    response_text: response.response_text,
                    created_at: new Date().toISOString(),
                    latency_ms: response.latency_ms || 0,
                    model_name: model,
                    is_sms: isSMS || false
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
            templateSaveManager.showToast('❌ Yanıt üretilirken hata oluştu.', 'error');
        } finally {
            ui.hideLoading();
        }
    }

    displayResponse(text, readOnly = false) {
        if (ui.elements.mainResponse) {
            // Düzenlenebilir textarea render et
            ui.elements.mainResponse.innerHTML = `
                <textarea id=\"main-response-editor\" class=\"response-textarea\" ${readOnly ? 'readonly' : ''} style=\"width:100%; height:300px; padding:12px; border:2px solid #e5e7eb; border-radius:8px; background:${readOnly ? '#f5f5f5' : '#ffffff'}; font-size:14px; line-height:1.5; white-space:pre-wrap; word-wrap:break-word; overflow-y:auto; resize:vertical; margin:0; display:block;\">${this.escapeHtml ? this.escapeHtml(text) : text}</textarea>
            `;
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
            const editor = document.getElementById('main-response-editor');
            const text = editor ? editor.value : ui.elements.mainResponse.textContent;
            
            // Durum makinesi kontrolü - eğer zaten kopyalanmışsa hiçbir şey yapma
            if (this.state === 'finalized') {
                console.log('Already copied, ignoring');
                return;
            }
            
            // Şablon kaydetme kontrolü
            const templateValidation = templateSaveManager.validateTemplateSave();
            if (!templateValidation.valid) {
                templateSaveManager.showToast(templateValidation.message, 'warning');
                return;
            }
            
            // Şablon kaydetme işlemi
            if (templateValidation.content && templateValidation.categoryId) {
                const isSMS = responseManager.currentIsSMS || false;
                await templateSaveManager.saveTemplate(templateValidation.content, templateValidation.categoryId, isSMS);
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
            
            // Kopyalama öncesi tüm mini "şablon kaydet" alanlarını gizle
            this.hideAllTemplateSaveUIs();

            navigator.clipboard.writeText(text).then(() => {
                console.log('✅ Ana yanıt panoya kopyalandı!');
                // Kopyalamadan sonra düzenlemeyi kilitle
                if (editor) {
                    editor.setAttribute('readonly', 'true');
                    editor.style.background = '#f5f5f5';
                }
                
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
            templateSaveManager.showToast('❌ Kopyalama başarısız.', 'error');
            });
        }
    }

    hideAllTemplateSaveUIs() {
        try {
            const nodes = document.querySelectorAll('.prev-template-save');
            nodes.forEach(n => n.style.display = 'none');
            // Ana bölümdeki şablon kaydetme alanını da kapat
            if (typeof templateSaveManager?.hideTemplateSaveSection === 'function') {
                templateSaveManager.hideTemplateSaveSection();
            } else {
                const mainSave = document.getElementById('save-template-section');
                if (mainSave) mainSave.classList.add('hidden');
            }
        } catch (e) {
            console.warn('template save UI gizleme uyarısı:', e);
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

    async copyPreviousResponse(responseId, editedText = null) {
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

        // Kopyalama öncesi tüm "şablon olarak sakla" alanlarını gizle
        this.hideAllTemplateSaveUIs();

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
            if (editedText !== null) {
                selectedResponse.response_text = editedText;
            }
            
            // 2. Seçilen yanıtı history'nin başına ekle (ana yanıt olarak)
            this.previousResponses.unshift(selectedResponse);
            
            // 3. Ana yanıt alanını güncelle (readonly, düzenlenmiş metin dahil)
            this.displayResponse(selectedResponse.response_text, true);
            
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
        
        // Input alanlarını temizle
        this.clearTextboxValues();
        
        // Şablon kaydetme formunu temizle
        templateSaveManager.resetTemplateSaveForm();
        
        // Şablon kaydetme bölümünü gizle
        templateSaveManager.hideTemplateSaveSection();
        
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
        // Dış sarmalayıcı (section) görünür değilse aç
        const outerSection = document.querySelector('.previous-responses');
        if (outerSection) {
            outerSection.style.display = 'block';
        }
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
                        <textarea id="prev-editor-${responseNumber}" class="response-textarea" style="width: 100%; height: 300px; padding: 12px; border: 2px solid #e5e7eb; border-radius: 8px; background: #ffffff; font-size: 14px; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word; overflow-y: auto; resize: vertical; margin: 0; display: block;">${response.response_text}</textarea>
                        <div class="prev-template-save" style="display:flex; align-items:center; gap:8px; margin-top:8px;">
                            <label style="display:flex; align-items:center; gap:6px; font-size:13px; color:#374151;">
                                <input type="checkbox" id="prev-save-${responseNumber}" /> Şablon olarak sakla
                            </label>
                            <select id="prev-category-${responseNumber}" class="category-select" style="display:none; padding:6px 8px; border:1px solid #e5e7eb; border-radius:6px;">
                                <option value="">Kategori seçiniz</option>
                            </select>
                            <button id="prev-newcat-btn-${responseNumber}" class="btn btn-secondary btn-sm" style="display:none;">+ Yeni</button>
                            <div id="prev-newcat-group-${responseNumber}" style="display:none; gap:6px; align-items:center;">
                                <input id="prev-newcat-${responseNumber}" type="text" class="category-input" placeholder="Kategori adı" style="padding:6px 8px; border:1px solid #e5e7eb; border-radius:6px;"/>
                                <button id="prev-createcat-${responseNumber}" class="btn btn-primary btn-sm">Oluştur</button>
                                <button id="prev-cancelcat-${responseNumber}" class="btn btn-secondary btn-sm">İptal</button>
                            </div>
                            <button id="prev-copy-btn-${responseNumber}" class="prev-copy-btn" style="margin-left:auto; padding: 8px 16px; background: #4b9ac7; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; transition: background-color 0.3s ease;" onmouseover="this.style.background='#e25b6b'" onmouseout="this.style.background='#4b9ac7'">📋 Seç ve Kopyala #${responseNumber}</button>
                        </div>
                    `;
                    
                    // Copy butonunu güncelle
                    const copyBtn = document.getElementById(`prev-copy-btn-${responseNumber}`);
                    if (copyBtn) {
                        copyBtn.onclick = async () => {
                            // Şablon olarak kaydetme işaretliyse önce kaydet
                            const saveChk = document.getElementById(`prev-save-${responseNumber}`);
                            const catSel = document.getElementById(`prev-category-${responseNumber}`);
                            const editor = document.getElementById(`prev-editor-${responseNumber}`);
                            const editedText = editor ? editor.value : response.response_text;
                            if (saveChk && saveChk.checked) {
                                if (!catSel || !catSel.value) {
                                    templateSaveManager.showToast('❌ Lütfen kategori seçin', 'error');
                                    return;
                                }
                                const isSMS = response.is_sms || false;
                                console.log('[ŞABLON KAYDET]', { text: editedText, category: catSel.value, is_sms: isSMS });
                                await templateSaveManager.saveTemplate(editedText, parseInt(catSel.value), isSMS);
                            }
                            // Tüm mini şablon alanlarını gizle
                            const prevSaves = document.querySelectorAll('.prev-template-save');
                            prevSaves.forEach(n => n.style.display = 'none');
                            // Kopyalama: düzenlenmiş metni ana alana gönder ve kilitle
                            if (editor) {
                                editor.setAttribute('readonly', 'true');
                                editor.style.background = '#f5f5f5';
                            }
                            await responseManager.copyPreviousResponse(response.id, editedText);
                        };
                    }

                    // Checkbox değişimi: kategori alanlarını aç/kapa ve kategorileri yükle
                    const saveChk = document.getElementById(`prev-save-${responseNumber}`);
                    const catSel = document.getElementById(`prev-category-${responseNumber}`);
                    const newBtn = document.getElementById(`prev-newcat-btn-${responseNumber}`);
                    const newGrp = document.getElementById(`prev-newcat-group-${responseNumber}`);
                    const newInp = document.getElementById(`prev-newcat-${responseNumber}`);
                    const createBtn = document.getElementById(`prev-createcat-${responseNumber}`);
                    const cancelBtn = document.getElementById(`prev-cancelcat-${responseNumber}`);

                    if (saveChk) {
                        saveChk.addEventListener('change', async () => {
                            if (saveChk.checked) {
                                if (catSel) catSel.style.display = 'inline-block';
                                if (newBtn) newBtn.style.display = 'inline-block';
                                // Kategorileri doldur
                                const cats = await templateSaveManager.loadCategories();
                                if (catSel) {
                                    catSel.innerHTML = '<option value="">Kategori seçiniz</option>';
                                    (cats || []).forEach(c => {
                                        const opt = document.createElement('option');
                                        opt.value = c.id; opt.textContent = c.name; catSel.appendChild(opt);
                                    });
                                }
                            } else {
                                if (catSel) catSel.style.display = 'none';
                                if (newBtn) newBtn.style.display = 'none';
                                if (newGrp) newGrp.style.display = 'none';
                            }
                        });
                    }

                    if (newBtn && newGrp && newInp && createBtn && cancelBtn) {
                        newBtn.addEventListener('click', () => {
                            newGrp.style.display = 'flex';
                            newBtn.style.display = 'none';
                        });
                        cancelBtn.addEventListener('click', () => {
                            newGrp.style.display = 'none';
                            newBtn.style.display = 'inline-block';
                        });
                        createBtn.addEventListener('click', async () => {
                            if (newInp.value.trim()) {
                                const cat = await templateSaveManager.createCategory(newInp.value.trim());
                                if (cat && catSel) {
                                    const opt = document.createElement('option');
                                    opt.value = cat.id; opt.textContent = cat.name; catSel.appendChild(opt);
                                    catSel.value = cat.id;
                                }
                                newGrp.style.display = 'none';
                                newBtn.style.display = 'inline-block';
                            }
                        });
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
        const generateSmsBtn = document.getElementById('generate-sms-btn');
        const newRequestBtn = document.getElementById('new-request-btn');
        const mainCopyBtn = document.getElementById('main-copy-btn');
        
        if (generateBtn && newRequestBtn) {
            // Gradio app.py mantığı:
            // generate_visible = user_state['state'] == 'draft' and user_state['yanit_sayisi'] < 5
            // new_request_visible = user_state['state'] == 'finalized' or user_state['yanit_sayisi'] >= 5
            
            const generateVisible = this.state === 'draft' && this.yanitSayisi < 5;
            
            // Şablon kaydetme alanı: sadece ana yanıtta gerçek içerik varsa ve kopyalama yapılmadan önce görünür
            const mainRespEl = document.getElementById('main-response');
            const text = (mainRespEl?.textContent || '').trim();
            const hasContent = text !== '' && text !== 'Henüz yanıt üretilmedi...';
            if (hasContent && this.state === 'draft') {
                templateSaveManager.showTemplateSaveSection();
            } else {
                templateSaveManager.hideTemplateSaveSection();
            }
            const newRequestVisible = this.state === 'finalized' || this.yanitSayisi >= 5;
            
            generateBtn.style.display = generateVisible ? 'block' : 'none';
            // SMS Yanıt Üret butonu da aynı mantıkla görünür/gizli
            if (generateSmsBtn) {
                generateSmsBtn.style.display = generateVisible ? 'block' : 'none';
            }
            newRequestBtn.style.display = newRequestVisible ? 'block' : 'none';
            
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
    
    // Textbox'ları boşalt (varsayılan değerler kaldırıldı)
    clearTextboxValues() {
        const requestInput = document.getElementById('original-text');
        const responseInput = document.getElementById('custom-input');
        
        if (requestInput) {
            requestInput.value = '';
        }
        
        if (responseInput) {
            responseInput.value = '';
        }
        
        console.log('✅ Textbox\'lar temizlendi');
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
        
        // Navigation events
        const homeBtn = document.getElementById('home-btn');
        const templatesBtn = document.getElementById('templates-btn');
        const homeBtnTemplates = document.getElementById('home-btn-templates');
        const templatesBtnTemplates = document.getElementById('templates-btn-templates');
        const goToHomeBtn = document.getElementById('go-to-home-btn');
        const logoutBtnTemplates = document.getElementById('logout-btn-templates');
        
        if (homeBtn) {
            homeBtn.addEventListener('click', () => navigationManager.showHomeScreen());
        }
        
        if (templatesBtn) {
            templatesBtn.addEventListener('click', async () => await navigationManager.showTemplatesScreen());
        }
        
        if (homeBtnTemplates) {
            homeBtnTemplates.addEventListener('click', () => navigationManager.showHomeScreen());
        }
        
        if (templatesBtnTemplates) {
            templatesBtnTemplates.addEventListener('click', async () => await navigationManager.showTemplatesScreen());
        }
        
        if (goToHomeBtn) {
            goToHomeBtn.addEventListener('click', () => navigationManager.showHomeScreen());
        }
        
        if (logoutBtnTemplates) {
            logoutBtnTemplates.addEventListener('click', async () => await authManager.logout());
        }
        
        // Modal event listeners
        const useModal = document.getElementById('use-template-modal');
        const deleteModal = document.getElementById('delete-template-modal');
        const closeUseModal = document.getElementById('close-use-modal');
        const closeDeleteModal = document.getElementById('close-delete-modal');
        const useToRequest = document.getElementById('use-to-request');
        const useToResponse = document.getElementById('use-to-response');
        const useToClipboard = document.getElementById('use-to-clipboard');
        const confirmDelete = document.getElementById('confirm-delete');
        const cancelDelete = document.getElementById('cancel-delete');
        const goToHomeBtnCategories = document.getElementById('go-to-home-btn-categories');
        
        // Use modal events
        if (closeUseModal) {
            closeUseModal.addEventListener('click', () => templatesManager.hideUseModal());
        }
        
        if (useToRequest) {
            useToRequest.addEventListener('click', () => {
                templatesManager.useTemplate(templatesManager.selectedTemplate, 'request');
                templatesManager.hideUseModal();
            });
        }
        
        if (useToResponse) {
            useToResponse.addEventListener('click', () => {
                templatesManager.useTemplate(templatesManager.selectedTemplate, 'response');
                templatesManager.hideUseModal();
            });
        }
        
        if (useToClipboard) {
            useToClipboard.addEventListener('click', () => {
                templatesManager.useTemplate(templatesManager.selectedTemplate, 'clipboard');
                templatesManager.hideUseModal();
            });
        }
        
        // Delete modal events
        if (closeDeleteModal) {
            closeDeleteModal.addEventListener('click', () => templatesManager.hideDeleteModal());
        }
        
        if (confirmDelete) {
            confirmDelete.addEventListener('click', () => {
                templatesManager.confirmDelete();
            });
        }
        
        if (cancelDelete) {
            cancelDelete.addEventListener('click', () => templatesManager.hideDeleteModal());
        }

        // Modal kapatma: ESC tuşu ve dışarı tıklama
        if (deleteModal) {
            deleteModal.addEventListener('click', (e) => {
                if (e.target === deleteModal) {
                    templatesManager.hideDeleteModal();
                }
            });
            
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && !deleteModal.classList.contains('hidden')) {
                    templatesManager.hideDeleteModal();
                }
            });
        }
        
        // Go to home from categories empty state
        if (goToHomeBtnCategories) {
            goToHomeBtnCategories.addEventListener('click', () => navigationManager.showHomeScreen());
        }
        
        // Modal backdrop clicks
        if (useModal) {
            useModal.addEventListener('click', (e) => {
                if (e.target === useModal) {
                    templatesManager.hideUseModal();
                }
            });
        }
        
        if (deleteModal) {
            deleteModal.addEventListener('click', (e) => {
                if (e.target === deleteModal) {
                    templatesManager.hideDeleteModal();
                }
            });
        }
        
        // AI Response events
        if (ui.elements.generateBtn) {
            ui.elements.generateBtn.addEventListener('click', () => responseManager.generateResponse(false));
        }
        
        // SMS Yanıt Üret button
        const generateSmsBtn = document.getElementById('generate-sms-btn');
        if (generateSmsBtn) {
            generateSmsBtn.addEventListener('click', () => responseManager.generateResponse(true));
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
const navigationManager = new NavigationManager();
const templatesManager = new TemplatesManager();
const templateSaveManager = new TemplateSaveManager();


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
        
        // Textbox'ları temizle
        responseManager.clearTextboxValues();
        
        // Template save manager event listener'larını başlat
        templateSaveManager.setupEventListeners();
        
        // Şablon kaydetme bölümünü başlangıçta gizle
        templateSaveManager.hideTemplateSaveSection();
        
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
        
        // Magic link kontrolü checkBackendSession içinde yapılıyor
        // Burada sadece normal init yap
        await authManager.init();
        
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
    console.log('=== FULL AUTH STATE DEBUG ===');
    console.log('appState type:', typeof authManager.appState);
    console.log('appState:', JSON.stringify(authManager.appState, null, 2));
    
    console.log('Authentication properties:');
    console.log('- authenticated:', authManager.appState.authenticated, typeof authManager.appState.authenticated);
    console.log('- userEmail:', authManager.appState.userEmail, typeof authManager.appState.userEmail);
    console.log('- accessToken:', authManager.appState.accessToken ? 'present' : 'missing', typeof authManager.appState.accessToken);
    console.log('- authToken:', authManager.appState.authToken ? 'present' : 'missing', typeof authManager.appState.authToken);
    
    console.log('localStorage items:', {
        authenticated: localStorage.getItem('authenticated'),
        accessToken: localStorage.getItem('accessToken') ? 'present' : 'missing',
        authToken: localStorage.getItem('authToken') ? 'present' : 'missing',
        userEmail: localStorage.getItem('userEmail'),
        userProfile: localStorage.getItem('userProfile') ? 'present' : 'missing'
    });
    
    const authResult = authManager.checkAuthenticationState();
    console.log('checkAuthenticationState() result:', authResult, typeof authResult);
    console.log('=============================');
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
