// Digital Twin Factory - Main JavaScript

const API_URL = window.location.origin;

// Состояние приложения
let appState = {
    currentJob: null,
    jobs: [],
    statistics: {},
    settings: {
        patients: 10000,
        visits: 50000,
        seed: 42,
        format: 'json'
    }
};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadJobs();
    setupEventListeners();
});

// Настройка обработчиков событий
function setupEventListeners() {
    // Форма генерации
    const generateForm = document.getElementById('generate-form');
    if (generateForm) {
        generateForm.addEventListener('submit', handleGenerate);
    }
    
    // Кнопки
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadStats();
            loadJobs();
        });
    }
    
    // Слайдеры
    const patientSlider = document.getElementById('patients');
    if (patientSlider) {
        patientSlider.addEventListener('input', function(e) {
            document.getElementById('patients-value').textContent = e.target.value;
            appState.settings.patients = parseInt(e.target.value);
        });
    }
    
    const visitsSlider = document.getElementById('visits');
    if (visitsSlider) {
        visitsSlider.addEventListener('input', function(e) {
            document.getElementById('visits-value').textContent = e.target.value;
            appState.settings.visits = parseInt(e.target.value);
        });
    }
}

// Загрузка статистики
async function loadStats() {
    try {
        const response = await fetch('/api/v1/stats');
        const data = await response.json();
        appState.statistics = data;
        updateStatsUI(data);
    } catch (error) {
        console.error('Error loading stats:', error);
        showAlert('Ошибка загрузки статистики', 'error');
    }
}

// Загрузка задач
async function loadJobs() {
    try {
        const response = await fetch('/api/v1/jobs');
        const data = await response.json();
        appState.jobs = data;
        updateJobsUI(data);
    } catch (error) {
        console.error('Error loading jobs:', error);
    }
}

