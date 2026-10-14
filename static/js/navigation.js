/**
 * E-CÜZDAN v15.0 - Navigation JavaScript
 * Navigation optimization and search functionality
 */

// Navigation Search
export function initNavigationSearch(searchInputId, navContainerId) {
    const searchInput = document.getElementById(searchInputId);
    const navContainer = document.getElementById(navContainerId);

    if (!searchInput || !navContainer) return;

    const sectionBlocks = Array.from(navContainer.querySelectorAll('.nav-section-title')).map(section => {
        const items = [];
        let sibling = section.nextElementSibling;

        while (sibling && !sibling.classList.contains('nav-section-title')) {
            if (sibling.classList.contains('nav-link')) {
                items.push(sibling);
            }
            sibling = sibling.nextElementSibling;
        }

        return { section, items };
    });

    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();

        sectionBlocks.forEach(({ section, items }) => {
            let anyVisible = false;

            items.forEach(link => {
                const text = link.textContent.toLowerCase();
                const visible = text.includes(searchTerm);

                link.style.display = visible ? 'flex' : 'none';
                anyVisible = anyVisible || visible;
            });

            section.style.display = anyVisible ? 'block' : 'none';
        });
    });
}

// Breadcrumb Generation
export function generateBreadcrumbs() {
    const path = window.location.pathname;
    const breadcrumbs = [];
    
    // Home
    breadcrumbs.push({ text: 'Ana Sayfa', url: '/' });
    
    // Parse path
    const segments = path.split('/').filter(Boolean);
    const pathMap = {
        'transactions': 'İşlemler',
        'plans': 'Düzenli İşlemler',
        'monthly_dashboard': 'Aylık Dashboard',
        'payment_calendar': 'Ödeme Takvimi',
        'reconciliation': 'Mutabakat',
        'assets': 'Varlık Yönetimi',
        'assets_management': 'Varlık Yönetimi',
        'assets_view': 'Varlık Görünümü',
        'investment_performance': 'Yatırım Performansı',
        'analysis': 'Finansal Sağlık',
        'financial_freedom': 'Finansal Özgürlük',
        'strategy': 'Strateji Paneli',
        'financial_dashboard': 'Piyasa Analizi',
        'logbook': 'Yatırım Günlüğü',
        'central-bank-reserves': 'Merkez Bankası Rezervleri',
        'global-ratios': 'Küresel Rasyolar',
        'profile': 'Yatırımcı Profili',
        'notifications': 'Bildirimler',
        'categories': 'Kategoriler',
        'settings': 'Ayarlar',
        'user_guide': 'Kullanıcı Rehberi',
        'financial_education': 'Finansal Eğitim',
        'monitoring': 'İzleme',
        'storage-health': 'Depolama Sağlığı',
        'admin': 'Yönetim Paneli'
    };
    
    let currentPath = '';
    segments.forEach((segment, index) => {
        currentPath += '/' + segment;
        const text = pathMap[segment] || segment;
        const isLast = index === segments.length - 1;
        
        breadcrumbs.push({
            text: text,
            url: isLast ? null : currentPath
        });
    });
    
    return breadcrumbs;
}

// Render Breadcrumbs
export function renderBreadcrumbs(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const breadcrumbs = generateBreadcrumbs();

    container.innerHTML = `
        <nav class="flex items-center gap-2 text-xs" aria-label="Breadcrumb">
            ${breadcrumbs.map((crumb, index) => {
                const isLast = index === breadcrumbs.length - 1;
                const separator = index > 0 ? `<span class="text-slate-400">/</span>` : '';

                return `
                    ${separator}
                    ${crumb.url 
                        ? `<a href="${crumb.url}" class="text-slate-500 hover:text-slate-700 transition">${crumb.text}</a>`
                        : `<span class="text-slate-700 font-semibold">${crumb.text}</span>`
                    }
                `;
            }).join('')}
        </nav>
    `;
}

// Recently Visited Pages
export function addToRecentlyVisited(pageTitle, pageUrl, maxItems = 5) {
    const recent = getRecentlyVisited();

    // Remove if already exists
    const filtered = recent.filter(item => item.url !== pageUrl);

    // Add to beginning
    filtered.unshift({
        title: pageTitle,
        url: pageUrl,
        timestamp: Date.now()
    });

    // Keep only max items
    const trimmed = filtered.slice(0, maxItems);

    if (window.saveToLocalStorage) {
        window.saveToLocalStorage('recently_visited', trimmed);
    }
}

export function getRecentlyVisited() {
    if (window.getFromLocalStorage) {
        return window.getFromLocalStorage('recently_visited', []);
    }

    return [];
}

export function renderRecentlyVisited(containerId, maxItems = 5) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const recent = getRecentlyVisited().slice(0, maxItems);
    
    if (recent.length === 0) {
        container.innerHTML = '<p class="text-xs text-slate-400">Henüz ziyaret edilen sayfa yok</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="space-y-1">
            ${recent.map(item => `
                <a href="${item.url}" class="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-100 transition">
                    <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span class="text-xs text-slate-600">${item.title}</span>
                </a>
            `).join('')}
        </div>
    `;
}

// Quick Navigation Shortcuts
export function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        const activeTag = document.activeElement ? document.activeElement.tagName : '';
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(activeTag) || (document.activeElement && document.activeElement.isContentEditable)) {
            return;
        }

        // Alt + H - Home
        if (e.altKey && e.key === 'h') {
            e.preventDefault();
            window.location.href = '/';
        }
        
        // Alt + T - Transactions
        if (e.altKey && e.key === 't') {
            e.preventDefault();
            window.location.href = '/transactions';
        }
        
        // Alt + P - Plans
        if (e.altKey && e.key === 'p') {
            e.preventDefault();
            window.location.href = '/plans';
        }
        
        // Alt + A - Assets
        if (e.altKey && e.key === 'a') {
            e.preventDefault();
            window.location.href = '/assets';
        }
        
        // Alt + S - Settings
        if (e.altKey && e.key === 's') {
            e.preventDefault();
            window.location.href = '/settings';
        }
        
        // Alt + ? - Help
        if (e.altKey && e.key === '?') {
            e.preventDefault();
            window.location.href = '/user_guide';
        }
    });
}

// Navigation Grouping (Collapsible Sections)
export function initCollapsibleNavigation() {
    const sectionTitles = document.querySelectorAll('.nav-section-title');
    
    sectionTitles.forEach(title => {
        // Skip sections already managed by layout-shell.js (which use data-target + .collapsible)
        if (title.classList.contains('collapsible') || title.hasAttribute('data-target') || title.dataset.collapsibleBound === 'true') {
            return;
        }
        title.dataset.collapsibleBound = 'true';
        title.style.cursor = 'pointer';
        title.addEventListener('click', () => {
            const nextElement = title.nextElementSibling;
            if (nextElement) {
                const isHidden = nextElement.style.display === 'none';
                nextElement.style.display = isHidden ? 'block' : 'none';
                title.classList.toggle('collapsed');
            }
        });
    });
}

// Export for global access
window.ECuzdanNavigation = {
    initNavigationSearch,
    generateBreadcrumbs,
    renderBreadcrumbs,
    addToRecentlyVisited,
    getRecentlyVisited,
    renderRecentlyVisited,
    initKeyboardShortcuts,
    initCollapsibleNavigation
};
