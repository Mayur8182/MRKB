/**
 * Session Management for Fire NOC Application
 * Handles session refresh, timeout detection, and automatic logout
 */

class SessionManager {
    constructor() {
        this.refreshInterval = 5 * 60 * 1000; // 5 minutes
        this.warningTime = 2 * 60 * 1000; // 2 minutes before session expires
        this.sessionTimeout = 7 * 24 * 60 * 60 * 1000; // 7 days
        this.lastActivity = Date.now();
        this.refreshTimer = null;
        this.warningTimer = null;
        this.isWarningShown = false;
        
        this.init();
    }

    init() {
        // Start session refresh timer
        this.startRefreshTimer();
        
        // Track user activity
        this.trackActivity();
        
        // Handle page visibility changes
        this.handleVisibilityChange();
        
        // Add refresh buttons to dashboards
        this.addRefreshButtons();
    }

    startRefreshTimer() {
        this.refreshTimer = setInterval(() => {
            this.refreshSession();
        }, this.refreshInterval);
    }

    async refreshSession() {
        try {
            const response = await fetch('/api/refresh-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    console.log('Session refreshed successfully');
                    this.lastActivity = Date.now();
                    this.hideWarning();
                } else {
                    console.warn('Session refresh failed:', data.error);
                    this.handleSessionExpired();
                }
            } else if (response.status === 401) {
                this.handleSessionExpired();
            }
        } catch (error) {
            console.error('Session refresh error:', error);
            // Don't redirect on network errors, just log them
        }
    }

    async checkSessionStatus() {
        try {
            const response = await fetch('/api/session-status', {
                method: 'GET',
                credentials: 'same-origin'
            });

            if (response.ok) {
                const data = await response.json();
                return data.authenticated;
            } else {
                return false;
            }
        } catch (error) {
            console.error('Session status check error:', error);
            return false;
        }
    }

    trackActivity() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        events.forEach(event => {
            document.addEventListener(event, () => {
                this.lastActivity = Date.now();
                this.hideWarning();
            }, true);
        });
    }

    handleVisibilityChange() {
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // Page became visible, check session status
                this.checkSessionStatus().then(isAuthenticated => {
                    if (!isAuthenticated) {
                        this.handleSessionExpired();
                    }
                });
            }
        });
    }

    showWarning() {
        if (this.isWarningShown) return;
        
        this.isWarningShown = true;
        
        // Create warning modal
        const modal = document.createElement('div');
        modal.id = 'session-warning-modal';
        modal.className = 'modal fade show';
        modal.style.display = 'block';
        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-warning">
                        <h5 class="modal-title">⚠️ Session Expiring Soon</h5>
                    </div>
                    <div class="modal-body">
                        <p>Your session will expire in 2 minutes due to inactivity.</p>
                        <p>Click "Stay Logged In" to continue your session.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="sessionManager.logout()">Logout</button>
                        <button type="button" class="btn btn-primary" onclick="sessionManager.extendSession()">Stay Logged In</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    hideWarning() {
        const modal = document.getElementById('session-warning-modal');
        if (modal) {
            modal.remove();
            this.isWarningShown = false;
        }
    }

    async extendSession() {
        await this.refreshSession();
        this.hideWarning();
    }

    handleSessionExpired() {
        // Clear timers
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        if (this.warningTimer) {
            clearTimeout(this.warningTimer);
        }

        // Show expiration message
        alert('Your session has expired. Please log in again.');
        
        // Redirect to login
        window.location.href = '/login';
    }

    logout() {
        window.location.href = '/logout';
    }

    addRefreshButtons() {
        // Add refresh buttons to dashboard pages
        const dashboardContainers = document.querySelectorAll('.dashboard-container, .card-header, .page-header');
        
        dashboardContainers.forEach(container => {
            if (container.querySelector('.refresh-btn')) return; // Already has refresh button
            
            const refreshBtn = document.createElement('button');
            refreshBtn.className = 'btn btn-outline-primary btn-sm refresh-btn ms-2';
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
            refreshBtn.onclick = () => this.refreshPage();
            
            container.appendChild(refreshBtn);
        });
    }

    refreshPage() {
        // Refresh current page data without full reload
        if (typeof loadDashboardData === 'function') {
            loadDashboardData();
        } else if (typeof loadNotifications === 'function') {
            loadNotifications();
        } else if (typeof loadRecentActivities === 'function') {
            loadRecentActivities();
        } else {
            // Fallback to page reload
            window.location.reload();
        }
    }

    // Handle API errors globally
    handleApiError(response) {
        if (response.status === 401) {
            this.handleSessionExpired();
            return true;
        }
        return false;
    }
}

// Initialize session manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.sessionManager = new SessionManager();
});

// Global fetch wrapper to handle session errors
const originalFetch = window.fetch;
window.fetch = function(...args) {
    return originalFetch.apply(this, args).then(response => {
        if (window.sessionManager && response.status === 401) {
            window.sessionManager.handleSessionExpired();
        }
        return response;
    });
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionManager;
}
