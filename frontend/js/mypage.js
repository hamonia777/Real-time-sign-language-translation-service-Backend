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
    startDate.setDate(today.getDate() - 52 * 7 - today.getDay());

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

    // 3. 잔디 그리드 채우기 (데이터 정합성 및 시뮬레이션 보완)
    if (grassGrid) {
        grassGrid.innerHTML = '';
        let learningData = [];

        try {
            const raw = localStorage.getItem('learningHistory');
            learningData = JSON.parse(raw);
            if (!Array.isArray(learningData)) learningData = null;
        } catch (e) {
            learningData = null;
        }

        // 371개(53주 * 7일) 박스 생성
        for (let i = 0; i < 371; i++) {
            const square = document.createElement('div');
            square.className = 'grass-square';

            // 데이터가 없으면 랜덤하게 테스트용 색칠
            let count = (learningData && learningData[i] !== undefined) 
                        ? learningData[i] 
                        : (Math.random() > 0.6 ? Math.floor(Math.random() * 6) : 0);

            const level = getGrassLevel(count);
            square.classList.add(level); // lv0~lv4 클래스 부여
            
            square.title = `학습량: ${count}개`;
            grassGrid.appendChild(square);
        }
    }

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
    if (notifToggle) {
        notifToggle.checked = localStorage.getItem('kakaoNotifEnabled') === 'true';
        notifToggle.addEventListener('change', (e) => {
            localStorage.setItem('kakaoNotifEnabled', e.target.checked);
            alert(e.target.checked ? '학습 알림이 설정되었습니다! 🔔' : '학습 알림이 해제되었습니다.');
        });
    }

    const kakaoBtn = document.getElementById('kakaoBtn');
    if (kakaoBtn) {
        kakaoBtn.addEventListener('click', () => {
            if (window.Kakao && Kakao.isInitialized()) {
                Kakao.Channel.chat({ channelPublicId: '_수어연구소' });
            } else {
                window.open('https://pf.kakao.com/_xxxx', '_blank');
            }
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