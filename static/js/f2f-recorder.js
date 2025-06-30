document.addEventListener('DOMContentLoaded', () => {
    const recvideo = document.getElementById('f2fvideo');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const f2fForm = document.getElementById('f2f-form');

    if (!startBtn || !recvideo || !stopBtn || !f2fForm) return;

    let chunks = [], recorder, stream;

    startBtn.onclick = async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            recvideo.srcObject = stream;
            recorder = new MediaRecorder(stream, { mimeType: 'video/webm' });

            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = () => {
                f2fForm.classList.remove('hidden');
            };

            recorder.start();
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
            chunks = [];

        } catch (err) {
            console.error("Error accessing media devices.", err);
            alert("Could not access camera and microphone.");
        }
    };

    stopBtn.onclick = () => {
        if (recorder && recorder.state === 'recording') {
            recorder.stop();
        }
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        stopBtn.style.display = 'none';
    };

    f2fForm.onsubmit = (event) => {
        event.preventDefault();

        const blob = new Blob(chunks, { type: 'video/webm' });
        const fileName = `${Date.now()}.webm`;
        const file = new File([blob], fileName, { type: 'video/webm' });

        const formData = new FormData(f2fForm);
        formData.append('file', file);

        const sendBtn = document.getElementById('send-btn');
        sendBtn.textContent = 'Uploading...';
        sendBtn.disabled = true;

        fetch(f2fForm.action, {
            method: 'POST',
            body: formData
        })
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    throw new Error('Upload failed, no redirect.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred during upload.');
                sendBtn.textContent = 'Send Video';
                sendBtn.disabled = false;
            });
    };
});