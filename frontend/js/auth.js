/* ──────────────────────────────────────────────────────────
   auth.js - 공통 헤더 처리 (로그인/로그아웃 버튼, 네비게이션 활성화)
   모든 페이지에서 <script src="../js/auth.js"></script> 로 포함
   ────────────────────────────────────────────────────────── */

function getCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
}

document.addEventListener('DOMContentLoaded', () => {

    /* ── 1. 현재 페이지에 맞는 nav 링크 강조 ── */
    const currentPage = location.pathname.split('/').pop();
    document.querySelectorAll('.nav-bar a').forEach(a => {
        const href = a.getAttribute('href');
        if (href === currentPage) {
            a.classList.add('active');
        } else {
            a.classList.remove('active');
        }
    });

    /* ── 2. 네비게이션 클릭 시 경고창 없이 바로 이동 ── */
    document.querySelectorAll('.nav-bar a').forEach(a => {
        a.onclick = null; // 기존 onclick 제거
    });

    /* ── 3. 로그인/로그아웃 버튼 처리 ── */
    const authBtn = document.getElementById('headerAuthBtn');
    if (!authBtn) return;

    const token = getCookie('access_token');

    if (token) {
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
    } else {
        authBtn.innerText = '로그인';
        authBtn.classList.remove('logout-style');
        authBtn.onclick = () => {
            location.href = 'login.html';
        };
    }
});