(function () {
"use strict";


function createVoiceRecorder(fileInput) {
    if (!fileInput) {
        return;
    }

    // Prevent creating the recorder twice
    if (fileInput.dataset.voiceRecorderReady === "true") {
        return;
    }

    fileInput.dataset.voiceRecorderReady = "true";

    const container = document.createElement("div");

    container.style.marginTop = "10px";
    container.style.padding = "12px";
    container.style.border = "1px solid #ddd";
    container.style.borderRadius = "8px";
    container.style.background = "#fafafa";

    const recordButton = document.createElement("button");

    recordButton.type = "button";
    recordButton.textContent = "🎤 Record Voice";

    recordButton.style.marginRight = "8px";
    recordButton.style.padding = "8px 14px";
    recordButton.style.border = "0";
    recordButton.style.borderRadius = "6px";
    recordButton.style.cursor = "pointer";

    const stopButton = document.createElement("button");

    stopButton.type = "button";
    stopButton.textContent = "⏹ Stop";

    stopButton.disabled = true;

    stopButton.style.marginRight = "8px";
    stopButton.style.padding = "8px 14px";
    stopButton.style.border = "0";
    stopButton.style.borderRadius = "6px";
    stopButton.style.cursor = "pointer";

    const status = document.createElement("span");

    status.textContent = "Voice not recorded";

    status.style.marginLeft = "5px";

    const audio = document.createElement("audio");

    audio.controls = true;
    audio.style.display = "none";
    audio.style.marginTop = "10px";
    audio.style.width = "100%";

    container.appendChild(recordButton);
    container.appendChild(stopButton);
    container.appendChild(status);
    container.appendChild(audio);

    fileInput.parentNode.appendChild(container);

    let mediaRecorder = null;
    let audioChunks = [];
    let mediaStream = null;

    recordButton.addEventListener("click", async function () {

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            status.textContent =
                "Your browser does not support voice recording.";

            return;
        }

        try {

            mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: true
            });

            audioChunks = [];

            mediaRecorder = new MediaRecorder(mediaStream);

            mediaRecorder.addEventListener("dataavailable", function (event) {

                if (event.data && event.data.size > 0) {
                    audioChunks.push(event.data);
                }

            });

            mediaRecorder.addEventListener("stop", function () {

                const audioBlob = new Blob(
                    audioChunks,
                    {
                        type: mediaRecorder.mimeType || "audio/webm"
                    }
                );

                const extension =
                    audioBlob.type.includes("ogg")
                        ? "ogg"
                        : "webm";

                const audioFile = new File(
                    [audioBlob],
                    "support_voice_" + Date.now() + "." + extension,
                    {
                        type: audioBlob.type
                    }
                );

                const dataTransfer = new DataTransfer();

                dataTransfer.items.add(audioFile);

                fileInput.files = dataTransfer.files;

                audio.src = URL.createObjectURL(audioBlob);
                audio.style.display = "block";

                status.textContent = "Voice ready";

                recordButton.disabled = false;
                stopButton.disabled = true;

                if (mediaStream) {

                    mediaStream.getTracks().forEach(function (track) {
                        track.stop();
                    });

                    mediaStream = null;
                }

            });

            mediaRecorder.start();

            recordButton.disabled = true;
            stopButton.disabled = false;

            status.textContent = "Recording...";

        } catch (error) {

            console.error(
                "Voice recording error:",
                error
            );

            status.textContent =
                "Microphone permission was denied or unavailable.";

        }

    });

    stopButton.addEventListener("click", function () {

        if (
            mediaRecorder &&
            mediaRecorder.state !== "inactive"
        ) {

            mediaRecorder.stop();

        }

    });
}


function initializeVoiceRecorders() {

    const inputs = document.querySelectorAll(
        'input[type="file"][name$="-voice_message"]'
    );

    inputs.forEach(function (input) {

        createVoiceRecorder(input);

    });
}


