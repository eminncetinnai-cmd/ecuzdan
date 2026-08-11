/**
 * E-CÜZDAN v15.0 - Lazy Loading JavaScript
 * Lazy loading for images, charts, and components
 */

// Image Lazy Loading
export function initLazyImages() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    }, {
        rootMargin: '50px 0px',
        threshold: 0.01
    });
    
    images.forEach(img => {
        img.classList.add('lazy');
        imageObserver.observe(img);
    });
}

// Chart Lazy Loading
export function initLazyCharts() {
    const chartContainers = document.querySelectorAll('[data-lazy-chart]');
    
    const chartObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const container = entry.target;
                const chartId = container.dataset.lazyChart;
                const chartType = container.dataset.chartType;
                const chartData = JSON.parse(container.dataset.chartData || '{}');
                
                // Initialize chart (would call appropriate chart function)
                if (window.ECuzdanCharts && window.ECuzdanCharts[chartType]) {
                    const ctx = document.getElementById(chartId);
                    if (ctx) {
                        window.ECuzdanCharts[chartType](ctx, chartData);
                    }
                }
                
                container.removeAttribute('data-lazy-chart');
                observer.unobserve(container);
            }
        });
    }, {
        rootMargin: '100px 0px',
        threshold: 0.1
    });
    
    chartContainers.forEach(container => {
        chartObserver.observe(container);
    });
}

// Component Lazy Loading
export function initLazyComponents() {
    const components = document.querySelectorAll('[data-lazy-component]');
    
    const componentObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const component = entry.target;
                const componentUrl = component.dataset.lazyComponent;
                
                // Load component content
                fetch(componentUrl)
                    .then(response => response.text())
                    .then(html => {
                        component.innerHTML = html;
                        component.removeAttribute('data-lazy-component');
                        
                        // Re-initialize any scripts in the loaded content
                        const scripts = component.querySelectorAll('script');
                        scripts.forEach(script => {
                            const newScript = document.createElement('script');
                            newScript.textContent = script.textContent;
                            component.appendChild(newScript);
                            script.remove();
                        });
                    })
                    .catch(error => {
                        console.error('Failed to load component:', error);
                        component.innerHTML = '<p class="text-red-500">Yükleme hatası</p>';
                    });
                
                observer.unobserve(component);
            }
        });
    }, {
        rootMargin: '50px 0px',
        threshold: 0.1
    });
    
    components.forEach(component => {
        componentObserver.observe(component);
    });
}

// Data Lazy Loading (for tables, lists)
export function initLazyData(loadMoreCallback, containerId, initialItems = 20, itemsPerLoad = 20) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    let loadedItems = initialItems;
    let isLoading = false;
    let hasMore = true;
    
    // Load more button
    const loadMoreBtn = document.createElement('button');
    loadMoreBtn.className = 'w-full mt-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition';
    loadMoreBtn.textContent = 'Daha Fazla Göster';
    
    loadMoreBtn.addEventListener('click', async () => {
        if (isLoading || !hasMore) return;
        
        isLoading = true;
        loadMoreBtn.textContent = 'Yükleniyor...';
        loadMoreBtn.disabled = true;
        
        try {
            const newItems = await loadMoreCallback(loadedItems, itemsPerLoad);
            
            if (newItems && newItems.length > 0) {
                // Append new items to container
                newItems.forEach(item => {
                    const itemElement = document.createElement('div');
                    itemElement.innerHTML = item;
                    container.appendChild(itemElement);
                });
                
                loadedItems += newItems.length;
                
                if (newItems.length < itemsPerLoad) {
                    hasMore = false;
                    loadMoreBtn.textContent = 'Tüm öğeler yüklendi';
                    loadMoreBtn.disabled = true;
                } else {
                    loadMoreBtn.textContent = 'Daha Fazla Göster';
                    loadMoreBtn.disabled = false;
                }
            } else {
                hasMore = false;
                loadMoreBtn.textContent = 'Tüm öğeler yüklendi';
                loadMoreBtn.disabled = true;
            }
        } catch (error) {
            console.error('Failed to load more items:', error);
            loadMoreBtn.textContent = 'Yükleme Hatası';
            loadMoreBtn.disabled = false;
        }
        
        isLoading = false;
    });
    
    container.parentNode.insertBefore(loadMoreBtn, container.nextSibling);
}

// Background Image Lazy Loading
export function initLazyBackgrounds() {
    const elements = document.querySelectorAll('[data-bg-src]');
    
    const bgObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                element.style.backgroundImage = `url(${element.dataset.bgSrc})`;
                element.removeAttribute('data-bg-src');
                observer.unobserve(element);
            }
        });
    }, {
        rootMargin: '50px 0px',
        threshold: 0.1
    });
    
    elements.forEach(element => {
        bgObserver.observe(element);
    });
}

// Initialize All Lazy Loading
export function initAllLazyLoading() {
    initLazyImages();
    initLazyCharts();
    initLazyComponents();
    initLazyBackgrounds();
}

// Export for global access
window.ECuzdanLazyLoad = {
    initLazyImages,
    initLazyCharts,
    initLazyComponents,
    initLazyData,
    initLazyBackgrounds,
    initAllLazyLoading
};
