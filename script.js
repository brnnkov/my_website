const messageCell = document.querySelector('.contact-cell--message');

if (messageCell) {
    let resizeFrame;

    window.addEventListener('resize', () => {
        window.cancelAnimationFrame(resizeFrame);
        resizeFrame = window.requestAnimationFrame(() => {
            messageCell.style.width = '';
        });
    });
}
