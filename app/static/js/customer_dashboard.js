"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const welcome = document.getElementById("customer-welcome");
    const message = document.getElementById("dashboard-message");
    const purchaseCount = document.getElementById("purchase-count");
    const returnCount = document.getElementById("return-count");
    const purchasesContainer = document.getElementById("purchases-container");
    const returnsContainer = document.getElementById("returns-container");
    const historyContainer = document.getElementById("history-container");
    const logoutButton = document.getElementById("logout-button");
    const returnForm = document.getElementById("return-request-form");
    const returnSelect = document.getElementById("return-order-item");
    const returnMessage = document.getElementById("return-request-message");
    let eligiblePurchases = new Map();

    function createElement(tag, text, className) {
        const element = document.createElement(tag);

        if (text !== undefined && text !== null) {
            element.textContent = String(text);
        }

        if (className) {
            element.className = className;
        }

        return element;
    }

    function displayValue(value) {
        return value === null || value === undefined || value === ""
            ? "Not available"
            : String(value);
    }

    function displayDate(value) {
        if (!value) {
            return "Not available";
        }

        const date = new Date(value);

        return Number.isNaN(date.getTime())
            ? String(value)
            : date.toLocaleDateString();
    }

    function addDetail(parent, label, value) {
        const paragraph = createElement("p");
        const strong = createElement("strong", label + ": ");

        paragraph.appendChild(strong);
        paragraph.appendChild(
            document.createTextNode(displayValue(value))
        );

        parent.appendChild(paragraph);
    }

    // RTR_CLICK_TO_RETURN_5982: presentation-only order number cleanup.
    function friendlyOrderNumber(value) {
        const raw = String(value ?? "");
        return raw.replace(/^RTR-DEMO-/i, "RTR-");
    }

    function selectPurchaseForReturn(purchase) {
        if (!purchase.can_request_return) return;
        const key = String(purchase.order_item_id);
        if (!eligiblePurchases.has(key)) return;
        returnSelect.value = key;
        rtrSelectedImage(purchase);
        returnMessage.textContent = `Selected: ${purchase.product_name} — ${formatPurchasePrice(purchase.unit_price)}`;
        document.getElementById("return-request-section").scrollIntoView({behavior: "smooth", block: "start"});
        returnSelect.focus({preventScroll: true});
    }

    // RTR_PRODUCT_THUMBNAILS_5984: self-hosted illustrations, no external URLs.
    // RTR_REAL_THUMBNAILS_5985: match names without the broken regex escape.
    // RTR_OPENVERSE_PHOTOS_5986: stable product-ID mapping with illustrated fallback.
    let rtrPurchases = [];
    let rtrReturns = [];
    function rtrFindPurchase(record) {
        return rtrPurchases.find(p =>
            (record.order_item_id != null && String(p.order_item_id) === String(record.order_item_id)) ||
            (record.return_id != null && rtrReturns.some(r =>
                String(r.return_id) === String(record.return_id) &&
                r.order_item_id != null && String(r.order_item_id) === String(p.order_item_id)))
        );
    }
    function productThumbnail(name, productId) {
        const value = String(name || "").toLowerCase();
        const types = ["headphones","backpack","notebook","organizer","speaker","bottle","pillow","shirt","mouse","cable","stand","lamp","towel","case","mug"];
        const type = types.find(t => value.includes(t)) || "package";
        const img = document.createElement("img");
        img.className = "rtr-product-thumbnail";
        img.width = 76; img.height = 76;
        img.loading = "lazy"; img.decoding = "async";
        img.alt = `Product photo: ${name}`;
        const file = (window.RTR_PRODUCT_IMAGES || {})[String(productId)];
        const fallback = `/static/images/product-thumbnails/${type}.svg`;
        img.onerror = () => { img.onerror = null; img.src = fallback; };
        img.src = file ? `/static/images/catalog/${encodeURIComponent(file)}` : fallback;
        return img;
    }
    function rtrSelectedImage(purchase) {
        const panel = document.getElementById("rtr-selected-product");
        if (!panel) return;
        panel.replaceChildren();
        panel.hidden = !purchase;
        if (!purchase) return;
        panel.appendChild(productThumbnail(purchase.product_name, purchase.product_id));
        const detail = createElement("div", null, "rtr-selected-details");
        detail.appendChild(createElement("strong", purchase.product_name));
        detail.appendChild(createElement("p", formatPurchasePrice(purchase.unit_price)));
        panel.appendChild(detail);
    }
    returnSelect.addEventListener("change", () => rtrSelectedImage(eligiblePurchases.get(returnSelect.value)));

    function showPurchases(purchases) {
        purchasesContainer.replaceChildren();

        if (purchases.length === 0) {
            purchasesContainer.appendChild(
                createElement(
                    "p",
                    "No purchases found for your account."
                )
            );
            return;
        }

        const grid = createElement("div", null, "feature-grid");

        // Keep every real order visible; avoid repeated photo files in this purchase grid.
        // This does NOT change product IDs, orders, return eligibility, or the manifest.
        const photoManifest = window.RTR_PRODUCT_IMAGES || {};
        const photoTypes = ["headphones","backpack","notebook","organizer","speaker","bottle","pillow","shirt","mouse","cable","stand","lamp","towel","case","mug"];
        // RTR_ALL_LOCAL_CATALOG_PHOTOS_START
        const allLocalCatalogPhotos = ["backpack_01.webp", "backpack_02.webp", "backpack_03.webp", "backpack_04.webp", "bottle_001.webp", "bottle_002.webp", "bottle_003.webp", "bottle_004.webp", "bottle_005.webp", "bottle_006.webp", "bottle_007.webp", "cable_006.webp", "cable_007.webp", "cable_02.webp", "cable_03.webp", "cable_04.webp", "case_002.webp", "case_003.webp", "case_004.webp", "case_005.webp", "case_006.webp", "case_007.webp", "headphones_005.webp", "headphones_006.webp", "headphones_007.webp", "headphones_008.webp", "headphones_009.webp", "headphones_01.webp", "headphones_010.webp", "headphones_011.webp", "headphones_012.webp", "headphones_013.webp", "headphones_014.webp", "headphones_015.webp", "headphones_02.webp", "headphones_03.webp", "headphones_04.webp", "lamp_002.webp", "lamp_003.webp", "lamp_004.webp", "lamp_005.webp", "lamp_006.webp", "lamp_007.webp", "lamp_008.webp", "lamp_009.webp", "mouse_005.webp", "mouse_007.webp", "mouse_008.webp", "mouse_009.webp", "mouse_01.webp", "mouse_010.webp", "mouse_011.webp", "mouse_02.webp", "mouse_03.webp", "mouse_04.webp", "mug_002.webp", "mug_003.webp", "mug_004.webp", "mug_005.webp", "mug_007.webp", "mug_008.webp", "mug_009.webp", "mug_01.webp", "mug_010.webp", "mug_011.webp", "mug_012.webp", "mug_013.webp", "mug_014.webp", "mug_015.webp", "mug_018.webp", "mug_020.webp", "mug_021.webp", "mug_022.webp", "mug_025.webp", "mug_026.webp", "mug_027.webp", "mug_028.webp", "mug_029.webp", "mug_031.webp", "notebook_005.webp", "notebook_006.webp", "notebook_007.webp", "notebook_008.webp", "organizer_006.webp", "organizer_007.webp", "pillow_01.webp", "pillow_02.webp", "pillow_03.webp", "shirt_005.webp", "shirt_006.webp", "shirt_007.webp", "shirt_009.webp", "shirt_01.webp", "shirt_010.webp", "shirt_03.webp", "shirt_04.webp", "speaker_001.webp", "speaker_002.webp", "speaker_003.webp", "stand_002.webp", "stand_003.webp", "stand_004.webp", "towel_004.webp", "towel_007.webp", "towel_008.webp"];
        // RTR_ALL_LOCAL_CATALOG_PHOTOS_END
        const photosByType = new Map(photoTypes.map(type => [type, []]));
        for (const filename of [...allLocalCatalogPhotos, ...Object.values(photoManifest)]) {
            if (typeof filename !== "string") continue;
            const type = photoTypes.find(type => filename.startsWith(type + "_"));
            if (type && !photosByType.get(type).includes(filename)) photosByType.get(type).push(filename);
        }
        const usedPurchasePhotos = new Set();
        function distinctPurchaseThumbnail(purchase) {
            const type = photoTypes.find(type => String(purchase.product_name || "").toLowerCase().includes(type));
            const preferred = photoManifest[String(purchase.product_id)];
            const options = type ? photosByType.get(type) : [];
            const selected = [preferred, ...options].find(file =>
                typeof file === "string" && (!type || file.startsWith(type + "_")) && !usedPurchasePhotos.has(file)
            );
            if (!selected) {
                // A real photo is preferred to an illustration when a category is exhausted.
                // Reuse the least recently used same-category photo if no distinct one exists.
                const realOptions = [preferred, ...options].filter(file =>
                    typeof file === "string" && (!type || file.startsWith(type + "_"))
                );
                const reused = realOptions.find(file => file !== preferred) || realOptions[0];
                if (reused) {
                    const image = productThumbnail(purchase.product_name, purchase.product_id);
                    image.src = `/static/images/catalog/${encodeURIComponent(reused)}`;
                    return image;
                }
                // No photograph exists in this category at all.
                return productThumbnail(purchase.product_name, purchase.product_id);
            }
            usedPurchasePhotos.add(selected);
            const image = productThumbnail(purchase.product_name, purchase.product_id);
            image.src = `/static/images/catalog/${encodeURIComponent(selected)}`;
            return image;
        }

        purchases.forEach((purchase) => {
            const card = createElement(
                "article",
                null,
                "feature-card rtr-product-card"
            );

            card.appendChild(distinctPurchaseThumbnail(purchase));

            card.appendChild(
                createElement(
                    "h3",
                    displayValue(purchase.product_name)
                )
            );

            // RTR_PRICE_DISPLAY_PATCH_5976: show actual purchased unit price
            card.appendChild(createElement("div", formatPurchasePrice(purchase.unit_price), "rtr-price"));

            addDetail(
                card,
                "Order",
                friendlyOrderNumber(purchase.order_number)
            );

            addDetail(
                card,
                "Purchase Date",
                displayDate(purchase.order_date)
            );

            addDetail(
                card,
                "Quantity",
                purchase.quantity
            );

            if (purchase.can_request_return) {
                card.classList.add("rtr-selectable-purchase");
                card.setAttribute("role", "button");
                card.tabIndex = 0;
                card.setAttribute("aria-label", `Request return for ${purchase.product_name}, ${formatPurchasePrice(purchase.unit_price)}`);
                card.addEventListener("click", () => selectPurchaseForReturn(purchase));
                card.addEventListener("keydown", (event) => {
                    if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        selectPurchaseForReturn(purchase);
                    }
                });
                card.appendChild(createElement("p", "Select to request a return", "rtr-select-hint"));
            } else {
                card.classList.add("rtr-unavailable-purchase");
                card.appendChild(createElement("p", purchase.return_eligibility_reason || "Return unavailable", "rtr-select-hint"));
            }
            grid.appendChild(card);
        });

        purchasesContainer.appendChild(grid);
    }

    async function showReturnHistory(returnId) {
        historyContainer.replaceChildren(
            createElement("p", "Loading return history...")
        );

        try {
            const response = await fetch(
                `/api/customer/returns/${encodeURIComponent(returnId)}/history`,
                { credentials: "same-origin" }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "Unable to load return history."
                );
            }

            historyContainer.replaceChildren();

            const heading = createElement("div", null, "rtr-history-heading");
            heading.appendChild(createElement("h3", `Return #${returnId}`));
            heading.appendChild(createStatusBadge(data.current_status));
            historyContainer.appendChild(heading);
            const matchingReturn = rtrReturns.find(r => String(r.return_id) === String(returnId));
            if (matchingReturn) {
                const matchingProduct = rtrFindPurchase(matchingReturn) || matchingReturn;
                const summary = createElement("div", null, "rtr-history-product");
                summary.appendChild(productThumbnail(matchingProduct.product_name, matchingProduct.product_id));
                summary.appendChild(createElement("strong", matchingProduct.product_name));
                historyContainer.appendChild(summary);
            }

            if (!Array.isArray(data.history) ||
                data.history.length === 0) {
                historyContainer.appendChild(
                    createElement(
                        "p",
                        "No status changes have been recorded."
                    )
                );
                return;
            }

            const list = createElement("ul");

            data.history.forEach((entry) => {
                const item = createElement("li", null, "rtr-history-event");
                const previous = entry.old_status || "Submitted";
                const current = entry.new_status || "Updated";
                const transition = createElement("div", null, "rtr-history-transition");
                transition.appendChild(createStatusBadge(previous));
                transition.appendChild(createElement("span", "→", "rtr-history-arrow"));
                transition.appendChild(createStatusBadge(current));
                item.appendChild(transition);
                if (entry.changed_at) {
                    const parsed = new Date(entry.changed_at);
                    const readable = Number.isNaN(parsed.getTime())
                        ? String(entry.changed_at)
                        : parsed.toLocaleString(undefined, {dateStyle:"medium", timeStyle:"short"});
                    item.appendChild(createElement("p", readable, "rtr-history-date"));
                }
                list.appendChild(item);
            });

            historyContainer.appendChild(list);

        } catch (error) {
            historyContainer.replaceChildren(
                createElement("p", error.message)
            );
        }
    }

    function createStatusBadge(status) {
        const text = displayValue(status);
        const key = text.toLowerCase().replace(/[^a-z]+/g, "-").replace(/^-|-$/g, "");
        return createElement("span", text, `rtr-status rtr-status-${key}`);
    }

    function showReturns(returns) {
        returnsContainer.replaceChildren();

        if (returns.length === 0) {
            returnsContainer.appendChild(
                createElement(
                    "p",
                    "You have not submitted any return requests."
                )
            );
            return;
        }

        const grid = createElement("div", null, "feature-grid");

        returns.forEach((returnRequest) => {
            const card = createElement(
                "article",
                null,
                "feature-card rtr-return-card"
            );

            card.appendChild(productThumbnail(returnRequest.product_name, (rtrFindPurchase(returnRequest) || returnRequest).product_id));

            card.appendChild(
                createElement(
                    "h3",
                    displayValue(returnRequest.product_name)
                )
            );

            addDetail(
                card,
                "Return ID",
                returnRequest.return_id
            );

            card.appendChild(createStatusBadge(returnRequest.status));

            addDetail(
                card,
                "Reason",
                returnRequest.return_reason
            );

            const historyButton = createElement(
                "button",
                "View Status History",
                "button"
            );

            historyButton.type = "button";

            historyButton.addEventListener("click", () => {
                showReturnHistory(returnRequest.return_id);
            });

            card.appendChild(historyButton);
            grid.appendChild(card);
        });

        returnsContainer.appendChild(grid);
    }

    function updateReturnOptions(purchases) {
        eligiblePurchases = new Map();
        returnSelect.replaceChildren(new Option("Select a purchased item", ""));
        purchases.forEach((purchase) => {
            if (!purchase.can_request_return) return;
            const key = String(purchase.order_item_id);
            eligiblePurchases.set(key, purchase);
            returnSelect.add(new Option(
                `${purchase.product_name} — ${formatPurchasePrice(purchase.unit_price)} — Order ${friendlyOrderNumber(purchase.order_number)}`,
                key
            ));
        });
        if (!eligiblePurchases.size) {
            returnMessage.textContent = "No purchased items are currently eligible for a new return.";
        }
    }

    returnForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const purchase = eligiblePurchases.get(returnSelect.value);
        if (!purchase) {
            returnMessage.textContent = "Select an eligible purchased item.";
            return;
        }
        const submitButton = returnForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        returnMessage.textContent = "Submitting return request...";
        try {
            const response = await fetch("/api/customer/returns", {
                method: "POST",
                credentials: "same-origin",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    product_id: purchase.product_id,
                    order_item_id: purchase.order_item_id,
                    purchase_date: purchase.order_date,
                    return_reason: document.getElementById("return-reason").value.trim(),
                    item_condition: document.getElementById("item-condition").value,
                    packaging_condition: document.getElementById("packaging-condition").value,
                    functionality: document.getElementById("functionality").value
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Return submission failed.");
            returnForm.reset();
            await loadDashboard();
            const status = data.return.status || "Submitted";
            returnMessage.textContent = `Return #${data.return.return_id}: ${status}.`;
        } catch (error) {
            returnMessage.textContent = error.message;
        } finally {
            submitButton.disabled = false;
        }
    });

    // RTR_PRICE_DISPLAY_PATCH_5976: display actual prices from /api/customer/dashboard
    function formatPurchasePrice(value) {
        const amount = Number(value);
        return value === null || value === undefined || value === "" || !Number.isFinite(amount)
            ? "Not available"
            : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
    }

    function addPricesToReturnSelector(purchases) {
        const selector = document.getElementById("return-order-item");
        if (!selector) return;
        const byId = new Map(purchases.map(p => [String(p.order_item_id), p]));
        for (const option of selector.options) {
            const purchase = byId.get(option.value);
            if (!purchase) continue;
            const price = formatPurchasePrice(purchase.unit_price);
            if (!option.textContent.includes(price)) option.textContent += ` — ${price}`;
        }
    }


    async function loadDashboard() {
        try {
            const response = await fetch(
                "/api/customer/dashboard",
                { credentials: "same-origin" }
            );

            if (response.status === 401) {
                window.location.href = "/login";
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "Unable to load dashboard."
                );
            }

            welcome.textContent =
                `Welcome, ${data.user.full_name}!`;

            const purchases = Array.isArray(data.purchases)
                ? data.purchases
                : [];

            const returns = Array.isArray(data.returns)
                ? data.returns
                : [];

            purchaseCount.textContent = data.purchase_count;
            returnCount.textContent = data.return_count;

            rtrPurchases = purchases;
            rtrReturns = returns;
            updateReturnOptions(purchases);
            showPurchases(purchases);
            addPricesToReturnSelector(purchases);
            showReturns(returns);

        } catch (error) {
            message.textContent = error.message;
        }
    }

    logoutButton.addEventListener("click", async () => {
        logoutButton.disabled = true;

        try {
            const response = await fetch("/api/logout", {
                method: "POST",
                credentials: "same-origin"
            });

            if (!response.ok) {
                throw new Error("Unable to log out.");
            }

            window.location.href = "/login";

        } catch (error) {
            message.textContent = error.message;
            logoutButton.disabled = false;
        }
    });

    loadDashboard();
});
