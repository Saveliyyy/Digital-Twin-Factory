// Система переключения тем
class ThemeManager {
    constructor() {
        this.themeToggle = document.getElementById('theme-toggle');
        this.body = document.body;
        this.init();
    }

    init() {
        // Загружаем сохраненную тему
        const savedTheme = localStorage.getItem('theme') || 'dark';
        this.setTheme(savedTheme);
        
        // Устанавливаем состояние переключателя
        if (this.themeToggle) {
            this.themeToggle.checked = savedTheme === 'light';
            this.themeToggle.addEventListener('change', () => this.toggleTheme());
        }
        
        // Добавляем анимацию появления
        this.addEntranceAnimation();
    }

    setTheme(theme) {
        // Удаляем старые классы тем
        this.body.classList.remove('light-theme', 'dark-theme');
        // Добавляем новый класс
        this.body.classList.add(`${theme}-theme`);
        // Сохраняем в localStorage
        localStorage.setItem('theme', theme);
        
        // Обновляем мета-теги для мобильных устройств
        this.updateMetaTheme(theme);
    }

    toggleTheme() {
        const currentTheme = this.body.classList.contains('dark-theme') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Добавляем эффект пульсации
        this.addPulseEffect();
        
        // Меняем тему
        this.setTheme(newTheme);
        
        // Отправляем событие для других компонентов
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
    }

    addPulseEffect() {
        const switcher = document.querySelector('.theme-switch');
        if (switcher) {
            switcher.classList.add('pulse');
            setTimeout(() => switcher.classList.remove('pulse'), 500);
        }
    }

    addEntranceAnimation() {
        const switcher = document.querySelector('.theme-switch-wrapper');
        if (switcher) {
            switcher.style.animation = 'slideInRight 0.5s ease';
        }
    }

    updateMetaTheme(theme) {
        let metaTheme = document.querySelector('meta[name="theme-color"]');
        if (!metaTheme) {
            metaTheme = document.createElement('meta');
            metaTheme.name = 'theme-color';
            document.head.appendChild(metaTheme);
        }
        
        const colors = {
            dark: '#0f0f0f',
            light: '#f8f9fa'
        };
        
        metaTheme.content = colors[theme];
    }
}

// Добавляем CSS анимации
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .theme-switch.pulse {
        animation: pulse 0.5s ease;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    /* Анимация смены темы */
    .theme-transition {
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }
    
    body * {
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
    }
`;
document.head.appendChild(style);

// Инициализируем менеджер тем после загрузки страницы
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});
