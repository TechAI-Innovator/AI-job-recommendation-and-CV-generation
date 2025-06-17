document.addEventListener('DOMContentLoaded', function () {
    // === Scroll Buttons ===
    const container = document.getElementById('jobCardsContainer');
    const scrollLeftBtn = document.getElementById('scrollLeft');
    const scrollRightBtn = document.getElementById('scrollRight');

    if (scrollLeftBtn && container) {
        scrollLeftBtn.addEventListener('click', () => {
            container.scrollBy({ left: -340, behavior: 'smooth' });
        });
    }

    if (scrollRightBtn && container) {
        scrollRightBtn.addEventListener('click', () => {
            container.scrollBy({ left: 340, behavior: 'smooth' });
        });
    }

    // === Star Rating ===
    const stars = document.querySelectorAll('.ri-star-fill');
    let selectedRating = -1;

    stars.forEach((star, index) => {
        star.addEventListener('click', () => {
            selectedRating = index + 1;  // now rating is 1 to 5
            updateStars();
        });

        star.addEventListener('mouseover', () => {
            highlightStars(index);
        });

        star.addEventListener('mouseout', () => {
            highlightStars(selectedRating - 1);
        });
    });

    function highlightStars(activeIndex) {
        stars.forEach((star, i) => {
            star.classList.toggle('text-yellow-400', i <= activeIndex);
            star.classList.toggle('text-gray-400', i > activeIndex);
        });
    }

    function updateStars() {
        highlightStars(selectedRating - 1);
    }

    // === Feedback Submission ===
    const submitBtn = document.getElementById("submitFeedback");
    const feedbackTextarea = document.getElementById("feedback");

    if (submitBtn && feedbackTextarea) {
        submitBtn.addEventListener("click", async () => {
            const message = feedbackTextarea.value.trim();

            if (selectedRating < 1 || message === "") {
                alert("Please rate and provide feedback.");
                return;
            }

            try {
                const res = await fetch("/submit-feedback", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        rating: selectedRating,
                        message: message
                    })
                });

                const data = await res.json();

                if (res.ok) {
                    alert("Thank you for your feedback!");
                    feedbackTextarea.value = "";
                    selectedRating = -1;
                    updateStars();
                } else {
                    alert("Error: " + data.message);
                }
            } catch (err) {
                alert("Something went wrong. Try again.");
                console.error(err);
            }
        });
    }

    // === Start Button Scraping ===
    const startButton = document.getElementById('startButton');

    function setStartButtonState(state) {
        if (!startButton) return;
        switch (state) {
            case 'loading':
                startButton.disabled = true;
                startButton.textContent = "Scraping...";
                break;
            case 'done':
                startButton.textContent = "Done!";
                break;
            case 'error':
                startButton.textContent = "Error! Try Again";
                break;
            case 'ready':
            default:
                startButton.disabled = false;
                startButton.textContent = "Start Scraping";
                break;
        }
    }

    if (startButton) {
        startButton.addEventListener('click', async function () {
            setStartButtonState('loading');

            try {
                const response = await fetch('/scrape-jobs', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) throw new Error("Scraping failed");

                const data = await response.json();
                console.log(data);
                setStartButtonState('done');
                container?.scrollIntoView({ behavior: 'smooth' });

            } catch (error) {
                console.error(error);
                setStartButtonState('error');
            } finally {
                setTimeout(() => {
                    setStartButtonState('ready');
                }, 3000);
            }
        });
    }
});
