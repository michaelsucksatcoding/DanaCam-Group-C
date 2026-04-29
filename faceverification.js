// ================= DANACAM FACE VERIFICATION =================

// Ambil elemen dari register.html
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const statusText = document.getElementById("status");

// Jalankan kamera saat halaman dibuka
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });

        video.srcObject = stream;

        statusText.innerHTML = "Kamera aktif. Pastikan wajah terlihat jelas.";
    } catch (error) {
        statusText.innerHTML = "Kamera gagal diakses. Izinkan akses kamera.";
        console.error("Camera Error:", error);
    }
}

// Ambil gambar wajah dari kamera
function captureFace() {
    if (!video.srcObject) {
        statusText.innerHTML = "Kamera belum aktif.";
        return;
    }

    const context = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Simulasi verifikasi sederhana
    statusText.innerHTML = "Wajah berhasil diverifikasi! Mengalihkan ke halaman pinjaman...";

    // Simpan status verifikasi sementara
    localStorage.setItem("faceVerified", "true");

    // Pindah halaman setelah 2 detik
    setTimeout(() => {
        window.location.href = "pinjaman.html";
    }, 2000);
}

// Hentikan kamera (opsional)
function stopCamera() {
    if (video.srcObject) {
        let tracks = video.srcObject.getTracks();

        tracks.forEach(track => {
            track.stop();
        });

        video.srcObject = null;
    }
}

// Jalankan otomatis saat halaman register dibuka
window.onload = startCamera;
