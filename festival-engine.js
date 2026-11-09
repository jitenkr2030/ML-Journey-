// =============================================
// ReconcileAI - Festival Auto-Theme Engine v1.0
// =============================================
// Auto-detects today's date and applies festival themes.
// Zero config needed - just include this script!
// Safe: wrapped in try-catch, never breaks the page.

(function() {
  'use strict';

  function pad(n) { return n < 10 ? '0' + n : '' + n; }

  function findFestival(date) {
    if (!window.FESTIVALS) return null;

    var year = date.getFullYear();
    var todayStart = new Date(year, date.getMonth(), date.getDate());
    var best = null;
    var bestPriority = 0;

    for (var id in window.FESTIVALS) {
      var f = window.FESTIVALS[id];
      var dateStr = null;

      if (f.fixed) {
        dateStr = f.fixed;
      } else if (f.dates && f.dates[String(year)]) {
        dateStr = f.dates[String(year)];
      }

      if (!dateStr) continue;

      var parts = dateStr.split('-');
      var m = parseInt(parts[0], 10) - 1;
      var d = parseInt(parts[1], 10);

      var festStart = new Date(year, m, d);
      var festEnd = new Date(year, m, d + (f.duration || 1) - 1);

      if (todayStart >= festStart && todayStart <= festEnd) {
        var p = f.priority || 5;
        if (p > bestPriority) {
          best = { id: id, config: f };
          bestPriority = p;
        }
      }
    }
    return best;
  }

  function applyTheme(f) {
    var root = document.documentElement;
    var c = f.config.colors;
    root.style.setProperty('--fest-primary', c.primary);
    root.style.setProperty('--fest-secondary', c.secondary);
    root.style.setProperty('--fest-accent', c.accent);
    root.style.setProperty('--accent', c.primary);
    root.style.setProperty('--accent2', c.secondary);
    root.style.setProperty('--accent3', c.accent);
    root.classList.add('festival-active');
    root.classList.add('festival-' + f.id);
  }

  function injectBanner(f, dismissKey) {
    var banner = document.createElement('div');
    banner.className = 'festival-banner';
    banner.setAttribute('role', 'banner');
    banner.innerHTML =
      '<span class="festival-banner-text">' + f.config.emoji + ' ' + f.config.banner + ' ' + f.config.emoji + '</span>' +
      '<button class="festival-banner-close" aria-label="Dismiss festival banner">&times;</button>';

    document.body.insertBefore(banner, document.body.firstChild);

    banner.querySelector('.festival-banner-close').addEventListener('click', function() {
      banner.style.animation = 'fest-banner-out 0.3s ease forwards';
      setTimeout(function() {
        if (banner.parentNode) banner.parentNode.removeChild(banner);
      }, 300);
      try { localStorage.setItem(dismissKey, '1'); } catch(e) {}
    });
  }

  function injectParticles(f) {
    var type = f.config.particles || 'sparkle';
    var count = window.innerWidth < 768 ? 10 : 18;
    var container = document.createElement('div');
    container.className = 'festival-particles fp-' + type;

    var colors = [f.config.colors.primary, f.config.colors.secondary, f.config.colors.accent];

    for (var i = 0; i < count; i++) {
      var p = document.createElement('div');
      p.className = 'fp';
      p.style.left = (Math.random() * 100) + '%';
      p.style.top = type === 'glow' ? (Math.random() * 100) + '%' : '';
      p.style.setProperty('--fp-delay', (Math.random() * 6) + 's');
      p.style.setProperty('--fp-dur', (Math.random() * 4 + 3) + 's');
      p.style.setProperty('--fp-size', (Math.random() * 8 + 3) + 'px');

      if (type === 'confetti' || type === 'float' || type === 'petal') {
        p.style.setProperty('--fp-color', colors[Math.floor(Math.random() * colors.length)]);
      }
      if (type === 'petal') {
        p.style.setProperty('--fp-radius', '50% 0 50% 50%');
      }
      container.appendChild(p);
    }
    document.body.appendChild(container);
  }

  function init() {
    try {
      if (!window.FESTIVALS) return;

      var today = new Date();
      var festival = findFestival(today);
      if (!festival) return;

      var dismissKey = 'fest-dismiss-' + festival.id + '-' + today.getFullYear();
      var dismissed = false;
      try { dismissed = localStorage.getItem(dismissKey) === '1'; } catch(e) {}

      applyTheme(festival);

      if (!dismissed) {
        injectBanner(festival, dismissKey);
      }

      injectParticles(festival);

    } catch(e) {
      // Silent fail - never break the page
      if (window.console && console.warn) {
        console.warn('Festival engine:', e);
      }
    }
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
