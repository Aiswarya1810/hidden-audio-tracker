function previewFile(event, previewId) {
    const file = event.target.files[0];
    const preview = document.getElementById(previewId);

    if (file) {
        preview.src = URL.createObjectURL(file);
        preview.style.display = "block";
    }
}

function previewAudio(event) {
    const file = event.target.files[0];
    const audio = document.getElementById("audioPreview");

    if (file) {
        audio.src = URL.createObjectURL(file);
        audio.style.display = "block";
    }
}