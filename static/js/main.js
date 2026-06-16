// Navbar scroll effect
window.addEventListener('scroll', function() {
  const navbar = document.getElementById('navbar');
  if (window.scrollY > 20) {
    navbar.classList.add('glass', 'shadow-lg', 'shadow-dark-900/50');
  } else {
    navbar.classList.remove('glass', 'shadow-lg', 'shadow-dark-900/50');
  }
});

// Profile dropdown toggle
function toggleProfile() {
  const menu = document.getElementById('profile-menu');
  menu.classList.toggle('hidden');
}

// Close profile dropdown on click outside
document.addEventListener('click', function(e) {
  const dropdown = document.getElementById('profile-dropdown');
  const menu = document.getElementById('profile-menu');
  if (dropdown && !dropdown.contains(e.target)) {
    menu.classList.add('hidden');
  }
});

// Mobile menu toggle
function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  const icon = document.getElementById('menu-icon');
  menu.classList.toggle('hidden');
  if (menu.classList.contains('hidden')) {
    icon.setAttribute('d', 'M4 6h16M4 12h16M4 18h16');
  } else {
    icon.setAttribute('d', 'M6 18L18 6M6 6l12 12');
  }
}

function updateThemeToggleText() {
  const lightMode = document.body.classList.contains('light-mode');
  const label = lightMode ? 'Dark mode' : 'White mode';
  const icon = lightMode ? 'fas fa-moon' : 'fas fa-sun';
  const themeToggle = document.getElementById('theme-toggle-button');
  const themeToggleMobile = document.getElementById('theme-toggle-button-mobile');

  if (themeToggle) {
    themeToggle.innerHTML = `<i class="${icon}"></i>${label}`;
  }
  if (themeToggleMobile) {
    themeToggleMobile.innerHTML = `<i class="${icon} mr-2 text-accent-400"></i>${label}`;
  }

  const themeMeta = document.querySelector('meta[name="theme-color"]');
  if (themeMeta) {
    themeMeta.setAttribute('content', lightMode ? '#ffffff' : '#0f172a');
  }
}

function applySavedTheme() {
  const stored = localStorage.getItem('ai-fake-news-theme');
  const useLight = stored === 'light';
  document.body.classList.toggle('light-mode', useLight);
  updateThemeToggleText();
}

function toggleTheme() {
  const isLight = document.body.classList.toggle('light-mode');
  localStorage.setItem('ai-fake-news-theme', isLight ? 'light' : 'dark');
  updateThemeToggleText();
}

document.addEventListener('DOMContentLoaded', function() {
  applySavedTheme();
  const themeToggle = document.getElementById('theme-toggle-button');
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }
  const themeToggleMobile = document.getElementById('theme-toggle-button-mobile');
  if (themeToggleMobile) {
    themeToggleMobile.addEventListener('click', toggleTheme);
  }
});

// Toast notification system
function showToast(message, type) {
  const container = document.getElementById('toast-container');
  if (!container) {
    const div = document.createElement('div');
    div.id = 'toast-container';
    div.className = 'toast-container';
    document.body.appendChild(div);
  }
  const toast = document.createElement('div');
  toast.className = 'toast toast-' + (type || 'info');
  toast.textContent = message;
  document.getElementById('toast-container').appendChild(toast);
  setTimeout(function() {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(function() { toast.remove(); }, 300);
  }, 3500);
}

// Confirm dialog
function confirmAction(message) {
  return window.confirm(message);
}

// Copy to clipboard
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(function() {
    showToast('Copied to clipboard', 'success');
  });
}

// Format date
function formatDate(dateStr) {
  var d = new Date(dateStr);
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
}

// Intersection Observer for scroll animations
document.addEventListener('DOMContentLoaded', function() {
  var elements = document.querySelectorAll('.animate-on-scroll');
  if (elements.length > 0) {
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    elements.forEach(function(el) { observer.observe(el); });
  }
});

// Auto-hide alerts
document.addEventListener('DOMContentLoaded', function() {
  var alerts = document.querySelectorAll('.auto-hide');
  alerts.forEach(function(alert) {
    setTimeout(function() {
      alert.style.opacity = '0';
      alert.style.transition = 'opacity 0.5s';
      setTimeout(function() { alert.remove(); }, 500);
    }, 4000);
  });
});