document.addEventListener(
    "DOMContentLoaded",
    initializeVoiceRecorders
);


/*
 * =========================================================
 * LIVE CUSTOMER MESSAGES
 * =========================================================
 */

function connectCustomerWebSocket() {

    const pathParts = window.location.pathname.split("/");

    const ticketIndex = pathParts.indexOf("supportticket");

    if (ticketIndex === -1) {
        return;
    }

    const ticketId = pathParts[ticketIndex + 1];

    if (!ticketId || !/^\d+$/.test(ticketId)) {
        return;
    }

    const protocol =
        window.location.protocol === "https:"
            ? "wss:"
            : "ws:";

    const socketUrl =
        protocol +
        "//" +
        window.location.host +
        "/ws/human-support/" +
        ticketId +
        "/";

    const socket = new WebSocket(socketUrl);

    socket.onopen = function () {

        console.log(
            "Admin live chat connected for ticket #" + ticketId
        );

    };

    socket.onmessage = function (event) {

        try {

            const data = JSON.parse(event.data);

            console.log(
                "Admin received WebSocket event:",
                data
            );

            if (data.type !== "customer_message") {
                return;
            }

            addCustomerMessageToAdmin(data);

        } catch (error) {

            console.error(
                "Error reading live customer message:",
                error
            );

        }

    };

    socket.onclose = function () {

        console.log(
            "Admin live chat disconnected."
        );

    };

    socket.onerror = function (error) {

        console.error(
            "Admin WebSocket error:",
            error
        );

    };
}


function addCustomerMessageToAdmin(data) {

    const message = data.message || "";

    /*
     * Find the Customer Ticket Messages inline
     */
    const inlineGroup =
        document.querySelector(
            ".inline-group"
        );

    if (!inlineGroup) {

        console.warn(
            "Customer message inline section not found."
        );

        return;
    }


    /*
     * Create a new visual message box.
     */
    const messageBox =
        document.createElement("div");

    messageBox.style.marginTop = "15px";
    messageBox.style.padding = "12px";
    messageBox.style.border = "1px solid #ddd";
    messageBox.style.borderRadius = "8px";
    messageBox.style.background = "#f9f9f9";


    /*
     * Customer label
     */
    const sender =
        document.createElement("strong");

    sender.textContent = "Customer";

    messageBox.appendChild(sender);


    /*
     * Message text
     */
    if (message) {

        const text =
            document.createElement("div");

        text.textContent = message;

        text.style.marginTop = "6px";

        messageBox.appendChild(text);

    }

    /*
 * Attachment
 */
if (data.attachment_url) {

    const attachment = document.createElement("div");

    attachment.style.marginTop = "10px";

    const link = document.createElement("a");

    link.href = data.attachment_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "📎 View attachment";

    attachment.appendChild(link);

    messageBox.appendChild(attachment);
}

    
    /*
 * Voice message
 */
if (data.voice_url) {

    const voiceContainer =
        document.createElement("div");

    voiceContainer.style.marginTop = "10px";

    const audio =
        document.createElement("audio");

    audio.controls = true;
    audio.preload = "metadata";
    audio.style.maxWidth = "100%";

    const source =
        document.createElement("source");

    source.src = data.voice_url;

    audio.appendChild(source);

    voiceContainer.appendChild(audio);

    messageBox.appendChild(voiceContainer);
}

    /*
     * Time
     */
    if (data.created_at) {

        const time =
            document.createElement("small");

        time.textContent =
            data.created_at;

        time.style.display = "block";
        time.style.marginTop = "6px";
        time.style.color = "#777";

        messageBox.appendChild(time);

    }


    inlineGroup.appendChild(messageBox);


    /*
     * Scroll the new message into view.
     */
    messageBox.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });

}


/*
 * Start the Admin WebSocket.
 */
document.addEventListener(
    "DOMContentLoaded",
    connectCustomerWebSocket
);


})();
