document.addEventListener('DOMContentLoaded', () => {
    console.log("수어 연구소 JS가 준비되었습니다!");

    /* -----------------------------------------------------------
       1. 네비게이션 (어느 페이지에서든 작동하도록)
    ----------------------------------------------------------- */
    const navLinks = document.querySelectorAll('.nav-bar a');

    navLinks.forEach(link => {
        link.onclick = (e) => {
            const menuText = link.innerText.trim();
            
            // 텍스트 기반 이동
            if (menuText === "고객지원") {
                location.href = 'support.html';
            } 
            else if (menuText === "마이페이지") {
                location.href = 'mypage.html';
            } 
            // 아직 안 만든 페이지들만 알림창 띄우기
            // 가령: 260422: 수정 내용 - 수어학습 페이지 구현 완료로 alert 제거, href("learning.html")로 자연스럽게 이동
            else if (menuText === "수어검색") {
                alert(`${menuText} 페이지는 준비 중입니다.`);
            }
        };
    });

    // 로고 클릭 시 홈으로
    const logo = document.querySelector('.logo');
    if (logo) {
        logo.style.cursor = 'pointer';
        logo.onclick = () => { location.href = 'home.html'; };
    }


    /* -----------------------------------------------------------
       2. 로그인 / 로그아웃 상태 관리 (공통)
    ----------------------------------------------------------- */
    const authBtn = document.getElementById('headerAuthBtn') || document.querySelector('.login-btn');
    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[1]) : null;
    }
    const isLoggedIn = !!getCookie('access_token');

    if (authBtn) {
        if (isLoggedIn) {
            authBtn.innerText = "로그아웃";
            authBtn.classList.add('logout-style');
            authBtn.onclick = async () => {
                await fetch('/api/v1/auth/logout', { method: 'GET', credentials: 'include' });
                alert("로그아웃 되었습니다.");
                location.href = 'home.html';
            };
        } else {
            authBtn.innerText = "로그인";
            authBtn.classList.remove('logout-style');
            authBtn.onclick = () => {
                location.href = 'login.html';
            };
        }
    }

    // 로그인 -> 가입 이동
    const kakaoBtn = document.querySelector('.kakao-login-btn');
    if (kakaoBtn) {
        kakaoBtn.onclick = () => { location.href = 'register.html'; };
    }

    // 가입 폼 제출
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            localStorage.setItem('isLoggedIn', 'true');
            alert("가입이 완료되었습니다!");
            location.href = 'home.html';
        });
    }


    /* -----------------------------------------------------------
       3. 랭킹 데이터 (홈 화면 전용 - 요소가 있을 때만 실행)
    ----------------------------------------------------------- */
    // const rankingTable = document.getElementById('ranking-list');
    // if (rankingTable) {
    //     const rankingData = [
    //         { rank: 1, nick: "햄부기", count: 240, color: "#FAEFC9" },
    //         { rank: 2, nick: "가령밤빵", count: 235, color: "#EAD6E4" },
    //         { rank: 3, nick: "민영부기", count: 210, color: "#838DBA" },
    //         { rank: 4, nick: "박진웅", count: 198, color: "#9EB19A" },
    //         { rank: 5, nick: "신나는 나나밍", count: 184, color: "#B19A9A" }
    //     ];

    //     rankingData.forEach(item => {
    //         const row = document.createElement('div');
    //         row.className = 'rank-row';
    //         row.innerHTML = `
    //             <span>${item.rank}등</span>
    //             <span style="text-align: left; padding-left: 10px;">
    //                 <i class="p-circle" style="background-color: ${item.color}"></i>
    //                 ${item.nick}
    //             </span>
    //             <span style="color: #34436D; font-weight: 600;">${item.count}개</span>
    //         `;
    //         rankingTable.appendChild(row);
    //     });
    // }
    const URL_BASE = "http://127.0.0.1:8080";
    const rankingTable = document.getElementById('ranking-list');
    if (rankingTable) {
        async function fetchRanking() {
            try {
                const response = await fetch(`${URL_BASE}/api/v1/users/ranking`);                
                if (!response.ok) {
                    throw new Error('랭킹 데이터를 불러오는데 실패했습니다.');
                }
                
                const rankingData = await response.json();
                const updateTimeSpan = document.getElementById('ranking-update-time');
                if (updateTimeSpan) {
                    const now = new Date();
                    const year = now.getFullYear();
                    const month = String(now.getMonth() + 1).padStart(2, '0');
                    const date = String(now.getDate()).padStart(2, '0');
                    const hours = String(now.getHours()).padStart(2, '0');
                    const minutes = String(now.getMinutes()).padStart(2, '0');
                
                    updateTimeSpan.innerText = `${year}년 ${month}월 ${date}일 ${hours}시 ${minutes}분 기준`;
                }

                rankingTable.innerHTML = '';
                const defaultColors = ["#FAEFC9", "#EAD6E4", "#838DBA", "#9EB19A", "#B19A9A"];
                rankingData.forEach((item, index) => {
                    const row = document.createElement('div');
                    row.className = 'rank-row';
                    const profileHtml = item.profileImageUrl 
                        ? `<img src="${item.profileImageUrl}" alt="프사" class="p-circle" style="object-fit: cover;">`
                        : `<i class="p-circle" style="background-color: ${defaultColors[index % defaultColors.length]}"></i>`;

                    row.innerHTML = `
                        <span>${item.rank}등</span>
                        <span style="text-align: left; padding-left: 10px;">
                            ${profileHtml}
                            ${item.nickname}
                        </span>
                        <span style="color: #34436D; font-weight: 600;">${item.completedLearningCount}개</span>
                    `;
                    rankingTable.appendChild(row);
                });

            } catch (error) {
                console.error("랭킹 로드 에러:", error);
                rankingTable.innerHTML = '<div style="padding: 20px; text-align: center; font-size: 13px; color: #757575;">랭킹 데이터를 불러올 수 없습니다.</div>';
            }
        }

        fetchRanking();
    }

    // 홈 탭 버튼
    const tabBtns = document.querySelectorAll('.tab-btn');
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    }


    /* -----------------------------------------------------------
       4. TOP 버튼 (공통 - 요소가 있을 때만 실행)
    ----------------------------------------------------------- */
    const scrollTopBtn = document.getElementById('scrollTopBtn');
    if (scrollTopBtn) {
        scrollTopBtn.onclick = () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        };

        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                scrollTopBtn.classList.add('show');
            } else {
                scrollTopBtn.classList.remove('show');
            }
        });
    }


    /* -----------------------------------------------------------
       5. FAQ 카테고리 전환 (고객지원 전용 - 요소가 있을 때만 실행)
    ----------------------------------------------------------- */
    const faqTitle = document.getElementById('faq-title');
    const faqContent = document.getElementById('faq-content');
    const chips = document.querySelectorAll('.chip');

    if (faqTitle && faqContent && chips.length > 0) {
        const faqData = {
            "카메라 이슈": `<h3>브라우저 권한 설정</h3><p>주소창 왼쪽 자물쇠 아이콘을 눌러 허용해 주세요.</p>`,
            "순위 업데이트": `<h3>실시간 반영</h3><p>학습 즉시 경험치가 반영됩니다.</p>`,
            "카카오톡 채널": `<h3>1:1 문의</h3><p>상담 운영시간은 10:00 - 17:00입니다.</p>`,
            "학습 단어": `<h3>단어 업데이트</h3><p>매주 새로운 수어 단어가 추가됩니다.</p>`,
            "학습 알림": `<h3>Push 알림</h3><p>마이페이지에서 알림 시간을 설정하세요.</p>`,
            "수어 지원 문의": `<h3>영상 제보</h3><p>새로운 수어 영상을 기다리고 있습니다.</p>`,
            "후원 문의": `<h3>연구소 후원</h3><p>교육 콘텐츠 제작에 소중히 사용됩니다.</p>`
        };

        // 초기화
        faqContent.innerHTML = faqData["카메라 이슈"];

        chips.forEach(chip => {
            chip.onclick = () => {
                chips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                
                const category = chip.innerText.trim();
                faqTitle.innerText = `Q. ${category}`;
                faqContent.innerHTML = faqData[category] || "<p>준비 중...</p>";
            };
        });
    }

    /* -----------------------------------------------------------
       6. 간편가입 모두 동의 (가입 페이지 전용)
    ----------------------------------------------------------- */
    const checkAll = document.getElementById('checkAll');
    const otherChecks = document.querySelectorAll('.check-list input[type="checkbox"]');
    
    if (checkAll && otherChecks.length > 0) {
        checkAll.onchange = () => {
            otherChecks.forEach(cb => cb.checked = checkAll.checked);
        };
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('surveyOverlay');
    const nextBtn = document.getElementById('nextStep');
    const prevBtn = document.getElementById('prevStep');
    const finishBtn = document.getElementById('finishSurvey');
    const pages = document.querySelectorAll('.step-page');
    let step = 1;

    // --- ⭐ 핵심: 가입 직후 첫 로그인인지 체크 ---
    const needsSurvey = localStorage.getItem('needsSurvey') === 'true';
    if (overlay && needsSurvey) {
        overlay.style.display = 'flex';
    }

    // 카드 선택 처리
    document.querySelectorAll('.option-card').forEach(card => {
        card.onclick = () => {
            card.parentElement.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
        };
    });

    // 단계 이동 함수
    const moveStep = (direction) => {
        step += direction;
        pages.forEach((p, i) => p.classList.toggle('active', i + 1 === step));
        
        // 스태퍼 & 버튼 업데이트
        document.querySelectorAll('.step-item').forEach((s, i) => s.classList.toggle('active', i < step));
        document.querySelectorAll('.step-line').forEach((l, i) => l.classList.toggle('active', i < step - 1));

        prevBtn.style.visibility = step > 1 ? 'visible' : 'hidden';
        nextBtn.style.display = step < 3 ? 'block' : 'none';
        finishBtn.style.display = step === 3 ? 'block' : 'none';
    };

    nextBtn.onclick = () => moveStep(1);
    prevBtn.onclick = () => moveStep(-1);

    // 완료 버튼
    finishBtn.onclick = () => {
        localStorage.removeItem('needsSurvey'); // 티켓 삭제
        localStorage.setItem('surveyResults', 'done'); // 결과 저장 표시
        alert("맞춤 설정이 완료되었습니다!");
        overlay.style.display = 'none';
    };
});