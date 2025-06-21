function generateCV(type) {
    const loadingState = document.getElementById('loadingState');
    const optionsState = document.getElementById('optionsState');
    const previewState = document.getElementById('previewState');
    const cvPreviewFrame = document.getElementById('cvPreviewFrame');
    const downloadLink = document.getElementById('downloadCvLink');

    // UI: show loading spinner
    optionsState.classList.add('hidden');
    loadingState.classList.remove('hidden');

    // Get job ID from URL (assumes route like/generate-cv/<job_id>)
    const jobId = window.location.pathname.split('/').pop();

    // Choose endpoint based on type
    const endpoint = type === 'template'
        ? `/api/generate-initial-format-cv/${jobId}`
        : `/api/generate-llm-format-cv/${jobId}`;

    fetch(endpoint)
        .then(response => {
            if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.messages?.join("\n") || "Failed to generate CV.");
            });
        }
            return response.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            cvPreviewFrame.src = url;
            downloadLink.href = url;
            downloadLink.download = `generated_cv_${jobId}.pdf`;

            // UI: show preview
            loadingState.classList.add('hidden');
            previewState.classList.remove('hidden');
        })
        .catch(error => {
            console.error("CV Generation Error:", error);
            alert(error.message);
            resetGenerator();
        });
}

function resetGenerator() {
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('previewState').classList.add('hidden');
    document.getElementById('optionsState').classList.remove('hidden');
}
