document.addEventListener('DOMContentLoaded', () => {
    const video = document.querySelector('#player');
    
    if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource('https://ifbest.org/your-video-source.m3u8');
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, function() {
            video.play().catch(e => console.log("Autoplay prevented:", e));
        });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = 'https://ifbest.org/your-video-source.m3u8';
        video.addEventListener('loadedmetadata', function() {
            video.play().catch(e => console.log("Autoplay prevented:", e));
        });
    }

    const player = new Plyr(video, {
        controls: [
            'play-large', 
            'play', 
            'progress', 
            'current-time', 
            'mute', 
            'volume', 
            'captions', 
            'settings', 
            'pip', 
            'airplay', 
            'fullscreen'
        ],
        ratio: '16:9'
    });

    const menuToggle = document.getElementById('menuToggle');
    const sideMenu = document.getElementById('sideMenu');
    
    menuToggle.addEventListener('click', () => {
        sideMenu.classList.toggle('active');
        menuToggle.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
        if (!sideMenu.contains(e.target) && e.target !== menuToggle) {
            sideMenu.classList.remove('active');
            menuToggle.classList.remove('active');
        }
    });
});