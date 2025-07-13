document.addEventListener("DOMContentLoaded", () => {
  const tr = window.tr,
    roomInput = document.getElementById("room"),
    joinBtn = document.getElementById("joinBtn"),
    startBtn = document.getElementById("startBtn"),
    hangBtn = document.getElementById("hangupBtn"),
    inviteInp = document.getElementById("invite-link"),
    localVid = document.getElementById("localVideo"),
    remoteVid = document.getElementById("remoteVideo");
  let ws, pc, stream;

  window.copyInvite = () => {
    const room = roomInput.value.trim();
    if (!room) return alert(tr.enter_room);
    const url = `${location.origin}/?page=f2f&lang=${document.documentElement.lang}&room=${encodeURIComponent(room)}`;
    inviteInp.value = url;
    navigator.clipboard.writeText(url);
    alert(tr.link_copied);
  };

  joinBtn.onclick = () => {
    const room = roomInput.value.trim();
    if (!room) return alert(tr.enter_room);
    ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/${encodeURIComponent(room)}`);
    ws.onmessage = async e => {
      const msg = JSON.parse(e.data);
      if (msg.candidate) return pc.addIceCandidate(msg);
      if (msg.sdp) {
        await pc.setRemoteDescription(msg.sdp);
        if (msg.sdp.type === 'offer') {
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          ws.send(JSON.stringify({ sdp: pc.localDescription }));
        }
      }
    };
    document.getElementById("chatArea").style.display = "block";
  };

  startBtn.onclick = async () => {
    try { stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true }); }
    catch { return alert(tr.media_error); }
    localVid.srcObject = stream;
    pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
    pc.onicecandidate = e => e.candidate && ws.send(JSON.stringify(e.candidate));
    pc.ontrack = e => remoteVid.srcObject = e.streams[0];
    stream.getTracks().forEach(t => pc.addTrack(t, stream));
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    ws.send(JSON.stringify({ sdp: pc.localDescription }));
    startBtn.disabled = true; hangBtn.disabled = false;
  };

  hangBtn.onclick = () => {
    stream.getTracks().forEach(t => t.stop());
    pc.close(); ws.close();
    localVid.srcObject = null; remoteVid.srcObject = null;
    startBtn.disabled = false; hangBtn.disabled = true;
  };
});
