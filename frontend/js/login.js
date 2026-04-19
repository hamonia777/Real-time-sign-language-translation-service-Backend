// 가령: 26/04/19 수정내용: 카카오 로그인 버튼 클릭 시 백엔드 /api/v1/auth/login/kakao 로 이동하도록 핸들러 추가
document.addEventListener('DOMContentLoaded', () => {
    const kakaoBtn = document.querySelector('.kakao-login-btn');
    if (kakaoBtn) {
        kakaoBtn.addEventListener('click', () => {
            window.location.href = '/api/v1/auth/login/kakao';
        });
    }
});
