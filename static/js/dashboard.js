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
            selectedRating = index;
            updateStars();
        });

        star.addEventListener('mouseover', () => {
            highlightStars(index);
        });

        star.addEventListener('mouseout', () => {
            highlightStars(selectedRating);
        });
    });

    function highlightStars(activeIndex) {
        stars.forEach((star, i) => {
            star.classList.toggle('text-yellow-400', i <= activeIndex);
            star.classList.toggle('text-gray-400', i > activeIndex);
        });
    }

    function updateStars() {
        highlightStars(selectedRating);
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
