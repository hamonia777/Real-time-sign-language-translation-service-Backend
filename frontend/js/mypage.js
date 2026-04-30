/* ─────────────────────────────────────────────
   쿠키 헬퍼
   ───────────────────────────────────────────── */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

/* ─────────────────────────────────────────────
   프로필 이미지 표시 헬퍼
   ───────────────────────────────────────────── */
function showProfileImage(url) {
    const img = document.getElementById('userAvatar');
    const svg = document.getElementById('avatarSvg');
    if (!img || !url) return;
    img.src = url;
    img.style.display = 'block';
    if (svg) svg.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    // 26.04.21 혜미 추가 - 로그인 체크 기능 추가
    // 로그인 체크 & 버튼 처리
    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[1]) : null;
    }

    const accessToken = getCookie('access_token');
    if (!accessToken) {
        alert('로그인이 필요합니다.');
        location.href = 'login.html';
        return;
    }

    // 로그인 됐으면 버튼을 로그아웃으로 변경
    const authBtn = document.getElementById('headerAuthBtn');
    if (authBtn) {
        authBtn.innerText = '로그아웃';
        authBtn.classList.add('logout-style');
        authBtn.onclick = async () => {
            if (confirm('로그아웃 하시겠습니까?')) {
                document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                document.cookie = "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                await fetch('/api/v1/auth/logout', { method: 'GET', credentials: 'include' });
                alert('로그아웃 되었습니다.');
                location.href = 'home.html';
            }
        };
    }
    /* ─────────────────────────────────────────────
       0. 프로필 사진 모달 (클릭 시 확대)
       ───────────────────────────────────────────── */
    const photoModal = document.getElementById('photoModal');
    const photoModalImg = document.getElementById('photoModalImg');
    const avatarCircle = document.getElementById('avatarCircle');

    if (avatarCircle && photoModal) {
        avatarCircle.addEventListener('click', () => {
            const userAvatar = document.getElementById('userAvatar');
            const photoModalSvg = document.getElementById('photoModalSvg');
            const hasPhoto = userAvatar && userAvatar.style.display !== 'none' && userAvatar.src;

            if (hasPhoto) {
                photoModalImg.src = userAvatar.src;
                photoModalImg.style.display = 'block';
                if (photoModalSvg) photoModalSvg.style.display = 'none';
            } else {
                photoModalImg.style.display = 'none';
                if (photoModalSvg) photoModalSvg.style.display = 'block';
            }
            photoModal.classList.add('active');
        });

        photoModal.addEventListener('click', () => {
            photoModal.classList.remove('active');
        });
    }

    /* ─────────────────────────────────────────────
       0. 프로필 사진 로드 및 카메라 버튼
       ───────────────────────────────────────────── */
    const token = getCookie('access_token');

    // 현재 저장된 프로필 사진 및 닉네임 불러오기
    if (token) {
        fetch('/api/v1/profile/photo', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(res => res.ok ? res.json() : null)
        .then(data => {
            if (data && data.photo_url) showProfileImage(data.photo_url);
        })
        .catch(() => {});

        fetch('/api/v1/profile/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(res => res.ok ? res.json() : null)
        .then(data => {
            if (data && data.nickname) {
                const el = document.getElementById('profileName');
                if (el) el.textContent = data.nickname;
                localStorage.setItem('kakaoNickname', data.nickname);
            }
        })
        .catch(() => {});
    }

    // 카메라 버튼 → 파일 탐색기 열기
    const avatarEditBtn = document.getElementById('avatarEditBtn');
    const photoInput    = document.getElementById('photoInput');

    if (avatarEditBtn && photoInput) {
        avatarEditBtn.addEventListener('click', () => photoInput.click());

        photoInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            if (!token) {
                alert('로그인이 필요합니다.');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/v1/profile/photo', {
                    method: 'PATCH',
                    headers: { 'Authorization': `Bearer ${token}` },
                    body: formData,
                });

                if (res.ok) {
                    const data = await res.json();
                    showProfileImage(data.photo_url);
                } else {
                    alert('사진 변경에 실패했습니다.');
                }
            } catch (err) {
                console.error('사진 업로드 오류:', err);
                alert('사진 업로드 중 오류가 발생했습니다.');
            }

            photoInput.value = '';
        });
    }

    /* ─────────────────────────────────────────────
       0-1. 닉네임 수정 모달
       ───────────────────────────────────────────── */
    const nicknameModal   = document.getElementById('nicknameModal');
    const nicknameInput   = document.getElementById('nicknameInput');
    const nicknameCheckBtn = document.getElementById('nicknameCheckBtn');
    const nicknameCheckMsg = document.getElementById('nicknameCheckMsg');
    const nicknameSaveBtn  = document.getElementById('nicknameSaveBtn');
    const nicknameCancelBtn = document.getElementById('nicknameCancelBtn');
    const nicknameLockMsg  = document.getElementById('nicknameLockMsg');
    const nicknameInputRow = document.getElementById('nicknameInputRow');
    const profileNameEl    = document.getElementById('profileName');

    let nicknameCheckPassed = false;

    function openNicknameModal() {
        nicknameInput.value = '';
        nicknameCheckMsg.textContent = '';
        nicknameCheckMsg.className = 'nickname-check-msg';
        nicknameLockMsg.style.display = 'none';
        nicknameInputRow.style.display = 'flex';
        nicknameSaveBtn.disabled = false;
        nicknameCheckPassed = false;
        nicknameModal.classList.add('active');

        // 7일 제한 여부 서버에서 확인
        if (token) {
            fetch('/api/v1/profile/nickname/check?nickname=__dummy_check__', {
                headers: { 'Authorization': `Bearer ${token}` }
            }).catch(() => {});

            // 현재 프로필 조회로 nickname_updated_at 확인
            fetch('/api/v1/profile/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            .then(res => res.ok ? res.json() : null)
            .then(data => {
                if (data && data.nickname_updated_at) {
                    const updatedAt = new Date(data.nickname_updated_at);
                    const now = new Date();
                    const daysPassed = Math.floor((now - updatedAt) / (1000 * 60 * 60 * 24));
                    if (daysPassed < 7) {
                        const daysLeft = 7 - daysPassed;
                        const nextDate = new Date(updatedAt.getTime() + 7 * 24 * 60 * 60 * 1000);
                        const nextStr = `${nextDate.getMonth() + 1}월 ${nextDate.getDate()}일`;
                        nicknameLockMsg.textContent = `닉네임은 변경 후 7일이 지나야 다시 변경할 수 있습니다. (${nextStr} 이후 가능, ${daysLeft}일 남음)`;
                        nicknameLockMsg.style.display = 'block';
                        nicknameInputRow.style.display = 'none';
                        nicknameSaveBtn.disabled = true;
                    }
                }
            })
            .catch(() => {});
        }
    }

    if (profileNameEl) {
        profileNameEl.addEventListener('click', openNicknameModal);
        profileNameEl.addEventListener('mouseenter', () => {
            profileNameEl.style.color = '#517AAF';
            profileNameEl.style.textDecoration = 'underline';
            profileNameEl.style.cursor = 'pointer';
        });
        profileNameEl.addEventListener('mouseleave', () => {
            profileNameEl.style.color = '';
            profileNameEl.style.textDecoration = '';
        });
    }

    if (nicknameCancelBtn) {
        nicknameCancelBtn.addEventListener('click', () => {
            nicknameModal.classList.remove('active');
        });
    }

    nicknameModal && nicknameModal.addEventListener('click', (e) => {
        if (e.target === nicknameModal) nicknameModal.classList.remove('active');
    });

    if (nicknameCheckBtn) {
        nicknameCheckBtn.addEventListener('click', async () => {
            const val = nicknameInput.value.trim();
            if (val.length < 2 || val.length > 8) {
                nicknameCheckMsg.textContent = '닉네임은 2~8자로 입력해주세요.';
                nicknameCheckMsg.className = 'nickname-check-msg err';
                nicknameCheckPassed = false;
                return;
            }
            try {
                const res = await fetch(`/api/v1/profile/nickname/check?nickname=${encodeURIComponent(val)}`);
                const data = await res.json();
                if (data.is_available) {
                    nicknameCheckMsg.textContent = '사용 가능한 닉네임입니다.';
                    nicknameCheckMsg.className = 'nickname-check-msg ok';
                    nicknameCheckPassed = true;
                } else {
                    nicknameCheckMsg.textContent = '이미 사용 중인 닉네임입니다.';
                    nicknameCheckMsg.className = 'nickname-check-msg err';
                    nicknameCheckPassed = false;
                }
            } catch {
                nicknameCheckMsg.textContent = '중복 확인 중 오류가 발생했습니다.';
                nicknameCheckMsg.className = 'nickname-check-msg err';
                nicknameCheckPassed = false;
            }
        });
    }

    if (nicknameSaveBtn) {
        nicknameSaveBtn.addEventListener('click', async () => {
            if (!nicknameCheckPassed) {
                nicknameCheckMsg.textContent = '중복 확인을 먼저 해주세요.';
                nicknameCheckMsg.className = 'nickname-check-msg err';
                return;
            }
            const val = nicknameInput.value.trim();
            if (!token) { alert('로그인이 필요합니다.'); return; }

            try {
                const res = await fetch('/api/v1/profile/nickname', {
                    method: 'PATCH',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ nickname: val }),
                });

                if (res.ok) {
                    const data = await res.json();
                    if (profileNameEl) profileNameEl.textContent = data.nickname;
                    localStorage.setItem('kakaoNickname', data.nickname);
                    nicknameModal.classList.remove('active');
                } else {
                    const err = await res.json();
                    nicknameCheckMsg.textContent = err.detail || '닉네임 변경에 실패했습니다.';
                    nicknameCheckMsg.className = 'nickname-check-msg err';
                }
            } catch {
                nicknameCheckMsg.textContent = '닉네임 변경 중 오류가 발생했습니다.';
                nicknameCheckMsg.className = 'nickname-check-msg err';
            }
        });
    }

    /* ─────────────────────────────────────────────
       1. 개인정보 연동
       ───────────────────────────────────────────── */
    const surveyData = JSON.parse(localStorage.getItem('surveyResults')) || {};

    const typeMap = { 'non-deaf': '비수어인', 'deaf': '수어인', 'oral': '구화인' };
    const skillMap = {
        'lv1': 'Lv1. 초급', 'lv2': 'Lv2. 기초', 'lv3': 'Lv3. 중급',
        'lv4': 'Lv4. 고급', 'lv5': 'Lv5. 마스터'
    };

    const userType  = typeMap[surveyData.type]  || typeMap[surveyData.userType]  || '비수어인';
    const userSkill = skillMap[surveyData.skill] || skillMap[surveyData.level]   || 'Lv1. 초급';

    const kakaoEmail = localStorage.getItem('kakaoEmail') || localStorage.getItem('userEmail') || 'gim02673@gmail.com';
    const userName = localStorage.getItem('kakaoNickname') || localStorage.getItem('userName') || '정혜미';
    const userPhone = localStorage.getItem('userPhone') || localStorage.getItem('phoneNumber') || '010-2413-4622';

    const elName   = document.getElementById('profileName');
    const elStatus = document.getElementById('profileStatus');
    const elEmail  = document.getElementById('profileEmail');
    const elPhone  = document.getElementById('profilePhone');

    if (elName)   elName.innerText   = userName;
    if (elStatus) elStatus.innerText = `${userType} / ${userSkill}`;
    if (elEmail)  elEmail.innerText  = kakaoEmail;
    if (elPhone)  elPhone.innerText  = userPhone;

    /* ─────────────────────────────────────────────
       1-1. 완료/진행 중인 학습 DB 연동
       ───────────────────────────────────────────── */
    function formatDate(value) {
        if (!value) return '';
        const d = new Date(value);
        if (Number.isNaN(d.getTime())) return '';
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}.${m}.${day}`;
    }

    function getLessonUrl(item) {
        if (item.category === 'sentence') return `sentence_learn.html?lesson_id=${item.lesson_id}`;
        if (item.category === 'fingerspell') {
            const wordModelFsChars = new Set(['ㄲ', 'ㄸ', 'ㅃ', 'ㅆ', 'ㅉ', 'ㅘ', 'ㅙ', 'ㅝ', 'ㅞ']);
            return `${wordModelFsChars.has(item.title) ? 'word_learn.html' : 'sign_learn.html'}?lesson_id=${item.lesson_id}`;
        }
        return `word_learn.html?lesson_id=${item.lesson_id}`;
    }

    function renderCompletedLearning(items, totalCount) {
        const countEl = document.getElementById('completedCount');
        const recentEl = document.getElementById('completedRecent');
        const listEl = document.getElementById('completedLearningList');
        if (countEl) countEl.textContent = `${totalCount}개`;
        if (recentEl) {
            const recent = items[0];
            recentEl.textContent = recent
                ? `최근 완료 : ${recent.title} (${formatDate(recent.updated_at)})`
                : '최근 완료 : 없음';
        }
        if (!listEl) return;
        listEl.innerHTML = '';
        if (!items.length) {
            listEl.innerHTML = '<li class="empty-learning">완료된 학습이 없습니다.</li>';
            return;
        }
        items.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = `
                <i class="check-dot"></i>
                <span></span>
                <span class="date"></span>
                <button class="btn-sm" type="button">다시 학습</button>
            `;
            li.querySelector('span').textContent = item.title;
            li.querySelector('.date').textContent = formatDate(item.updated_at);
            li.querySelector('button').addEventListener('click', () => {
                location.href = getLessonUrl(item);
            });
            listEl.appendChild(li);
        });
    }

    function renderInProgressLearning(items, totalCount) {
        const countEl = document.getElementById('inProgressCount');
        const recentEl = document.getElementById('inProgressRecent');
        const listEl = document.getElementById('inProgressLearningList');
        if (countEl) countEl.textContent = `진행 중인 학습 : ${totalCount}개 단어/문장`;
        if (recentEl) {
            const recent = items[0];
            recentEl.textContent = recent
                ? `최근 진행 : ${recent.title} (${formatDate(recent.updated_at)})`
                : '최근 진행 : 없음';
        }
        if (!listEl) return;
        listEl.innerHTML = '';
        if (!items.length) {
            listEl.innerHTML = '<div class="empty-learning">진행 중인 학습이 없습니다.</div>';
            return;
        }
        items.forEach(item => {
            const pct = Math.max(0, Math.min(100, item.progress_percent || 0));
            const row = document.createElement('div');
            row.className = 'progress-item';
            row.innerHTML = `
                <div class="item-left">
                    <div class="custom-radio active"><div class="radio-inner"></div></div>
                    <span class="word-text"></span>
                </div>
                <div class="progress-bar-container">
                    <div class="bar-bg"><div class="bar-fill"></div></div>
                    <span class="percent-text"></span>
                </div>
                <span class="date-text"></span>
                <button class="resume-btn" type="button">이어하기</button>
            `;
            row.querySelector('.word-text').textContent = item.title;
            row.querySelector('.bar-fill').style.width = `${pct}%`;
            row.querySelector('.percent-text').textContent = `${pct}% 완료`;
            row.querySelector('.date-text').textContent = formatDate(item.updated_at);
            row.querySelector('button').addEventListener('click', () => {
                location.href = getLessonUrl(item);
            });
            listEl.appendChild(row);
        });
    }

    async function loadLearningProgress() {
        try {
            const authHeaders = { 'Authorization': `Bearer ${token}` };
            const [completedRes, inProgressRes] = await Promise.all([
                fetch('/api/v1/profile/learning/completed', { headers: authHeaders }),
                fetch('/api/v1/profile/learning/in-progress', { headers: authHeaders }),
            ]);
            if (completedRes.status === 401 || inProgressRes.status === 401) {
                alert('로그인이 필요합니다.');
                location.href = 'login.html';
                return;
            }
            if (!completedRes.ok) throw new Error(`completed HTTP ${completedRes.status}`);
            if (!inProgressRes.ok) throw new Error(`in-progress HTTP ${inProgressRes.status}`);

            const completedData = await completedRes.json();
            const inProgressData = await inProgressRes.json();
            const completedItems = completedData.items || [];
            const inProgressItems = inProgressData.items || [];
            renderCompletedLearning(completedItems, completedData.total_count || 0);
            renderInProgressLearning(inProgressItems, inProgressData.total_count || 0);

            const completedIds = completedItems.map(item => item.lesson_id);
            localStorage.setItem('learning_completed_lessons', JSON.stringify(completedIds));
        } catch (err) {
            console.error('학습 진행 현황 로드 실패:', err);
            renderCompletedLearning([], 0);
            renderInProgressLearning([], 0);
        }
    }

    loadLearningProgress();

    /* ─────────────────────────────────────────────
       1-2. 학습 바구니 DB 연동
       26.4.30 : 가령 : 수정 내용 - DB 바구니 항목을 category 기준 3열 UI로 렌더링
       ───────────────────────────────────────────── */
    function renderLearningBasket(items) {
        const countEl = document.getElementById('basketCount');
        const gridEl = document.getElementById('basketGrid');
        if (countEl) countEl.textContent = `학습 바구니 총 항목 : ${items.length}개`;
        if (!gridEl) return;

        gridEl.innerHTML = '';
        const groups = [
            // 26.4.30 : 가령 : 수정 내용 - lessons.category 기준으로 지문자/단어/문장 컬럼 분리
            { key: 'fingerspell', label: '지문자' },
            { key: 'word', label: '단어' },
            { key: 'sentence', label: '문장' },
        ];
        const columns = {};

        groups.forEach(group => {
            const col = document.createElement('div');
            col.className = 'basket-col';
            const list = document.createElement('ul');
            list.className = 'item-list';
            list.dataset.category = group.key;
            col.appendChild(list);
            gridEl.appendChild(col);
            columns[group.key] = list;
        });

        if (!items.length) {
            groups.forEach(group => {
                columns[group.key].innerHTML = '';
            });
            return;
        }

        items.forEach(item => {
            const list = columns[item.category];
            if (!list) return;
            const li = document.createElement('li');
            li.innerHTML = `
                <div class="flex-center"><i class="green-dot"></i><span></span></div>
                <button class="btn-blue learn-btn" type="button">학습하기</button>
            `;
            li.querySelector('span').textContent = item.title;
            li.querySelector('.learn-btn').addEventListener('click', () => {
                location.href = getLessonUrl(item);
            });
            list.appendChild(li);
        });

        groups.forEach(group => {
            if (!columns[group.key].children.length) {
                columns[group.key].innerHTML = '';
            }
        });
    }

    // 26.4.30 : 가령 : 수정 내용 - 마이페이지 진입 시 서버에서 학습 바구니 목록 조회
    async function loadLearningBasket() {
        try {
            const res = await fetch('/api/v1/profile/basket', {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (res.status === 401) {
                alert('로그인이 필요합니다.');
                location.href = 'login.html';
                return;
            }
            if (!res.ok) throw new Error(`basket HTTP ${res.status}`);
            const data = await res.json();
            renderLearningBasket(data.items || []);
        } catch (err) {
            console.error('학습 바구니 로드 실패:', err);
            renderLearningBasket([]);
        }
    }

    async function removeLearningBasket(basketId) {
        if (!confirm('학습 바구니에서 삭제하시겠습니까?')) return;
        try {
            const res = await fetch(`/api/v1/learning/basket/${basketId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!res.ok) throw new Error(`basket delete HTTP ${res.status}`);
            await loadLearningBasket();
        } catch (err) {
            console.error('학습 바구니 삭제 실패:', err);
            alert('학습 바구니 삭제 중 오류가 발생했습니다.');
        }
    }

    loadLearningBasket();


