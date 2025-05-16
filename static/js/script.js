function validatePassword() {
    let password = document.getElementById("password").value;
    let confirmPassword = document.getElementById("confirm_password").value;
    let errorMessage = document.getElementById("error-message");

    if (password !== confirmPassword) {
        errorMessage.textContent = "Passwords do not match!";
        return false;  // Prevent form submission
    }

    errorMessage.textContent = ""; // Clear error if passwords match
    return true; // Allow form submission
}



document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".container");
    const sections = document.querySelectorAll(".slide-section");
    
    const homeBtn = document.getElementById("homeBtn");
    const loginBtn = document.getElementById("loginBtn");
    const registerBtn = document.getElementById("registerBtn");
    const goToRegister = document.getElementById("goToRegister");
    const goToLogin = document.getElementById("goToLogin");

    function slideTo(index) {
        container.style.transform = `translateX(-${index * 33.3333}%)`;
        sections.forEach((section, i) => {
            section.style.setProperty('--border-color', getColorForIndex(i));
        });
    }

    function getColorForIndex(index) {
        const colors = ["#2196F3", "#4CAF50", "#673AB7"];
        return colors[index] || "#2196F3";
    }

    // ⛔ Disable animation initially
    container.style.transition = "none";

    // Jump instantly based on hash (no animation)
    const hash = window.location.hash;
    if (hash === "#login") {
        slideTo(1);
    } else if (hash === "#register") {
        slideTo(2);
    } else {
        slideTo(0);
    }

    // ✅ Re-enable animation after 100ms
    setTimeout(() => {
        container.style.transition = "transform 0.6s ease";
    }, 100);

    // Button navigation (with animation)
    homeBtn.addEventListener("click", () => {
        slideTo(0);
        window.location.hash = "";
    });

    loginBtn.addEventListener("click", () => {
        slideTo(1);
        window.location.hash = "login";
    });

    registerBtn.addEventListener("click", () => {
        slideTo(2);
        window.location.hash = "register";
    });

    goToRegister.addEventListener("click", () => {
        slideTo(2);
        window.location.hash = "register";
    });

    goToLogin.addEventListener("click", () => {
        slideTo(1);
        window.location.hash = "login";
    });
});

