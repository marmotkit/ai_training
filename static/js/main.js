/**
 * 課程互動平台 - 主要JavaScript文件
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 移動設備側邊欄收起/展開功能
    var sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('show-sidebar');
        });
    }

    // 監聽簡報頁面的鍵盤事件
    if (document.querySelector('.presentation-viewer')) {
        window.addEventListener('keydown', function(e) {
            var prevPageBtn = document.getElementById('prevPage');
            var nextPageBtn = document.getElementById('nextPage');

            if (e.key === 'ArrowLeft' && prevPageBtn && !prevPageBtn.classList.contains('disabled')) {
                prevPageBtn.click();
            } else if (e.key === 'ArrowRight' && nextPageBtn && !nextPageBtn.classList.contains('disabled')) {
                nextPageBtn.click();
            }
        });
    }

    // 簡報全屏功能
    var fullscreenBtn = document.getElementById('fullscreenBtn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function() {
            var presentationViewer = document.querySelector('.presentation-viewer');
            if (presentationViewer) {
                if (!document.fullscreenElement) {
                    if (presentationViewer.requestFullscreen) {
                        presentationViewer.requestFullscreen();
                    } else if (presentationViewer.mozRequestFullScreen) { // Firefox
                        presentationViewer.mozRequestFullScreen();
                    } else if (presentationViewer.webkitRequestFullscreen) { // Chrome, Safari and Opera
                        presentationViewer.webkitRequestFullscreen();
                    } else if (presentationViewer.msRequestFullscreen) { // IE/Edge
                        presentationViewer.msRequestFullscreen();
                    }
                    fullscreenBtn.innerHTML = '<i class="bi bi-fullscreen-exit me-1"></i>退出全屏';
                } else {
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.mozCancelFullScreen) {
                        document.mozCancelFullScreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    } else if (document.msExitFullscreen) {
                        document.msExitFullscreen();
                    }
                    fullscreenBtn.innerHTML = '<i class="bi bi-fullscreen me-1"></i>全屏顯示';
                }
            }
        });
    }

    // 問答頁面篩選功能
    var applyFiltersBtn = document.getElementById('applyFilters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            var searchText = document.getElementById('searchQuestion').value.toLowerCase();
            var questionCards = document.querySelectorAll('.question-card');
            
            questionCards.forEach(function(card) {
                var title = card.querySelector('.card-header h5').textContent.toLowerCase();
                var content = card.querySelector('.card-text').textContent.toLowerCase();
                
                if (title.includes(searchText) || content.includes(searchText)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // 複製按鈕功能
    document.querySelectorAll('.copy-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            var targetId = this.getAttribute('data-target');
            var content = document.getElementById(targetId).textContent;
            
            navigator.clipboard.writeText(content).then(function() {
                button.innerHTML = '<i class="bi bi-check-lg me-1"></i>已複製';
                setTimeout(function() {
                    button.innerHTML = '<i class="bi bi-clipboard me-1"></i>複製';
                }, 2000);
            }).catch(function(err) {
                console.error('複製失敗:', err);
            });
        });
    });

    // 保存筆記到本地存儲
    var saveNotesBtn = document.getElementById('saveNotes');
    if (saveNotesBtn) {
        saveNotesBtn.addEventListener('click', function() {
            var notesContent = document.getElementById('notesContent').value;
            var presentationId = this.getAttribute('data-presentation-id');
            var pageNumber = this.getAttribute('data-page');
            
            if (notesContent.trim()) {
                localStorage.setItem('presentation_notes_' + presentationId + '_' + pageNumber, notesContent);
                
                // 顯示成功消息
                var alert = document.createElement('div');
                alert.className = 'alert alert-success mt-3';
                alert.innerHTML = '<i class="bi bi-check-circle me-2"></i>筆記已成功保存！';
                
                var notesCard = document.querySelector('.card:has(#notesContent)');
                notesCard.querySelector('.card-body').appendChild(alert);
                
                setTimeout(function() {
                    alert.remove();
                }, 3000);
            }
        });
        
        // 載入已保存的筆記
        var presentationId = saveNotesBtn.getAttribute('data-presentation-id');
        var pageNumber = saveNotesBtn.getAttribute('data-page');
        var savedNotes = localStorage.getItem('presentation_notes_' + presentationId + '_' + pageNumber);
        
        if (savedNotes) {
            document.getElementById('notesContent').value = savedNotes;
        }
    }

    // 簡報切換提示
    var presentationDropdownItems = document.querySelectorAll('.dropdown-item[href^="/presentation/"]');
    presentationDropdownItems.forEach(function(item) {
        item.addEventListener('click', function(e) {
            var currentPresentation = document.querySelector('.dropdown-item.active').textContent;
            var newPresentation = this.textContent;
            
            if (currentPresentation !== newPresentation) {
                var confirmChange = confirm('您確定要切換到「' + newPresentation + '」嗎？您在當前簡報的筆記和進度將被保存。');
                
                if (!confirmChange) {
                    e.preventDefault();
                }
            }
        });
    });

    // 密碼顯示切換
    const togglePassword = document.getElementById('togglePassword');
    if (togglePassword) {
        togglePassword.addEventListener('click', function() {
            const passwordInput = document.getElementById('password');
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // 切換圖標
            const eyeIcon = this.querySelector('i');
            eyeIcon.classList.toggle('bi-eye');
            eyeIcon.classList.toggle('bi-eye-slash');
        });
    }
    
    // 講師登入
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.addEventListener('click', function() {
            const form = document.getElementById('lecturerLoginForm');
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const rememberMe = document.getElementById('rememberMe').checked;
            const errorDiv = document.getElementById('loginError');
            
            // 簡單的客戶端驗證
            if (!username || !password) {
                errorDiv.textContent = '請填寫用戶名和密碼';
                errorDiv.classList.remove('d-none');
                return;
            }
            
            // 發送登入請求
            fetch('/lecturer/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    password,
                    rememberMe
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 登入成功
                    window.location.href = '/lecturer/dashboard';
                } else {
                    // 登入失敗
                    errorDiv.textContent = data.message || '登入失敗，請檢查用戶名和密碼';
                    errorDiv.classList.remove('d-none');
                }
            })
            .catch(error => {
                errorDiv.textContent = '登入過程中發生錯誤，請稍後再試';
                errorDiv.classList.remove('d-none');
                console.error('登入錯誤:', error);
            });
        });
    }
});

// 幻燈片切換功能
const prevSlide = document.getElementById('prevSlide');
const nextSlide = document.getElementById('nextSlide');
const slideImage = document.getElementById('slideImage');
const currentPage = document.getElementById('currentPage');
const totalPages = document.getElementById('totalPages');

if (prevSlide && nextSlide && slideImage) {
    let current = parseInt(currentPage.textContent);
    let total = parseInt(totalPages.textContent);
    
    prevSlide.addEventListener('click', function() {
        if (current > 1) {
            current--;
            updateSlide();
        }
    });
    
    nextSlide.addEventListener('click', function() {
        if (current < total) {
            current++;
            updateSlide();
        }
    });
    
    // 使用方向鍵導航
    document.addEventListener('keydown', function(event) {
        if (event.key === 'ArrowLeft') {
            prevSlide.click();
        } else if (event.key === 'ArrowRight') {
            nextSlide.click();
        }
    });
    
    function updateSlide() {
        // 更新頁碼
        currentPage.textContent = current;
        
        // 從圖片URL中提取基本路徑，並更新為新頁面
        const imgSrc = slideImage.src;
        const basePath = imgSrc.substring(0, imgSrc.lastIndexOf('/') + 1);
        const filename = imgSrc.substring(imgSrc.lastIndexOf('/') + 1, imgSrc.lastIndexOf('_'));
        slideImage.src = `${basePath}${filename}_${current}.jpg`;
        
        // 更新按鈕狀態
        prevSlide.disabled = (current === 1);
        nextSlide.disabled = (current === total);
    }
}

// 顯示通知提示
function showToast(title, message, type) {
    // 創建toast元素
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    const toastBody = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}：</strong> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastEl.innerHTML = toastBody;
    
    // 創建toast容器（如果不存在）
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // 添加toast到容器
    toastContainer.appendChild(toastEl);
    
    // 初始化Bootstrap toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 3000
    });
    
    // 顯示toast
    toast.show();
    
    // 當toast隱藏後移除元素
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
} 