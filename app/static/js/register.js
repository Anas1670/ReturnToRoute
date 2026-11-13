"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("register-form");
    const message = document.getElementById("register-message");
    const submitButton = form.querySelector(
        'button[type="submit"]'
    );

    const genderSelect = document.getElementById("gender");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const fullName = document
            .getElementById("full-name").value.trim();

        const email = document
            .getElementById("email").value.trim();

        const phoneNumber = document
            .getElementById("phone-number").value.trim();

        const dateOfBirth = document
            .getElementById("date-of-birth").value;

        const password = document
            .getElementById("password").value;

        const confirmPassword = document
            .getElementById("confirm-password").value;

        let gender = genderSelect.value;

        message.textContent = "";

        if (password !== confirmPassword) {
            message.textContent = "Passwords do not match.";
            return;
        }

        if (dateOfBirth > new Date().toLocaleDateString("en-CA")) {
            message.textContent =
                "Date of birth cannot be in the future.";
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "Creating Account...";

        try {
            const response = await fetch("/api/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    full_name: fullName,
                    email: email,
                    phone_number: phoneNumber,
                    date_of_birth: dateOfBirth,
                    gender: gender,
                    password: password,
                    role: document.getElementById("account-role").value
                })
            });

            const data = await response.json();

            if (!response.ok) {
                message.textContent = data.error ||
                    "Registration failed. Please try again.";
                return;
            }

            window.location.href = "/login";

        } catch (error) {
            message.textContent =
                "Unable to connect to the server. Please try again.";

        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Create Account";
        }
    });
});
