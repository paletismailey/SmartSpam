const themeToggle =
    document.getElementById("themeToggle");


if (themeToggle) {

    themeToggle.addEventListener(
        "click",
        function () {

            document.body.classList.toggle(
                "light-mode"
            );

            localStorage.setItem(
                "theme",
                document.body.classList.contains(
                    "light-mode"
                )
                    ? "light"
                    : "dark"
            );

        }
    );

}


// Load saved theme

if (localStorage.getItem("theme") === "light") {

    document.body.classList.add(
        "light-mode"
    );

}


// Character and word counter

const messageBox =
    document.getElementById("message");

const charCount =
    document.getElementById("charCount");

const wordCount =
    document.getElementById("wordCount");


if (messageBox) {

    function updateCount() {

        const text =
            messageBox.value;

        const characters =
            text.length;

        const words =
            text.trim() === ""
                ? 0
                : text.trim().split(/\s+/).length;


        if (charCount) {

            charCount.textContent =
                characters + " characters";

        }


        if (wordCount) {

            wordCount.textContent =
                words + " words";

        }

    }


    messageBox.addEventListener(
        "input",
        updateCount
    );


    updateCount();

}