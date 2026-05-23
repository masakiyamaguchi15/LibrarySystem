// Interactive client-side scripts for Library Loan System

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialise Toast Container if not exists
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    // Toast Notifier
    window.showToast = (message, type = 'success') => {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // Add danger icon if error
        let iconHtml = '';
        if (type === 'danger') {
            iconHtml = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg>`;
        }
        
        toast.innerHTML = `${iconHtml}<span>${message}</span>`;
        toastContainer.appendChild(toast);

        toast.addEventListener('click', () => toast.remove());

        setTimeout(() => {
            toast.remove();
        }, 4000);
    };

    // 2. Demo Assistant Panel Toggle
    const demoToggle = document.querySelector('.demo-assist-toggle');
    const demoPanel = document.querySelector('.demo-panel');

    if (demoToggle && demoPanel) {
        demoToggle.addEventListener('click', () => {
            if (demoPanel.style.display === 'none' || !demoPanel.style.display) {
                demoPanel.style.display = 'block';
            } else {
                demoPanel.style.display = 'none';
            }
        });

        // Close button inside demo panel
        const closeBtn = demoPanel.querySelector('.close-demo-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                demoPanel.style.display = 'none';
            });
        }
    }

    // 3. Automated Demo Scenario runner
    const scenarioBtns = document.querySelectorAll('.demo-scenario-btn');
    scenarioBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const scenarioId = btn.dataset.scenario;
            showToast(`シナリオ ${scenarioId} を実行中...`, 'warning');
            
            try {
                const response = await fetch(`/api/run_scenario/?scenario_id=${scenarioId}`);
                const data = await response.json();
                
                if (data.success) {
                    showToast(data.message, 'success');
                    // Reload the page to reflect new DB state after 1.2s
                    setTimeout(() => {
                        window.location.reload();
                    }, 1200);
                } else {
                    showToast(data.error || 'エラーが発生しました。', 'danger');
                }
            } catch (err) {
                showToast('ネットワーク接続エラーが発生しました。', 'danger');
            }
        });
    });

    // 4. Lend Wizard multi-step coordinator (if on Lend page)
    const lendWizard = document.getElementById('lend-wizard-form');
    if (lendWizard) {
        const step1 = document.getElementById('lend-step-1');
        const step2 = document.getElementById('lend-step-2');
        const step3 = document.getElementById('lend-step-3');

        const bubble1 = document.getElementById('bubble-1');
        const bubble2 = document.getElementById('bubble-2');
        const bubble3 = document.getElementById('bubble-3');

        const verifyUserBtn = document.getElementById('verify-user-btn');
        const verifyCopyBtn = document.getElementById('verify-copy-btn');
        const confirmLendBtn = document.getElementById('confirm-lend-btn');

        const lendUserIdInput = document.getElementById('lend-user-id-input');
        const lendCopyIdInput = document.getElementById('lend-copy-id-input');

        // State variables
        let selectedUser = null;
        let selectedCopy = null;

        // Step 1 -> Step 2 transition
        verifyUserBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const userId = lendUserIdInput.value.trim();
            if (!userId) {
                showToast('利用者カード番号を入力してください。', 'danger');
                return;
            }

            try {
                const res = await fetch(`/api/validate_user/?user_id=${userId}`);
                const data = await res.json();

                if (data.success) {
                    selectedUser = data.user;
                    showToast(`${selectedUser.name} 様のカードを認証しました。`, 'success');
                    
                    // Render details inside step 2 header
                    document.getElementById('selected-user-name-display').textContent = selectedUser.name;
                    document.getElementById('selected-user-id-display').textContent = selectedUser.user_id;

                    // Transition UI
                    step1.style.display = 'none';
                    step2.style.display = 'block';
                    bubble1.classList.remove('active');
                    bubble1.classList.add('completed');
                    bubble2.classList.add('active');
                } else {
                    showToast(data.error || '利用者カードを認証できませんでした。', 'danger');
                }
            } catch (err) {
                showToast('利用者カード照合中にエラーが発生しました。', 'danger');
            }
        });

        // Step 2 -> Step 3 transition
        verifyCopyBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const copyId = lendCopyIdInput.value.trim();
            if (!copyId) {
                showToast('蔵書コピーIDを入力してください。', 'danger');
                return;
            }

            try {
                const res = await fetch(`/api/validate_copy/?copy_id=${copyId}`);
                const data = await res.json();

                if (data.success) {
                    selectedCopy = data.copy;
                    showToast(`図書「${selectedCopy.title}」を照合しました。`, 'success');

                    // Render summary details in step 3
                    document.getElementById('summary-user-name').textContent = selectedUser.name;
                    document.getElementById('summary-user-id').textContent = selectedUser.user_id;
                    document.getElementById('summary-user-address').textContent = selectedUser.address;

                    document.getElementById('summary-book-title').textContent = selectedCopy.title;
                    document.getElementById('summary-book-author').textContent = selectedCopy.author;
                    document.getElementById('summary-copy-id').textContent = selectedCopy.copy_id;

                    // Compute due date (14 days from now)
                    const dueDate = new Date();
                    dueDate.setDate(dueDate.getDate() + 14);
                    document.getElementById('summary-due-date').textContent = dueDate.toLocaleDateString('ja-JP');

                    // Transition UI
                    step2.style.display = 'none';
                    step3.style.display = 'block';
                    bubble2.classList.remove('active');
                    bubble2.classList.add('completed');
                    bubble3.classList.add('active');
                } else {
                    showToast(data.error || '図書を照合できませんでした。', 'danger');
                }
            } catch (err) {
                showToast('図書照合中にエラーが発生しました。', 'danger');
            }
        });

        // Step 3 Back Buttons
        document.getElementById('back-to-step-2').addEventListener('click', (e) => {
            e.preventDefault();
            step3.style.display = 'none';
            step2.style.display = 'block';
            bubble3.classList.remove('active');
            bubble2.classList.remove('completed');
            bubble2.classList.add('active');
        });

        // Step 2 Back Button
        document.getElementById('back-to-step-1').addEventListener('click', (e) => {
            e.preventDefault();
            step2.style.display = 'none';
            step1.style.display = 'block';
            bubble2.classList.remove('active');
            bubble1.classList.remove('completed');
            bubble1.classList.add('active');
        });

        // Step 3 Confirm Lend (Submit via POST)
        confirmLendBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            try {
                const response = await fetch('/api/create_loan/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        user_id: selectedUser.user_id,
                        copy_id: selectedCopy.copy_id
                    })
                });
                const data = await response.json();

                if (data.success) {
                    showToast('貸出処理が正常に完了しました！ダッシュボードへ戻ります。', 'success');
                    setTimeout(() => {
                        window.location.href = '/menu/';
                    }, 1500);
                } else {
                    showToast(data.error || '貸出の登録に失敗しました。', 'danger');
                }
            } catch (err) {
                showToast('貸出処理登録中にネットワークエラーが発生しました。', 'danger');
            }
        });
    }
});
