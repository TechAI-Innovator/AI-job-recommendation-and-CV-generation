document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('cv-upload-form');
  const progressBar = document.getElementById('progress-bar');
  const uploadStatus = document.getElementById('upload-status');
  const fileInput = document.getElementById('cv_file');
  const submitButton = uploadForm.querySelector("button[type='submit']");

  uploadForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
      alert("Please select a file.");
      return;
    }

    // File size and type validation
    if (file.size > 2 * 1024 * 1024) { // 2MB
      alert("File too large. Max size is 2MB.");
      fileInput.value = "";
      return;
    }

    if (!file.name.match(/\.(pdf|docx?)$/i)) {
      alert("Only PDF or Word documents are allowed.");
      fileInput.value = "";
      return;
    }

    const formData = new FormData(uploadForm);
    uploadStatus.classList.remove('hidden');
    progressBar.value = 0;
    submitButton.disabled = true;

    // Simulated progress (for visual feedback)
    let fakeProgress = 0;
    const progressInterval = setInterval(() => {
      fakeProgress += Math.random() * 10;
      progressBar.value = Math.min(100, fakeProgress);
      if (fakeProgress >= 100) clearInterval(progressInterval);
    }, 300);

    try {
      const response = await fetch('/extract_cv', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      // Fill name fields individually
      document.querySelector('input[name="first_name"]').value = data.first_name || '';
      document.querySelector('input[name="middle_name"]').value = data.middle_name || '';
      document.querySelector('input[name="surname"]').value = data.surname || '';

      // Contact details and summary
      document.querySelector('input[name="email"]').value = data.email || '';
      document.querySelector('input[name="phone"]').value = data.phone || '';
      document.querySelector('input[name="location"]').value = data.location || '';
      document.querySelector('input[name="linkedin"]').value = data.linkedin || '';
      document.querySelector('input[name="github"]').value = data.github || '';
      document.querySelector('input[name="skills"]').value = data.skills || '';
      document.querySelector('textarea[name="summary"]').value = data.summary || '';

      // Education
      if (data.education) {
        data.education.forEach((edu, index) => {
          if (index > 0) addEducation();
          const entry = document.querySelectorAll('.education-entry')[index];
          entry.querySelector('input[name="degree[]"]').value = edu.degree || '';
          entry.querySelector('input[name="institution[]"]').value = edu.institution || '';
          entry.querySelector('input[name="edu_year[]"]').value = edu.year || '';
          entry.querySelector('textarea[name="edu_description[]"]').value = edu.description || '';
        });
      }

      // Experience
      if (data.experience) {
        data.experience.forEach((exp, index) => {
          if (index > 0) addExperience();
          const entry = document.querySelectorAll('.experience-entry')[index];
          entry.querySelector('input[name="job_title[]"]').value = exp.title || '';
          entry.querySelector('input[name="company[]"]').value = exp.company || '';
          entry.querySelector('input[name="duration[]"]').value = exp.duration || '';
          entry.querySelector('textarea[name="exp_description[]"]').value = exp.description || '';
        });
      }

        // === RESUME PREVIEW SETUP ===
      if (data.uploaded_cv_path) {
        document.getElementById('uploaded-filename').textContent = file.name;
        document.getElementById('uploaded-resume-preview').classList.remove('hidden');
        document.getElementById('uploaded_cv_path').value = data.uploaded_cv_path;
        document.getElementById('resume_file').disabled = true;
      }

    } catch (error) {
      alert('Failed to extract CV. Please try again.');
      console.error(error);
    } finally {
      uploadStatus.classList.add('hidden');
      submitButton.disabled = false;
    }
  });

  // Manual validation for initial upload
  fileInput.addEventListener("change", function () {
    const file = this.files[0];
    if (file && file.size > 2 * 1024 * 1024) {
      alert("File too large. Max size is 2MB.");
      this.value = "";
    }

    if (file && !file.name.match(/\.(pdf|docx?)$/i)) {
      alert("Only PDF or Word documents are allowed.");
      this.value = "";
    }
  });
});

// === Resume Section: Remove Uploaded Resume ===
function removeUploadedResume() {
  const resumePath = document.getElementById("uploaded_cv_path").value;

  fetch("/delete_cv", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_path: resumePath }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.message) {
        document.getElementById("uploaded-resume-preview").classList.add("hidden");
        document.getElementById("uploaded_cv_path").value = "";
        const resumeInput = document.getElementById("resume_file");
        resumeInput.disabled = false;
        resumeInput.value = "";
      } else {
        alert("Failed to delete resume. Please try again.");
      }
    });
}


// === Education/Experience Add/Remove ===
function addEducation() {
  const section = document.getElementById('education-section');
  const clone = section.firstElementChild.cloneNode(true);
  Array.from(clone.querySelectorAll('input, textarea')).forEach(input => input.value = '');
  section.appendChild(clone);
}

function addExperience() {
  const section = document.getElementById('experience-section');
  const clone = section.firstElementChild.cloneNode(true);
  Array.from(clone.querySelectorAll('input, textarea')).forEach(input => input.value = '');
  section.appendChild(clone);
}

function removeSection(button) {
  const entry = button.closest('.education-entry, .experience-entry');
  if (entry && entry.parentElement.children.length > 1) {
    entry.remove();
  }
}


function addLocationRow() {
  const container = document.getElementById("location-preference-list");
  const row = document.createElement("div");
  row.classList.add("location-preference-row");

  row.innerHTML = `
    <div class="location-preference-row">
      <input type="text" name="locations[]" placeholder="e.g. Nigeria, USA" required>
      <label><input type="checkbox" name="worktypes_${locationIndex}[]" value="remote"> Remote</label>
      <label><input type="checkbox" name="worktypes_${locationIndex}[]" value="on-site"> On-site</label>
      <label><input type="checkbox" name="worktypes_${locationIndex}[]" value="hybrid"> Hybrid</label>
    </div>
      <button type="button" class="remove-btn" onclick="removeLocationRow(this)">Remove</button>
  `;

  container.appendChild(row);
  locationIndex++;
}

function removeLocationRow(button) {
  const row = button.closest('.location-preference-row');
  const container = document.getElementById("location-preference-list");

  if (container.children.length > 1) {
    // Add fade-out class to trigger CSS animation
    row.classList.add("fade-out");

    // Wait for the animation to finish before removing
    setTimeout(() => {
      container.removeChild(row);
    }, 300); // Match this with CSS transition duration
  }
}