/* ──────────────────────────────────────────────────────────
   2. 성취도 잔디 그래프 생성 (가변 그리드 대응 교정본)
   ────────────────────────────────────────────────────────── */
    const monthContainer = document.getElementById('monthLabels');
    const grassGrid      = document.getElementById('grassGrid');
    const dayLabelsEl    = document.getElementById('dayLabels');

    // 1. 요일 라벨 (월, 수, 금)
    if (dayLabelsEl) {
        dayLabelsEl.innerHTML = '';
        const labels = ['', '월', '', '수', '', '금', ''];
        labels.forEach(txt => {
            const sp = document.createElement('span');
            sp.textContent = txt;
            dayLabelsEl.appendChild(sp);
        });
    }

    // 오늘부터 52주 전 계산
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - 370);

    // 2. 월 라벨 생성 (CSS 그리드 칼럼 시스템 활용)
    if (monthContainer) {
        monthContainer.innerHTML = '';
        
        // 첫 번째 칸(요일 라벨 너비 26px 대응) 비워두기용 스페이서 생성
        const spacer = document.createElement('div');
        spacer.className = 'month-spacer'; 
        monthContainer.appendChild(spacer);

        const monthNames = ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월'];
        let lastMonth = -1;

        for (let w = 0; w < 53; w++) {
            const d = new Date(startDate.getTime());
            d.setDate(startDate.getDate() + w * 7);
            const m = d.getMonth();

            if (m !== lastMonth) {
                lastMonth = m;
                const lbl = document.createElement('span');
                lbl.className = 'month-label-item';
                lbl.textContent = monthNames[m];
                
                // 핵심: px 계산 대신 grid-column 속성 사용
                // 첫 칸이 spacer이므로 (w + 2)번째 칼럼에 위치시킴
                lbl.style.gridColumn = w + 2; 
                monthContainer.appendChild(lbl);
            }
        }
    }

    function toIsoDate(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    function renderAchievement(days, startDateValue) {
        if (!grassGrid) return;
        grassGrid.innerHTML = '';
        const countMap = new Map((days || []).map(day => [day.date, day.count || 0]));
        const graphStartDate = startDateValue ? new Date(`${startDateValue}T00:00:00`) : startDate;

        // 371개(53주 * 7일) 박스 생성
        for (let i = 0; i < 371; i++) {
            const square = document.createElement('div');
            square.className = 'grass-square';
            const currentDate = new Date(graphStartDate.getTime());
            currentDate.setDate(graphStartDate.getDate() + i);
            const dateKey = toIsoDate(currentDate);
            const count = countMap.get(dateKey) || 0;
            const level = getGrassLevel(count);
            square.classList.add(level);
            square.title = `${dateKey} 학습량: ${count}개`;
            grassGrid.appendChild(square);
        }
    }

    async function loadAchievement() {
        try {
            const res = await fetch('/api/v1/profile/achievement', {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (res.status === 401) {
                alert('로그인이 필요합니다.');
                location.href = 'login.html';
                return;
            }
            if (!res.ok) throw new Error(`achievement HTTP ${res.status}`);
            const data = await res.json();
            renderAchievement(data.days || [], data.start_date);
        } catch (err) {
            console.error('성취도 로드 실패:', err);
            renderAchievement([]);
        }
    }

    loadAchievement();

    // 레벨 판별 함수 (수치 조정)
    function getGrassLevel(count) {
        if (!count || count === 0) return 'lv0';
        if (count === 1) return 'lv1';
        if (count <= 3)  return 'lv2';
        if (count <= 5)  return 'lv3';
        return 'lv4';
    }


    /* ─────────────────────────────────────────────
       3. 탭 전환 / 알림 / 카카오 / 로그아웃 (기존 동일)
       ───────────────────────────────────────────── */
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    const notifToggle = document.getElementById('kakaoNotif');
    if (notifToggle && token) {
        // 현재 알림 상태 서버에서 조회
        fetch('/api/v1/profile/notification/status', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(res => res.ok ? res.json() : null)
        .then(data => {
            if (data) notifToggle.checked = data.enabled;
        })
        .catch(() => {});

        notifToggle.addEventListener('change', async (e) => {
            if (e.target.checked) {
                // ON: 카카오 talk_message 동의 페이지로 이동
                if (confirm('카카오톡 학습 알림을 받으려면 카카오 메시지 권한 동의가 필요합니다.\n동의 페이지로 이동하시겠습니까?')) {
                    location.href = '/api/v1/auth/kakao/notification/enable';
                } else {
                    e.target.checked = false;
                }
            } else {
                // OFF: 알림 비활성화 API 호출
                try {
                    const res = await fetch('/api/v1/profile/notification/disable', {
                        method: 'PATCH',
                        headers: { 'Authorization': `Bearer ${token}` },
                    });
                    if (!res.ok) e.target.checked = true;
                } catch {
                    e.target.checked = true;
                }
            }
        });
    }

    const notifTestBtn = document.getElementById('notifTestBtn');
    if (notifTestBtn) {
        notifTestBtn.addEventListener('click', async () => {
            if (!token) { alert('로그인이 필요합니다.'); return; }
            notifTestBtn.textContent = '발송 중...';
            notifTestBtn.disabled = true;
            try {
                const res = await fetch('/api/v1/profile/notification/test', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` },
                });
                const data = await res.json();
                alert(data.result || data.detail);
            } catch {
                alert('테스트 발송 중 오류가 발생했습니다.');
            }
            notifTestBtn.textContent = '알림 테스트';
            notifTestBtn.disabled = false;
        });
    }

    const kakaoBtn = document.getElementById('kakaoBtn');
    if (kakaoBtn) {
        kakaoBtn.addEventListener('click', () => {
            window.open('http://pf.kakao.com/_GxoDEX', '_blank');
        });
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            if (confirm('로그아웃 하시겠습니까?')) {
                document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                document.cookie = "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                await fetch('/api/v1/auth/logout', { method: 'GET', credentials: 'include' });
                alert('로그아웃 되었습니다.');
                location.href = 'home.html';
            }
        });
    }
});

/* ─────────────────────────────────────────────
   학습 기록 탭 전환 로직
   ───────────────────────────────────────────── */
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');

        // 1. 버튼 활성화 상태 변경
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // 2. 콘텐츠 전환
        tabContents.forEach(content => {
            if (content.id === `tab-${targetTab}`) {
                content.style.display = 'block';
            } else {
                content.style.display = 'none';
            }
        });
    });
});
