(function () {
    "use strict";

    const configElement = document.getElementById("safety-data-admin-config");
    if (!configElement) {
        return;
    }

    const config = JSON.parse(configElement.textContent);
    const strings = config.strings;
    const api = config.api;

    const grantSelect = document.getElementById("grant");
    const emailInput = document.getElementById("email");
    const grantForm = document.getElementById("grant-form");
    const lookupBtn = document.getElementById("lookup-btn");
    const submitBtn = document.getElementById("submit-btn");
    const messageEl = document.getElementById("message");
    const allGrantsList = document.getElementById("all-grants-list");
    const userGrantsCard = document.getElementById("user-grants-card");
    const userGrantsContent = document.getElementById("user-grants-content");

    let grants = [];
    let lookupEmail = "";

    function showMessage(text, type) {
        messageEl.textContent = text;
        messageEl.className = "message visible " + type;
    }

    function hideMessage() {
        messageEl.className = "message";
        messageEl.textContent = "";
    }

    function setFormBusy(isBusy) {
        submitBtn.disabled = isBusy;
        lookupBtn.disabled = isBusy;
    }

    async function apiFetch(path, options) {
        try {
            const response = await fetch(path, {
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                ...options,
            });
            let data = null;
            const contentType = response.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                data = await response.json();
            }
            return { response, data };
        } catch (error) {
            return { response: { ok: false }, data: null, networkError: true };
        }
    }

    function parseError(data, fallback) {
        if (!data) {
            return fallback;
        }
        if (data.error_msg) {
            return data.error_msg;
        }
        if (Array.isArray(data.error_msg_args) && data.error_msg_args.length) {
            return data.error_msg_args.join(" ");
        }
        return fallback;
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function formatString(template, params) {
        return template.replace(/\{(\w+)\}/g, function (_match, key) {
            return params[key] !== undefined ? params[key] : "";
        });
    }

    function renderAllGrants() {
        if (!grants.length) {
            allGrantsList.innerHTML =
                '<li class="empty-state">' + escapeHtml(strings.noGrantsInSystem) + "</li>";
            return;
        }
        allGrantsList.innerHTML = grants
            .map(function (grant) {
                const description = grant.description
                    ? '<div class="grant-meta">' + escapeHtml(grant.description) + "</div>"
                    : "";
                return (
                    "<li>" +
                    "<div><strong>" +
                    escapeHtml(grant.name) +
                    "</strong>" +
                    description +
                    "</div>" +
                    "</li>"
                );
            })
            .join("");
    }

    function populateGrantSelect() {
        if (!grants.length) {
            grantSelect.innerHTML =
                '<option value="">' + escapeHtml(strings.noGrantsAvailable) + "</option>";
            return;
        }
        grantSelect.innerHTML =
            '<option value="">' + escapeHtml(strings.selectGrant) + "</option>" +
            grants
                .map(function (grant) {
                    return (
                        '<option value="' +
                        escapeHtml(grant.name) +
                        '">' +
                        escapeHtml(grant.name) +
                        "</option>"
                    );
                })
                .join("");
    }

    function renderUserGrants(user) {
        userGrantsCard.hidden = false;

        if (!user) {
            userGrantsContent.innerHTML =
                '<p class="empty-state">' + escapeHtml(strings.userNotFound) + "</p>";
            return;
        }

        const userGrants = user.grants || [];
        if (!userGrants.length) {
            userGrantsContent.innerHTML =
                "<p><strong>" +
                escapeHtml(user.email) +
                "</strong></p>" +
                '<p class="empty-state">' +
                escapeHtml(strings.userHasNoGrants) +
                "</p>";
            return;
        }

        const items = userGrants
            .map(function (grantName) {
                return (
                    "<li>" +
                    "<span>" +
                    escapeHtml(grantName) +
                    "</span>" +
                    '<button type="button" class="btn-danger remove-grant-btn" data-grant="' +
                    escapeHtml(grantName) +
                    '">' +
                    escapeHtml(strings.removeGrant) +
                    "</button>" +
                    "</li>"
                );
            })
            .join("");

        userGrantsContent.innerHTML =
            "<p><strong>" +
            escapeHtml(user.email) +
            "</strong></p>" +
            '<ul class="grant-list">' +
            items +
            "</ul>";
    }

    async function loadGrants() {
        const { response, data, networkError } = await apiFetch(api.getGrantsList);
        if (networkError) {
            showMessage(strings.networkError, "error");
            grantSelect.innerHTML =
                '<option value="">' + escapeHtml(strings.loadError) + "</option>";
            allGrantsList.innerHTML =
                '<li class="empty-state">' + escapeHtml(strings.loadError) + "</li>";
            return;
        }
        if (!response.ok) {
            showMessage(parseError(data, strings.loadGrantsError), "error");
            grantSelect.innerHTML =
                '<option value="">' + escapeHtml(strings.loadError) + "</option>";
            allGrantsList.innerHTML =
                '<li class="empty-state">' + escapeHtml(strings.loadError) + "</li>";
            return;
        }
        grants = data || [];
        populateGrantSelect();
        renderAllGrants();
    }

    async function lookupUserGrants() {
        hideMessage();
        const email = emailInput.value.trim();
        if (!email) {
            showMessage(strings.emailRequired, "error");
            return;
        }

        lookupEmail = email;
        setFormBusy(true);
        const { response, data, networkError } = await apiFetch(api.getAllUsersInfo);
        setFormBusy(false);

        if (networkError) {
            showMessage(strings.networkError, "error");
            return;
        }
        if (!response.ok) {
            showMessage(parseError(data, strings.loadUsersError), "error");
            return;
        }

        const user = (data || []).find(function (item) {
            return item.email && item.email.toLowerCase() === email.toLowerCase();
        });
        renderUserGrants(user);
    }

    async function addGrant(email, grant) {
        hideMessage();
        setFormBusy(true);
        const { response, data, networkError } = await apiFetch(api.addToGrant, {
            method: "POST",
            body: JSON.stringify({ email: email, grant: grant }),
        });
        setFormBusy(false);

        if (networkError) {
            showMessage(strings.networkError, "error");
            return false;
        }
        if (!response.ok) {
            showMessage(parseError(data, strings.addGrantError), "error");
            return false;
        }
        showMessage(formatString(strings.grantAddedSuccess, { grant: grant, email: email }), "success");
        return true;
    }

    async function removeGrant(email, grant) {
        hideMessage();
        setFormBusy(true);
        const { response, data, networkError } = await apiFetch(api.removeFromGrant, {
            method: "POST",
            body: JSON.stringify({ email: email, grant: grant }),
        });
        setFormBusy(false);

        if (networkError) {
            showMessage(strings.networkError, "error");
            return;
        }
        if (!response.ok) {
            showMessage(parseError(data, strings.removeGrantError), "error");
            return;
        }
        showMessage(formatString(strings.grantRemovedSuccess, { grant: grant, email: email }), "success");
        await lookupUserGrants();
    }

    grantForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const email = emailInput.value.trim();
        const grant = grantSelect.value;
        if (!email || !grant) {
            showMessage(strings.emailAndGrantRequired, "error");
            return;
        }
        const success = await addGrant(email, grant);
        if (success) {
            await lookupUserGrants();
        }
    });

    lookupBtn.addEventListener("click", lookupUserGrants);

    userGrantsContent.addEventListener("click", async function (event) {
        const button = event.target.closest(".remove-grant-btn");
        if (!button || !lookupEmail) {
            return;
        }
        await removeGrant(lookupEmail, button.dataset.grant);
    });

    loadGrants();
})();