// Обновление UI статистики
function updateStatsUI(stats) {
    const statsContainer = document.getElementById('stats-container');
    if (!statsContainer) return;
    
    statsContainer.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card fade-in">
                <div class="stat-icon">📊</div>
                <div class="stat-label">Всего генераций</div>
                <div class="stat-value">${stats.total_generations || 0}</div>
                <div class="stat-change">+ за сегодня</div>
            </div>
            <div class="stat-card fade-in">
                <div class="stat-icon">👥</div>
                <div class="stat-label">Сгенерировано пациентов</div>
                <div class="stat-value">${(stats.total_patients || 0).toLocaleString()}</div>
                <div class="stat-change">реалистичные данные</div>
            </div>
            <div class="stat-card fade-in">
                <div class="stat-icon">🏥</div>
                <div class="stat-label">Сгенерировано визитов</div>
                <div class="stat-value">${(stats.total_visits || 0).toLocaleString()}</div>
                <div class="stat-change">с сезонностью</div>
            </div>
            <div class="stat-card fade-in">
                <div class="stat-icon">⚡</div>
                <div class="stat-label">Успешных задач</div>
                <div class="stat-value">${stats.successful_jobs || 0}</div>
                <div class="stat-change">${stats.success_rate || '0%'}</div>
            </div>
        </div>
    `;
}

// Обновление UI задач
function updateJobsUI(jobs) {
    const jobsTable = document.getElementById('jobs-table-body');
    if (!jobsTable) return;
    
    if (jobs.length === 0) {
        jobsTable.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px;">
                    <span style="font-size: 48px;">📭</span>
                    <p style="color: #6c757d; margin-top: 10px;">Нет активных задач. Запустите генерацию!</p>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    jobs.slice(0, 10).forEach(job => {
        const statusClass = getStatusClass(job.status);
        const statusIcon = getStatusIcon(job.status);
        
        html += `
            <tr class="fade-in">
                <td><code>${job.job_id ? job.job_id.substring(0, 8) : 'N/A'}...</code></td>
                <td>${job.patients || 0}</td>
                <td>${job.visits || 0}</td>
                <td>
                    <span class="badge ${statusClass}">
                        ${statusIcon} ${job.status || 'pending'}
                    </span>
                </td>
                <td>${job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}</td>
                <td>
                    ${job.result_url ? 
                        `<button class="btn btn-sm btn-success" onclick="downloadJob('${job.job_id}')">📥</button>` : 
                        '<span class="badge badge-secondary">⏳</span>'
                    }
                </td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="viewJob('${job.job_id}')">👁️</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteJob('${job.job_id}')">🗑️</button>
                </td>
            </tr>
        `;
    });
    
    jobsTable.innerHTML = html;
}

// Получение класса статуса
function getStatusClass(status) {
    switch(status) {
        case 'completed': return 'badge-success';
        case 'processing': return 'badge-warning';
        case 'failed': return 'badge-danger';
        default: return 'badge-primary';
    }
}

// Получение иконки статуса
function getStatusIcon(status) {
    switch(status) {
        case 'completed': return '✅';
        case 'processing': return '⏳';
        case 'failed': return '❌';
        default: return '⏸️';
    }
}

// Обработка генерации
async function handleGenerate(e) {
    e.preventDefault();
    
    const button = e.target.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loader"></span> Генерация...';
    button.disabled = true;
    
    // Показываем прогресс
    showProgress();
    
    try {
        const formData = new FormData(e.target);
        const patients = formData.get('patients') || 10000;
        const visits = formData.get('visits') || 50000;
        const seed = formData.get('seed') || 42;
        
        const response = await fetch(`/api/v1/generate/medical?patients=${patients}&visits=${visits}&seed=${seed}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            appState.currentJob = data.job_id;
            showAlert(`✅ Генерация запущена! ID задачи: ${data.job_id.substring(0, 8)}...`, 'success');
            updateProgress(30);
            
            // Начинаем отслеживать прогресс
            trackProgress(data.job_id);
            
            // Обновляем статистику
            loadStats();
            loadJobs();
        } else {
            throw new Error(data.message || 'Ошибка генерации');
        }
    } catch (error) {
        showAlert(`❌ Ошибка: ${error.message}`, 'error');
        hideProgress();
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Отслеживание прогресса
async function trackProgress(jobId) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    let progress = 10;
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/v1/tasks/${jobId}`);
            const data = await response.json();
            
            if (data.state === 'PROGRESS') {
                progress = data.meta?.progress || progress + 5;
                updateProgress(progress);
                if (progressText) {
                    progressText.textContent = data.meta?.status || 'Генерация...';
                }
            } else if (data.state === 'SUCCESS') {
                updateProgress(100);
                if (progressText) progressText.textContent = '✅ Готово!';
                clearInterval(interval);
                setTimeout(() => hideProgress(), 2000);
                loadJobs();
                showAlert('✅ Генерация успешно завершена!', 'success');
            } else if (data.state === 'FAILURE') {
                clearInterval(interval);
                hideProgress();
                showAlert(`❌ Ошибка: ${data.meta?.error || 'Неизвестная ошибка'}`, 'error');
            }
        } catch (error) {
            console.error('Error tracking progress:', error);
        }
    }, 1000);
}

// Показать прогресс
function showProgress() {
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
        progressContainer.style.display = 'block';
    }
}

// Обновить прогресс
function updateProgress(percent) {
    const progressBar = document.getElementById('progress-bar');
    const progressPercent = document.getElementById('progress-percent');
    
    if (progressBar) {
        progressBar.style.width = `${percent}%`;
    }
    if (progressPercent) {
        progressPercent.textContent = `${percent}%`;
    }
}

// Скрыть прогресс
function hideProgress() {
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
        setTimeout(() => {
            progressContainer.style.display = 'none';
            updateProgress(0);
        }, 1000);
    }
}

// Просмотр задачи
async function viewJob(jobId) {
    try {
        const response = await fetch(`/api/v1/jobs/${jobId}`);
        const job = await response.json();
        
        showModal('Детали задачи', `
            <div style="padding: 20px;">
                <p><strong>ID задачи:</strong> ${job.job_id}</p>
                <p><strong>Статус:</strong> <span class="badge ${getStatusClass(job.status)}">${job.status}</span></p>
                <p><strong>Создана:</strong> ${new Date(job.created_at).toLocaleString()}</p>
                <p><strong>Пациентов:</strong> ${job.entity_counts?.patients || 'N/A'}</p>
                <p><strong>Визитов:</strong> ${job.entity_counts?.visits || 'N/A'}</p>
                <p><strong>Seed:</strong> ${job.parameters?.seed || 'N/A'}</p>
                ${job.error ? `<p style="color: #dc3545;"><strong>Ошибка:</strong> ${job.error}</p>` : ''}
                ${job.result_url ? `<button class="btn btn-success" onclick="downloadJob('${job.job_id}')">📥 Скачать результат</button>` : ''}
            </div>
        `);
    } catch (error) {
        showAlert('Ошибка загрузки задачи', 'error');
    }
}

// Удаление задачи
async function deleteJob(jobId) {
    if (!confirm('Вы уверены, что хотите удалить эту задачу?')) return;
    
    try {
        const response = await fetch(`/api/v1/jobs/${jobId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showAlert('✅ Задача удалена', 'success');
            loadJobs();
            loadStats();
        }
    } catch (error) {
        showAlert('❌ Ошибка удаления задачи', 'error');
    }
}

// Скачивание результата
async function downloadJob(jobId) {
    try {
        const response = await fetch(`/api/v1/datasets/${jobId}`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `medical_dataset_${jobId}.json`;
        a.click();
    } catch (error) {
        showAlert('❌ Ошибка скачивания', 'error');
    }
}

// Показать модальное окно
function showModal(title, content) {
    let modal = document.getElementById('modal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modal-title"></h2>
                    <span class="modal-close">&times;</span>
                </div>
                <div id="modal-body"></div>
            </div>
        `;
        document.body.appendChild(modal);
        
        modal.querySelector('.modal-close').onclick = function() {
            modal.classList.remove('active');
        };
        
        window.onclick = function(event) {
            if (event.target === modal) {
                modal.classList.remove('active');
            }
        };
    }
    
    modal.querySelector('#modal-title').textContent = title;
    modal.querySelector('#modal-body').innerHTML = content;
    modal.classList.add('active');
}

// Показать уведомление
function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} fade-in`;
    alert.innerHTML = message;
    alert.style.position = 'fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.style.maxWidth = '400px';
    alert.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.style.animation = 'slideIn 0.3s reverse';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

// Экспорт данных
function exportData(format = 'json') {
    if (!appState.currentJob) {
        showAlert('Нет данных для экспорта', 'warning');
        return;
    }
    
    downloadJob(appState.currentJob);
}

// Переключение темы
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
}

// Инициализация темы
function initTheme() {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
    }
}

// Вызов инициализации темы
initTheme();
