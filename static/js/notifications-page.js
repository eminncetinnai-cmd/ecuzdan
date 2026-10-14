/* Notifications Page JavaScript */

(function() {
    'use strict';

    var i18n = window.ECuzdanI18n || {};
    function t(key, vars) {
        var value = i18n[key] || key;
        Object.keys(vars || {}).forEach(function(name) {
            value = value.replace('{' + name + '}', String(vars[name]));
        });
        return value;
    }

    var currentPage = 1;
    var perPage = 20;
    var allNotifications = [];
    var filteredNotifications = [];

    function csrf() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    function post(url, data) {
        var body = new URLSearchParams();
        body.append('csrf_token', csrf());
        if (data) {
            Object.keys(data).forEach(function(key) {
                body.append(key, data[key]);
            });
        }
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: body
        }).then(function(r) { return r.json(); });
    }

    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function loadNotifications() {
        var list = document.getElementById('notificationsList');
        list.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div><p>' + escapeHtml(t('notification_loading')) + '</p></div>';

        fetch(ECuzdanEndpoints.notifications.all)
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (!d || !d.success) {
                    list.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg></div><div class="empty-state-title">' + escapeHtml(t('notifications_error_title')) + '</div><div class="empty-state-text">' + escapeHtml(t('notifications_load_failed')) + '</div></div>';
                    return;
                }
            ECuzdanApi.dto.notifications(d);
                allNotifications = d.items || [];
                applyFilters();
                updateStats(d.items || []);
            })
            .catch(function() {
                list.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg></div><div class="empty-state-title">' + escapeHtml(t('notifications_error_title')) + '</div><div class="empty-state-text">' + escapeHtml(t('notifications_load_failed')) + '</div></div>';
            });
    }

    function updateStats(notifications) {
        var total = notifications.length;
        var unread = notifications.filter(function(n) { return !n.is_read; }).length;
        var danger = notifications.filter(function(n) { return n.severity === 'danger'; }).length;
        var warning = notifications.filter(function(n) { return n.severity === 'warning'; }).length;

        document.getElementById('statTotal').textContent = total;
        document.getElementById('statUnread').textContent = unread;
        document.getElementById('statDanger').textContent = danger;
        document.getElementById('statWarning').textContent = warning;
    }

    function applyFilters() {
        var status = document.getElementById('filterStatus').value;
        var severity = document.getElementById('filterSeverity').value;
        var category = document.getElementById('filterCategory').value;
        var search = document.getElementById('searchInput').value.toLowerCase();

        filteredNotifications = allNotifications.filter(function(n) {
            if (status === 'unread' && n.is_read) return false;
            if (status === 'read' && !n.is_read) return false;
            if (severity !== 'all' && n.severity !== severity) return false;
            if (category !== 'all' && n.category !== category) return false;
            if (search && !n.title.toLowerCase().includes(search) && !n.body.toLowerCase().includes(search)) return false;
            return true;
        });

        currentPage = 1;
        renderNotifications();
    }

    function renderNotifications() {
        var list = document.getElementById('notificationsList');
        var start = (currentPage - 1) * perPage;
        var end = start + perPage;
        var pageItems = filteredNotifications.slice(start, end);

        if (pageItems.length === 0) {
            list.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg></div><div class="empty-state-title">' + escapeHtml(t('notifications_empty_title')) + '</div><div class="empty-state-text">' + escapeHtml(t('notifications_empty_text')) + '</div></div>';
            document.getElementById('paginationBar').style.display = 'none';
            return;
        }

        list.innerHTML = pageItems.map(function(n) {
            var severityClass = n.severity || 'info';
            var severityLabel = severityClass === 'danger' ? t('notifications_critical') : severityClass === 'warning' ? t('notifications_warning') : t('notifications_info');
            return '<div class="notification-item' + (n.is_read ? ' is-read' : '') + '" data-id="' + n.id + '">' +
                '<div class="notification-dot ' + severityClass + '"></div>' +
                '<div class="notification-body">' +
                    '<div class="notification-title">' + escapeHtml(n.title) + '</div>' +
                    (n.body ? '<div class="notification-text">' + escapeHtml(n.body) + '</div>' : '') +
                    '<div class="notification-meta">' +
                        '<span class="notification-badge ' + severityClass + '">' + severityLabel + '</span>' +
                        '<span>' + escapeHtml(n.created_at) + '</span>' +
                    '</div>' +
                '</div>' +
                '<div class="notification-actions">' +
                    '<button type="button" class="notification-action-btn" onclick="markRead(' + n.id + ', event)" title="' + escapeHtml(t('notifications_mark_read')) + '">' +
                        '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"></path></svg>' +
                    '</button>' +
                    '<button type="button" class="notification-action-btn" onclick="deleteNotification(' + n.id + ', event)" title="' + escapeHtml(t('notifications_delete')) + '">' +
                        '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>' +
                    '</button>' +
                '</div>' +
            '</div>';
        }).join('');

        // Add click handlers for notification items
        list.querySelectorAll('.notification-item').forEach(function(el) {
            el.addEventListener('click', function(e) {
                if (e.target.closest('.notification-action-btn')) return;
                var id = el.dataset.id;
                var item = allNotifications.find(function(x) { return String(x.id) === id; });
                if (item && item.link) {
                    markRead(id, e);
                    setTimeout(function() { window.location.href = item.link; }, 100);
                }
            });
        });

        updatePagination();
    }

    function updatePagination() {
        var totalPages = Math.ceil(filteredNotifications.length / perPage);
        var paginationBar = document.getElementById('paginationBar');
        
        if (totalPages <= 1) {
            paginationBar.style.display = 'none';
            return;
        }

        paginationBar.style.display = 'flex';
        document.getElementById('paginationInfo').textContent = t('notifications_pagination_total', { count: filteredNotifications.length });
        document.getElementById('paginationPages').textContent = currentPage + ' / ' + totalPages;
        document.getElementById('prevBtn').disabled = currentPage === 1;
        document.getElementById('nextBtn').disabled = currentPage === totalPages;
    }

    function prevPage() {
        if (currentPage > 1) {
            currentPage--;
            renderNotifications();
        }
    }

    function nextPage() {
        var totalPages = Math.ceil(filteredNotifications.length / perPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderNotifications();
        }
    }

    function markRead(id, event) {
        if (event) event.stopPropagation();
        post(ECuzdanEndpoints.notifications.markRead(id))
            .then(function(d) {
                if (d && d.success) {
                    var item = allNotifications.find(function(x) { return String(x.id) === String(id); });
                    if (item) item.is_read = true;
                    applyFilters();
                    // Update header badge
                    var badge = document.getElementById('notifBadge');
                    if (badge && d.unread !== undefined) {
                        badge.textContent = d.unread > 99 ? '99+' : String(d.unread);
                        badge.style.display = d.unread > 0 ? 'flex' : 'none';
                    }
                }
            });
    }

    function deleteNotification(id, event) {
        if (event) event.stopPropagation();
        if (!confirm(t('notifications_delete_confirm'))) return;
        
        post(ECuzdanEndpoints.notifications.delete(id))
            .then(function(d) {
                if (d && d.success) {
                    allNotifications = allNotifications.filter(function(x) { return String(x.id) !== String(id); });
                    applyFilters();
                }
            })
            .catch(function() {
                alert(t('notifications_delete_failed'));
            });
    }

    function markAllRead() {
        post(ECuzdanEndpoints.notifications.markAllRead)
            .then(function(d) {
                if (d && d.success) {
                    allNotifications.forEach(function(n) { n.is_read = true; });
                    applyFilters();
                    // Update header badge
                    var badge = document.getElementById('notifBadge');
                    if (badge) {
                        badge.textContent = '0';
                        badge.style.display = 'none';
                    }
                }
            });
    }

    function deleteAllRead() {
        var readCount = allNotifications.filter(function(n) { return n.is_read; }).length;
        if (readCount === 0) {
            alert(t('notifications_no_read'));
            return;
        }
        if (!confirm(t('notifications_delete_read_confirm', { count: readCount }))) return;
        
        post(ECuzdanEndpoints.notifications.deleteRead)
            .then(function(d) {
                if (d && d.success) {
                    allNotifications = allNotifications.filter(function(n) { return !n.is_read; });
                    applyFilters();
                }
            })
            .catch(function() {
                alert(t('notifications_delete_all_failed'));
            });
    }

    function resetNotificationFilters() {
        var s = document.getElementById('filterStatus');
        var sev = document.getElementById('filterSeverity');
        var cat = document.getElementById('filterCategory');
        var search = document.getElementById('searchInput');
        if (s) s.value = 'all';
        if (sev) sev.value = 'all';
        if (cat) cat.value = 'all';
        if (search) search.value = '';
        applyFilters();
    }

    // Expose functions to global scope
    window.markRead = markRead;
    window.deleteNotification = deleteNotification;
    window.markAllRead = markAllRead;
    window.deleteAllRead = deleteAllRead;
    window.applyFilters = applyFilters;
    window.resetNotificationFilters = resetNotificationFilters;
    window.prevPage = prevPage;
    window.nextPage = nextPage;

    // ESC key handling for search input
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            var search = document.getElementById('searchInput');
            if (document.activeElement === search && search.value) {
                search.value = '';
                applyFilters();
            }
        }
    });

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadNotifications);
    } else {
        loadNotifications();
    }
})();
