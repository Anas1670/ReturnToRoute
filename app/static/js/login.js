"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");
    const message = document.getElementById("login-message");
    const submitButton = form.querySelector('button[type="submit"]');

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        message.textContent = "";
        submitButton.disabled = true;
        submitButton.textContent = "Signing In...";

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    email: email,
                    password: password,
                    role: document.getElementById("account-role").value
                })
            });

            const data = await response.json();

            if (!response.ok) {
                message.textContent =
                    data.error || "Login failed. Please try again.";
                return;
            }

            if (data.user && data.user.role === "customer") {
                window.location.href = "/customer/dashboard";
            } else if (data.user && data.user.role === "staff") {
                window.location.href = "/staff/dashboard";
            } else {
                message.textContent = "Unknown user role.";
            }

        } catch (error) {
            message.textContent =
                "Unable to connect to the server. Please try again.";
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Sign In";
        }
    });
});
