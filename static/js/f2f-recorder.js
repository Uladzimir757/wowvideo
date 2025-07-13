document.addEventListener("DOMContentLoaded", () => {
  const recBtn = document.getElementById("f2f-rec-btn"),
    stopBtn = document.getElementById("f2f-stop-btn"),
    vid = document.getElementById("f2fvideo"),
    fileInp = document.getElementById("f2fblobfile"),
    sendBtn = document.getElementById("f2f-send-btn");
  let recorder, stream, chunks = [];

  recBtn.onclick = async () => {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    vid.srcObject = stream;
    recorder = new MediaRecorder(stream); chunks = [];
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: "video/webm" }),
        file = new File([blob], "f2f.webm"),
        dt = new DataTransfer();
      dt.items.add(file);
      fileInp.files = dt.files;
      sendBtn.hidden = false;
    };
    recorder.start();
    recBtn.hidden = true; stopBtn.hidden = false;
  };

  stopBtn.onclick = () => {
    recorder.stop();
    stream.getTracks().forEach(t => t.stop());
    stopBtn.hidden = true;
  };
});
