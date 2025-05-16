document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("resetForm");
  const sendBtn = document.getElementById("sendBtn");
  const cooldownPeriod = 60; // in seconds

  // Check if there's a saved timestamp
  const lastSent = localStorage.getItem("resetLastSent");

  if (lastSent) {
      const secondsPassed = Math.floor((Date.now() - parseInt(lastSent)) / 1000);
      if (secondsPassed < cooldownPeriod) {
          startCountdown(cooldownPeriod - secondsPassed);
      }
  }

  // Disable submission when offline
  form.addEventListener("submit", (e) => {
      if (!navigator.onLine) {
          e.preventDefault();
          alert("You're offline. Please check your internet connection and try again.");
          return;
      }

      // Save the current timestamp to localStorage
      localStorage.setItem("resetLastSent", Date.now().toString());
      // Allow the form to submit normally so flash message shows
  });

  // Offline/Online UI handling
  window.addEventListener("offline", () => {
      sendBtn.disabled = true;
      sendBtn.textContent = "You're offline";
  });

  window.addEventListener("online", () => {
      const lastSent = localStorage.getItem("resetLastSent");
      if (lastSent) {
          const secondsPassed = Math.floor((Date.now() - parseInt(lastSent)) / 1000);
          if (secondsPassed < cooldownPeriod) {
              startCountdown(cooldownPeriod - secondsPassed);
          } else {
              sendBtn.disabled = false;
              sendBtn.textContent = "Send Reset Link";
          }
      } else {
          sendBtn.disabled = false;
          sendBtn.textContent = "Send Reset Link";
      }
  });

  function startCountdown(duration) {
      let countdown = duration;
      sendBtn.disabled = true;
      sendBtn.textContent = `Wait ${countdown}s`;

      const interval = setInterval(() => {
          countdown--;
          sendBtn.textContent = `Wait ${countdown}s`;

          if (countdown <= 0) {
              clearInterval(interval);
              sendBtn.disabled = false;
              sendBtn.textContent = "Send Reset Link";
              localStorage.removeItem("resetLastSent");
          }
      }, 1000);
  }
});
